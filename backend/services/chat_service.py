"""
Orchestrates the pipeline required by spec section 34:

User -> Language Detection/Translation -> Emergency Safety Screening -> Intent
     -> RAG Retrieval -> LLM -> Response Validation -> Translation -> Response

This is intentionally NOT `User -> LLM -> Answer`.
"""
from __future__ import annotations
import logging

from backend.models.schemas import ChatResponse, Source
from backend.safety.safety_layer import (
    check_emergency, SAFE_SYSTEM_PROMPT, validate_response,
    DISCLAIMER, SAFE_FALLBACK_RESPONSE, INSUFFICIENT_EVIDENCE_RESPONSE,
)
from backend.services.intent_classifier import classify, Intent
from backend.services.llm_provider import llm_router, LLMProviderError
from backend.rag.retriever import get_retriever
from backend.multilingual.language_service import prepare_query, translate_response

logger = logging.getLogger("chat_service")


def handle_chat(message: str, language: str = "en") -> ChatResponse:
    # 0. LANGUAGE HANDLING — translate the incoming query to English up front.
    # Emergency detection, intent classification, RAG and the LLM all operate
    # in English; the final response is translated back at the end. This
    # avoids silently mistranslating medical facts in the knowledge base
    # itself (see backend/multilingual/language_service.py for rationale).
    ctx = prepare_query(message, language)
    english_query = ctx.query_in_english

    # 1. SAFETY SCREENING FIRST — never buried inside a longer response.
    # Runs on the ENGLISH query so emergency keyword patterns (currently
    # English-only) still catch non-English input correctly.
    safety_check = check_emergency(english_query)
    if safety_check.is_emergency:
        emergency_text = translate_response(safety_check.emergency_message, ctx.original_language)
        return ChatResponse(
            response=emergency_text,
            language=ctx.original_language,
            intent=Intent.EMERGENCY.value,
            is_emergency=True,
            sources=[],
            disclaimer=translate_response(DISCLAIMER, ctx.original_language),
        )

    # 2. INTENT DETECTION
    intent = classify(english_query)

    # 3. KNOWLEDGE RETRIEVAL (RAG) — ground the answer, don't rely on LLM memory alone
    retriever = get_retriever()
    chunks = retriever.retrieve(english_query)

    if not chunks:
        # 8. Refuse gracefully rather than hallucinate (spec section 20)
        refusal_text = translate_response(INSUFFICIENT_EVIDENCE_RESPONSE, ctx.original_language)
        return ChatResponse(
            response=refusal_text,
            language=ctx.original_language,
            intent=intent.value,
            is_emergency=False,
            sources=[],
            disclaimer=translate_response(DISCLAIMER, ctx.original_language),
        )

    context_text = "\n\n".join(
        f"[Source: {c['metadata']['source']}] {c['content']}" for c in chunks
    )
    user_prompt = (
        f"Reference context (trusted public-health sources):\n{context_text}\n\n"
        f"Citizen's question: {english_query}\n\n"
        "Answer using ONLY the reference context above. Keep it simple, concise, and safe. "
        "Mention which source(s) you used."
    )

    # 4. LLM GENERATION (provider-abstracted, with fallback chain) — always in English
    try:
        llm_result = llm_router.generate(SAFE_SYSTEM_PROMPT, user_prompt, max_tokens=1000)
        response_text_en = llm_result.text.strip()
        provider_used = llm_result.provider
    except LLMProviderError as e:
        logger.error("All LLM providers failed: %s", e)
        fallback_en = (
            "I'm temporarily unable to reach my language model providers. "
            "Please try again shortly, or consult a qualified healthcare professional / "
            "your nearest government health facility in the meantime."
        )
        return ChatResponse(
            response=translate_response(fallback_en, ctx.original_language),
            language=ctx.original_language,
            intent=intent.value,
            is_emergency=False,
            sources=[],
            disclaimer=translate_response(DISCLAIMER, ctx.original_language),
        )

    # 5. RESPONSE VALIDATION — post-hoc safety guard (checked in English, before translation)
    is_safe, reason = validate_response(response_text_en)
    if not is_safe:
        logger.warning("Unsafe response blocked: %s", reason)
        response_text_en = SAFE_FALLBACK_RESPONSE
        provider_used = None

    # 6. TRANSLATE RESPONSE BACK to the user's requested language (no-op if already English)
    response_text = translate_response(response_text_en, ctx.original_language)

    sources = [
        Source(
            source=c["metadata"]["source"],
            publisher=c["metadata"]["publisher"],
            url=c["metadata"]["url"],
            publication_date=c["metadata"]["publication_date"],
        )
        for c in chunks
    ]

    return ChatResponse(
        response=response_text,
        language=ctx.original_language,
        intent=intent.value,
        is_emergency=False,
        sources=sources,
        disclaimer=translate_response(DISCLAIMER, ctx.original_language),
        provider_used=provider_used,
    )
