"""
Medical misinformation checker.

Per spec section 11: avoid simply asking the LLM "is this true?". Instead:
  claim -> retrieve relevant trusted evidence -> LLM reasons ONLY over that
  evidence and must output a structured verdict -> cite sources.

Note: this RAG-based verifier is the Phase-5 MVP implementation. Section 12's
comparison (TF-IDF+LogReg baseline vs transformer classifier vs this RAG
approach) requires a labeled misinformation dataset to train/evaluate the
first two — see scripts/train_misinformation_classifier.py placeholder.
This module currently implements only the RAG-based verification arm.
"""
from __future__ import annotations
import json
import re
import logging

from backend.models.schemas import Source
from backend.safety.safety_layer import INSUFFICIENT_EVIDENCE_RESPONSE
from backend.services.llm_provider import llm_router, LLMProviderError
from backend.rag.retriever import get_retriever

logger = logging.getLogger("misinformation.checker")

VERDICTS = {"supported", "misleading", "unsupported", "false", "insufficient_evidence"}

MISINFO_SYSTEM_PROMPT = """You are a medical fact-checking assistant. You will be given a health-related
claim and trusted reference evidence. Your job is to classify the claim strictly based on the evidence
provided — not your own general knowledge — into exactly one of these verdicts:
- "supported": the evidence directly confirms the claim.
- "misleading": the claim contains some truth but is presented in a way that could cause harm or wrong conclusions.
- "unsupported": the evidence does not confirm the claim, but also doesn't clearly refute it.
- "false": the evidence directly contradicts the claim.
- "insufficient_evidence": the provided evidence does not cover this claim at all.

Respond ONLY in strict JSON with this shape, no markdown fences, no extra text:
{"verdict": "<one of the above>", "explanation": "<2-3 simple sentences explaining why, referencing the evidence>"}
"""


def check_claim(claim: str) -> dict:
    retriever = get_retriever()
    chunks = retriever.retrieve(claim, top_k=4)

    if not chunks:
        return {
            "claim": claim,
            "verdict": "insufficient_evidence",
            "explanation": INSUFFICIENT_EVIDENCE_RESPONSE,
            "sources": [],
        }

    evidence_text = "\n\n".join(
        f"[Source: {c['metadata']['source']}] {c['content']}" for c in chunks
    )
    user_prompt = f"Claim: \"{claim}\"\n\nTrusted evidence:\n{evidence_text}\n\nClassify this claim."

    sources = [
        Source(
            source=c["metadata"]["source"],
            publisher=c["metadata"]["publisher"],
            url=c["metadata"]["url"],
            publication_date=c["metadata"]["publication_date"],
        )
        for c in chunks
    ]

    try:
        result = llm_router.generate(MISINFO_SYSTEM_PROMPT, user_prompt, temperature=0.1)
    except LLMProviderError as e:
        logger.error("Misinformation check failed, all providers down: %s", e)
        return {
            "claim": claim,
            "verdict": "insufficient_evidence",
            "explanation": "Unable to verify this claim right now due to a temporary service issue. Please try again shortly.",
            "sources": [s.model_dump() for s in sources],
        }

    raw = result.text.strip()
    # Strip accidental markdown fences
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(raw)
        verdict = parsed.get("verdict", "insufficient_evidence")
        if verdict not in VERDICTS:
            verdict = "insufficient_evidence"
        explanation = parsed.get("explanation", "")
    except json.JSONDecodeError:
        logger.warning("Could not parse misinformation verdict JSON: %s", raw)
        verdict = "insufficient_evidence"
        explanation = "Unable to confidently evaluate this claim against trusted sources."

    return {
        "claim": claim,
        "verdict": verdict,
        "explanation": explanation,
        "sources": [s.model_dump() for s in sources],
    }
