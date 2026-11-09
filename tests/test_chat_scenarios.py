"""
Test cases per spec section 33.G. Run with: pytest tests/ -v

NOTE: Tests that call handle_chat() end-to-end require a configured LLM
provider (.env with at least one API key) and will download the embedding
model on first run. Tests marked [offline] test logic that needs no network.
"""
import pytest
from backend.safety.safety_layer import check_emergency, validate_response
from backend.services.intent_classifier import classify, Intent
from backend.risk.risk_model import assess, RiskInput, RiskLevel


# ---------- [offline] Emergency detection ----------
def test_emergency_chest_pain_detected():
    result = check_emergency("I have severe chest pain and can't breathe")
    assert result.is_emergency is True


def test_emergency_not_falsely_triggered_on_normal_query():
    result = check_emergency("What are the symptoms of dengue?")
    assert result.is_emergency is False


def test_emergency_unconscious_child():
    result = check_emergency("My child is unconscious and not responding")
    assert result.is_emergency is True


# ---------- [offline] Intent classification ----------
def test_intent_disease_awareness():
    assert classify("What are the symptoms of dengue?") in (Intent.SYMPTOMS, Intent.DISEASE_AWARENESS)


def test_intent_prevention():
    assert classify("How can I prevent malaria?") == Intent.PREVENTION


def test_intent_misinformation():
    assert classify("Is this health message I received on WhatsApp true?") == Intent.MISINFORMATION


def test_intent_vaccination():
    assert classify("Where can I get vaccinated for COVID?") == Intent.VACCINATION


# ---------- [offline] Response validation (hallucination/unsafe guard) ----------
def test_validate_response_blocks_diagnosis_claim():
    is_safe, reason = validate_response("Based on your symptoms, you have dengue.")
    assert is_safe is False


def test_validate_response_blocks_dosage():
    is_safe, reason = validate_response("Take 500 mg of the tablet twice a day.")
    assert is_safe is False


def test_validate_response_allows_safe_text():
    is_safe, reason = validate_response(
        "Dengue commonly causes high fever and joint pain. Please consult a doctor for diagnosis."
    )
    assert is_safe is True


# ---------- [offline] Risk assessment ----------
def test_risk_high_for_breathing_difficulty():
    result = assess(RiskInput(age_group="adult", symptoms=["difficulty breathing"]))
    assert result.risk_level == RiskLevel.HIGH


def test_risk_low_for_mild_single_symptom():
    result = assess(RiskInput(age_group="adult", symptoms=["fatigue"], duration_days=1))
    assert result.risk_level == RiskLevel.LOW


def test_risk_moderate_for_persistent_fever():
    result = assess(RiskInput(age_group="adult", symptoms=["high fever"], duration_days=3, temperature_celsius=38.5))
    assert result.risk_level in (RiskLevel.MODERATE, RiskLevel.HIGH)


def test_risk_elevated_for_infant_with_fever():
    result = assess(RiskInput(age_group="infant", symptoms=["high fever"], temperature_celsius=39.8))
    assert result.risk_level == RiskLevel.HIGH


# ---------- [online] End-to-end chat — requires .env with a working API key ----------
@pytest.mark.skip(reason="Requires live LLM provider API key; run manually after configuring .env")
def test_chat_normal_health_query():
    from backend.services.chat_service import handle_chat
    resp = handle_chat("What are the symptoms of dengue?")
    assert resp.is_emergency is False
    assert len(resp.sources) > 0


@pytest.mark.skip(reason="Requires live LLM provider API key; run manually after configuring .env")
def test_chat_unsupported_question_refuses_gracefully():
    from backend.services.chat_service import handle_chat
    resp = handle_chat("What is the GDP of Odisha in 1990?")
    assert "don't have enough reliable information" in resp.response or len(resp.sources) == 0


@pytest.mark.skip(reason="Requires live LLM provider + SARVAM_API_KEY; run manually after configuring .env")
def test_chat_multilingual_hindi_query():
    """Spec section G: multilingual query test case."""
    from backend.services.chat_service import handle_chat
    resp = handle_chat("डेंगू के लक्षण क्या हैं?", language="hi")
    assert resp.language == "hi"
    assert resp.is_emergency is False
    assert len(resp.response) > 0


@pytest.mark.skip(reason="Requires live LLM provider API key; run manually after configuring .env")
def test_chat_api_failure_fallback_message():
    """Simulates all providers failing by temporarily clearing provider list."""
    from backend.services.llm_provider import llm_router
    original = llm_router.providers
    llm_router.providers = []
    try:
        from backend.services.chat_service import handle_chat
        resp = handle_chat("What are the symptoms of malaria?")
        assert "temporarily unable" in resp.response.lower()
    finally:
        llm_router.providers = original
