"""
Thin client around Sarvam AI's text APIs.

Sarvam AI (https://docs.sarvam.ai) is an India-focused provider with strong
Indic-language support (22 scheduled languages + English), which is why it's
used here instead of a generic translation API.

Endpoints used:
  POST /translate   — text translation (model: sarvam-translate:v1)
  POST /text-lid     — language identification

Auth: header `api-subscription-key: <SARVAM_API_KEY>` (NOT a Bearer token —
Sarvam uses its own header scheme, different from the OpenAI-style providers
in llm_provider.py).
"""
from __future__ import annotations
import logging
import httpx

from backend.config import settings

logger = logging.getLogger("multilingual.sarvam")

BASE_URL = "https://api.sarvam.ai"

# App-level language codes (what the rest of the app and the frontend use)
# mapped to Sarvam's BCP-47-style codes.
APP_TO_SARVAM_LANG = {
    "en": "en-IN",      # English
    "hi": "hi-IN",      # Hindi
    "bn": "bn-IN",      # Bengali
    "te": "te-IN",      # Telugu
    "mr": "mr-IN",      # Marathi
    "ta": "ta-IN",      # Tamil
    "gu": "gu-IN",      # Gujarati
    "ur": "ur-IN",      # Urdu
    "kn": "kn-IN",      # Kannada
    "or": "od-IN",      # Odia
    "ml": "ml-IN",      # Malayalam
    "pa": "pa-IN",      # Punjabi
    "as": "as-IN",      # Assamese
    "mai": "mai-IN",    # Maithili
    "sat": "sat-IN",    # Santali
    "ks": "ks-IN",      # Kashmiri
    "ne": "ne-IN",      # Nepali
    "sd": "sd-IN",      # Sindhi
    "doi": "doi-IN",    # Dogri
    "kok": "kok-IN",    # Konkani
    "mni": "mni-IN",    # Manipuri (Meitei)
    "brx": "brx-IN",    # Bodo
    "sa": "sa-IN",      # Sanskrit
}
SARVAM_TO_APP_LANG = {v: k for k, v in APP_TO_SARVAM_LANG.items()}


class SarvamError(Exception):
    """Raised on any Sarvam API failure (timeout / auth / rate-limit / 5xx)."""


def _headers() -> dict:
    if not settings.SARVAM_API_KEY:
        raise SarvamError("SARVAM_API_KEY is not configured")
    return {
        "Content-Type": "application/json",
        "api-subscription-key": settings.SARVAM_API_KEY,
    }


def is_configured() -> bool:
    return bool(settings.SARVAM_API_KEY)


def translate(text: str, source_lang: str, target_lang: str) -> str:
    """source_lang / target_lang are app-level codes: 'en' | 'hi' | 'or'.
    Returns the translated text. Raises SarvamError on failure.
    """
    if source_lang == target_lang:
        return text
    if not text.strip():
        return text

    source_code = APP_TO_SARVAM_LANG.get(source_lang, "en-IN")
    target_code = APP_TO_SARVAM_LANG.get(target_lang, "en-IN")

    # Sarvam Translate limits input to 2000 chars per request — chunk defensively.
    if len(text) > 1900:
        text = text[:1900]

    try:
        resp = httpx.post(
            f"{BASE_URL}/translate",
            headers=_headers(),
            json={
                "input": text,
                "source_language_code": source_code,
                "target_language_code": target_code,
                "model": settings.SARVAM_TRANSLATE_MODEL,
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("translated_text", text)
    except httpx.TimeoutException as e:
        raise SarvamError(f"Sarvam translate timeout: {e}") from e
    except httpx.HTTPStatusError as e:
        raise SarvamError(f"Sarvam translate HTTP {e.response.status_code}: {e}") from e
    except httpx.RequestError as e:
        raise SarvamError(f"Sarvam translate network error: {e}") from e


def detect_language(text: str) -> str:
    """Returns an app-level language code ('en' | 'hi' | 'or' | ...).
    Falls back to 'en' if detection fails or returns something unmapped.
    """
    if not text.strip():
        return "en"
    try:
        resp = httpx.post(
            f"{BASE_URL}/text-lid",
            headers=_headers(),
            json={"input": text},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        sarvam_code = data.get("language_code", "en-IN")
        return SARVAM_TO_APP_LANG.get(sarvam_code, "en")
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
        logger.warning("Sarvam language detection failed, defaulting to 'en': %s", e)
        return "en"
