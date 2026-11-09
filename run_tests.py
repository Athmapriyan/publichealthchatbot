#!/usr/bin/env python
"""
Run offline unit tests for the public health chatbot.
Tests: emergency detection, intent classification, response validation, risk assessment.
"""
import sys
sys.path.insert(0, '.')

from backend.safety.safety_layer import check_emergency, validate_response
from backend.services.intent_classifier import classify, Intent
from backend.risk.risk_model import assess, RiskInput, RiskLevel

def test_emergency_detection():
    print("=== Testing Emergency Detection ===")
    
    result = check_emergency("I have severe chest pain and can't breathe")
    assert result.is_emergency is True, "Chest pain should be detected as emergency"
    print("[PASS] Emergency chest pain detected")

    result = check_emergency("What are the symptoms of dengue?")
    assert result.is_emergency is False, "Normal query should not trigger emergency"
    print("[PASS] Normal query not falsely triggered")

    result = check_emergency("My child is unconscious and not responding")
    assert result.is_emergency is True, "Unconscious child should be detected as emergency"
    print("[PASS] Unconscious child detected")

def test_intent_classification():
    print("\n=== Testing Intent Classification ===")
    
    intent = classify("How can I prevent malaria?")
    assert intent == Intent.PREVENTION, f"Expected PREVENTION, got {intent}"
    print(f"[PASS] Prevention intent: {intent}")

    intent = classify("Is this true? I heard drinking papaya juice cures dengue")
    assert intent == Intent.MISINFORMATION, f"Expected MISINFORMATION, got {intent}"
    print(f"[PASS] Misinformation intent: {intent}")

def test_response_validation():
    print("\n=== Testing Response Validation ===")
    
    is_safe, reason = validate_response("Based on your symptoms, you have dengue.")
    assert is_safe is False, "Diagnosis claim should be blocked"
    print(f"[PASS] Diagnosis claim blocked: {reason}")

    is_safe, reason = validate_response("Dengue commonly causes high fever and joint pain. Please consult a doctor for diagnosis.")
    assert is_safe is True, "Safe response should be allowed"
    print("[PASS] Safe response allowed")

def test_risk_assessment():
    print("\n=== Testing Risk Assessment ===")
    
    result = assess(RiskInput(age_group="adult", symptoms=["difficulty breathing"]))
    assert result.risk_level == RiskLevel.HIGH, f"Expected HIGH, got {result.risk_level}"
    print(f"[PASS] High risk for breathing difficulty")

    result = assess(RiskInput(age_group="adult", symptoms=["fatigue"], duration_days=1))
    assert result.risk_level == RiskLevel.LOW, f"Expected LOW, got {result.risk_level}"
    print(f"[PASS] Low risk for mild symptom")

    result = assess(RiskInput(age_group="infant", symptoms=["high fever"], temperature_celsius=39.8))
    assert result.risk_level == RiskLevel.HIGH, f"Expected HIGH, got {result.risk_level}"
    print(f"[PASS] Elevated risk for infant with fever")

if __name__ == "__main__":
    try:
        test_emergency_detection()
        test_intent_classification()
        test_response_validation()
        test_risk_assessment()
        print("\n[SUCCESS] All offline tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
