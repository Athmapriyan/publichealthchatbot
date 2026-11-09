"""
Early health risk assessment module.

Phase-1 implementation: a transparent, explainable RULE-BASED scorer (not an
opaque ML black box) so the project can demonstrate explainability immediately.
Section 10 of the spec (Logistic Regression / RandomForest / XGBoost) belongs
here as a drop-in replacement — see `train_ml_model.py` placeholder below for
where that plugs in. The interface (`assess()`) stays the same either way, so
swapping rule-based -> ML does not require changing any caller.

This module explicitly does NOT diagnose. It classifies urgency of care-seeking.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


# Symptoms that, combined with other factors, push risk up sharply.
HIGH_RISK_SYMPTOMS = {
    "difficulty breathing", "chest pain", "severe bleeding", "seizure",
    "confusion", "unconsciousness", "blood in vomit", "blood in stool",
    "severe dehydration", "stiff neck", "persistent vomiting",
}
MODERATE_RISK_SYMPTOMS = {
    "high fever", "persistent cough", "abdominal pain", "rash",
    "severe headache", "joint pain", "vomiting", "diarrhea", "fatigue",
}
VULNERABLE_AGE_GROUPS = {"infant", "child_under_5", "elderly_65_plus"}


@dataclass
class RiskInput:
    age_group: str  # e.g. "infant", "child_under_5", "child", "adult", "elderly_65_plus"
    symptoms: List[str]
    duration_days: Optional[float] = None
    temperature_celsius: Optional[float] = None
    existing_conditions: List[str] = field(default_factory=list)
    pregnant: bool = False


@dataclass
class RiskResult:
    risk_level: RiskLevel
    factors_considered: List[str]
    recommendation: str
    disclaimer: str = (
        "This is general risk guidance based on the information you provided, "
        "not a medical diagnosis. A healthcare professional should evaluate your specific situation."
    )


def assess(data: RiskInput) -> RiskResult:
    factors: List[str] = []
    score = 0

    symptoms_lower = {s.strip().lower() for s in data.symptoms}

    high_hits = symptoms_lower & HIGH_RISK_SYMPTOMS
    if high_hits:
        score += 3
        factors.append(f"High-risk symptom(s) reported: {', '.join(sorted(high_hits))}")

    moderate_hits = symptoms_lower & MODERATE_RISK_SYMPTOMS
    if moderate_hits:
        score += 1
        factors.append(f"Moderate-risk symptom(s) reported: {', '.join(sorted(moderate_hits))}")

    if data.temperature_celsius is not None:
        if data.temperature_celsius >= 39.5:
            score += 2
            factors.append(f"High fever reported ({data.temperature_celsius}°C)")
        elif data.temperature_celsius >= 38.0:
            score += 1
            factors.append(f"Fever reported ({data.temperature_celsius}°C)")

    if data.duration_days is not None and data.duration_days >= 3:
        score += 1
        factors.append(f"Symptoms persisting for {data.duration_days} days")

    if data.age_group in VULNERABLE_AGE_GROUPS:
        score += 1
        factors.append(f"Age group increases vulnerability: {data.age_group}")

    if data.pregnant:
        score += 1
        factors.append("Pregnancy increases risk and warrants closer monitoring")

    if data.existing_conditions:
        score += 1
        factors.append(f"Existing condition(s) reported: {', '.join(data.existing_conditions)}")

    if not factors:
        factors.append("No significant risk factors identified from the information provided")

    if score >= 4 or high_hits:
        level = RiskLevel.HIGH
        recommendation = (
            "Seek medical attention promptly. Based on what you've described, a healthcare "
            "professional should evaluate this soon — consider visiting a hospital or clinic today."
        )
    elif score >= 2:
        level = RiskLevel.MODERATE
        recommendation = (
            "It would be a good idea to consult a healthcare professional, especially if symptoms "
            "worsen or do not improve in the next day or two."
        )
    else:
        level = RiskLevel.LOW
        recommendation = (
            "Your reported symptoms don't indicate an urgent concern, but monitor how you feel and "
            "consult a healthcare professional if symptoms develop or persist."
        )

    return RiskResult(risk_level=level, factors_considered=factors, recommendation=recommendation)


# ---------------------------------------------------------------------------
# Phase 4 extension point: replace `assess()`'s scoring with a trained model.
# Planned interface (not yet implemented — needs a labeled symptom dataset):
#
#   from joblib import load
#   _model = load("data/models/risk_classifier.joblib")
#   def assess_ml(data: RiskInput) -> RiskResult:
#       features = featurize(data)             # see scripts/train_risk_model.py
#       proba = _model.predict_proba([features])[0]
#       level = RiskLevel(_model.classes_[proba.argmax()])
#       ... build factors_considered from feature importances (SHAP) for explainability
#
# Keep recall/sensitivity for HIGH risk as the primary metric to optimize,
# per spec section 10 — a missed high-risk case is far costlier than a
# false alarm in a public-health screening tool.
# ---------------------------------------------------------------------------
