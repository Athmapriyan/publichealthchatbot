"""
Multilingual orchestration used by chat_service.py.

Design per spec section 7:
  User Language -> Language Detection -> Query Translation -> Retrieval/LLM
  (in English) -> Translation back to User's Language

Important: the knowledge base (knowledge_base/diseases.json) and LLM prompts
are English-only for now (Phase 3 content). So for hi/or input, we translate
the QUERY to English for retrieval+generation, then translate the RESPONSE
back — we do NOT translate medical source documents on the fly, to avoid
silently mistranslating clinical facts. This matches spec section 7's warning
against "blindly translating medical terminology."

If Sarvam is unavailable (no key / API down), the service degrades gracefully:
non-English requests get an explanatory note instead of a hard failure.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

from backend.multilingual import sarvam_client
from backend.multilingual.sarvam_client import SarvamError

logger = logging.getLogger("multilingual.language_service")

UNAVAILABLE_NOTICE = {
    "hi": "(अनुवाद सेवा अभी उपलब्ध नहीं है — अंग्रेज़ी में उत्तर नीचे दिया गया है)",
    "or": "(ଅନୁବାଦ ସେବା ବର୍ତ୍ତମାନ ଉପଲବ୍ଧ ନାହିଁ — ଇଂରାଜୀରେ ଉତ୍ତର ନିମ୍ନରେ ଦିଆଯାଇଛି)",
}


@dataclass
class TranslationContext:
    original_language: str       # what the user asked in (or selected)
    query_in_english: str        # query translated to English for RAG/LLM
    translation_available: bool  # whether Sarvam successfully handled this request


def prepare_query(message: str, requested_language: str) -> TranslationContext:
    """Detects/confirms language and translates the query to English if needed."""
    if requested_language == "en" or not sarvam_client.is_configured():
        return TranslationContext(
            original_language="en" if requested_language == "en" else requested_language,
            query_in_english=message,
            translation_available=requested_language == "en",  # true only if no translation was needed
        )

    try:
        english_query = sarvam_client.translate(message, source_lang=requested_language, target_lang="en")
        return TranslationContext(
            original_language=requested_language,
            query_in_english=english_query,
            translation_available=True,
        )
    except SarvamError as e:
        logger.warning("Query translation failed (%s), falling back to English passthrough: %s", requested_language, e)
        return TranslationContext(
            original_language=requested_language,
            query_in_english=message,  # best-effort passthrough
            translation_available=False,
        )


def translate_response(english_text: str, target_language: str) -> str:
    """Translates the final English response back to the user's language.
    Returns the English text (with a notice prefix) if translation isn't available.
    """
    if target_language == "en" or not sarvam_client.is_configured():
        return english_text

    try:
        return sarvam_client.translate(english_text, source_lang="en", target_lang=target_language)
    except SarvamError as e:
        logger.warning("Response translation failed (%s), returning English with notice: %s", target_language, e)
        notice = UNAVAILABLE_NOTICE.get(target_language, "")
        return f"{notice}\n\n{english_text}" if notice else english_text
