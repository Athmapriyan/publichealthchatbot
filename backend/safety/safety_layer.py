"""
Safety layer sitting between the user and the LLM.

Responsibilities:
1. Emergency detection — runs BEFORE normal flow; if triggered, short-circuits
   straight to an urgent, non-buried warning (never nested inside a long reply).
2. Prompt constraints — the system prompt the LLM must follow (no diagnosis,
   no prescriptions, no dosages, cite evidence, express uncertainty).
3. Response validation — a lightweight post-hoc check for red-flag phrases
   that must never appear in output (e.g. specific drug dosages, "you have X").
4. Standard disclaimer appended to every informational response.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

DISCLAIMER = (
    "This information is for general public-health awareness only and is not a medical "
    "diagnosis. Please consult a qualified healthcare professional for advice specific to you."
)

# Emergency keyword/phrase patterns (English). Expand per-language in Phase 6.
# Intentionally pattern-level, not exhaustive clinical triage logic.
EMERGENCY_PATTERNS = [
    r"\bcan'?t breathe\b", r"\bdifficulty breathing\b", r"\bshortness of breath\b",
    r"\bchest pain\b", r"\bchest pressure\b",
    r"\bunconscious\b", r"\bnot responding\b", r"\bpassed out\b", r"\bfainted and (not|won'?t) wak",
    r"\bsevere bleeding\b", r"\bbleeding (a lot|heavily|won'?t stop)\b",
    r"\bseizure\b", r"\bconvulsion\b", r"\bfitting\b",
    r"\bstroke\b", r"\bface (is )?droop", r"\bslurred speech\b", r"\bsudden weakness on one side\b",
    r"\bsevere allergic reaction\b", r"\banaphylaxis\b", r"\bthroat (is )?swelling\b",
    r"\bsuicid", r"\bkill myself\b", r"\bwant to die\b", r"\bself.?harm\b",
    r"\bpoison(ed|ing)?\b", r"\boverdose\b",
    r"\bsevere injury\b", r"\bheavy accident\b", r"\bsnake ?bite\b",
    r"\bheart attack\b",
    r"\bbaby (not moving|not breathing)\b", r"\bchild (not breathing|unresponsive)\b",
]
_EMERGENCY_RE = re.compile("|".join(EMERGENCY_PATTERNS), re.IGNORECASE)

# Phrases that should never appear in a generated response (post-hoc guard).
FORBIDDEN_OUTPUT_PATTERNS = [
    r"\byou have (dengue|malaria|tuberculosis|tb|diabetes|typhoid|cholera|covid|cancer)\b",
    r"\byou (are|'re) diagnosed with\b",
    r"\btake \d+\s?(mg|ml|mcg|tablets?|pills?)\b",
    r"\bi (am|'m) (a|your) doctor\b",
    r"\bdefinitely (is|are|have)\b.*\b(dengue|malaria|tb|cancer)\b",
]
_FORBIDDEN_RE = re.compile("|".join(FORBIDDEN_OUTPUT_PATTERNS), re.IGNORECASE)

EMERGENCY_MESSAGE_EN = (
    "⚠️ This may be a medical emergency.\n\n"
    "Please seek immediate in-person medical help now:\n"
    "- Call your local emergency ambulance number immediately.\n"
    "- In India, you can call 112 (national emergency number) or 108 (ambulance, in most states).\n"
    "- Go to the nearest hospital emergency department right away.\n\n"
    "Do not wait for an online chat response to decide on emergency symptoms. "
    "This chatbot cannot provide emergency medical care."
)

SAFE_SYSTEM_PROMPT = """You are a public-health information assistant for citizens of Odisha, India.
You operate under strict safety rules:
1. You NEVER diagnose a disease. Never say "you have X" — only describe what is generally associated with symptoms.
2. You NEVER prescribe medication, dosages, or specific drug names/amounts.
3. You ALWAYS recommend consulting a qualified healthcare professional for personal medical decisions.
4. You ONLY use the provided reference context to answer medical factual questions. If the context does not
   contain enough relevant information, say so clearly and do not invent facts.
5. You explain things in simple, plain language suitable for people with limited health literacy.
6. You cite which source the information came from when you use the reference context.
7. You never claim certainty you do not have. Use language like "commonly", "may", "in general".
8. Keep responses concise and focused — this is a chat interface, not a textbook.
"""


@dataclass
class SafetyCheckResult:
    is_emergency: bool
    emergency_message: str | None = None
    matched_patterns: List[str] = field(default_factory=list)


def check_emergency(user_text: str) -> SafetyCheckResult:
    match = _EMERGENCY_RE.search(user_text)
    if match:
        return SafetyCheckResult(is_emergency=True, emergency_message=EMERGENCY_MESSAGE_EN, matched_patterns=[match.group(0)])
    return SafetyCheckResult(is_emergency=False)


def validate_response(response_text: str) -> tuple[bool, str | None]:
    """Returns (is_safe, reason_if_unsafe). Caller should replace unsafe responses
    with a safe fallback rather than showing them to the user."""
    match = _FORBIDDEN_RE.search(response_text)
    if match:
        return False, f"Response contained a disallowed pattern: '{match.group(0)}'"
    return True, None

SAFE_FALLBACK_RESPONSE = (
    "I want to make sure I give you safe, accurate information, and I'm not confident enough in my "
    "answer to share it directly. Please consult a qualified healthcare professional, or ask your "
    "question again in a different way and I'll try to help with general public-health information."
)

INSUFFICIENT_EVIDENCE_RESPONSE = (
    "I don't have enough reliable information in my verified knowledge base to answer that safely. "
    "Please consult a qualified healthcare professional, or contact your nearest government health "
    "facility for accurate guidance."
)
