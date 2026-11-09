"""
Intent classification — Phase-1 keyword baseline per spec section 23/24.
Swap for a trained transformer/sklearn classifier later without changing the
`classify()` interface (see scripts/train_intent_classifier.py placeholder).
"""
from __future__ import annotations
from enum import Enum
import re


class Intent(str, Enum):
    DISEASE_AWARENESS = "disease_awareness"
    SYMPTOMS = "symptoms"
    PREVENTION = "prevention"
    TREATMENT_INFO = "treatment_information"
    EMERGENCY = "emergency"
    MEDICATION = "medication"
    VACCINATION = "vaccination"
    MISINFORMATION = "misinformation"
    GOVERNMENT_HEALTH_SERVICE = "government_health_services"
    RISK_ASSESSMENT = "risk_assessment"
    GENERAL_HEALTH = "general_health"


_RULES = [
    (Intent.MISINFORMATION, re.compile(r"\b(is (it|this) true|true or false|fake|hoax|whatsapp (forward|message)|rumou?r|myth)\b", re.I)),
    (Intent.VACCINATION, re.compile(r"\b(vaccin|immuniz|immunis)\w*\b", re.I)),
    (Intent.GOVERNMENT_HEALTH_SERVICE, re.compile(r"\b(nearest (hospital|clinic|phc|chc)|government hospital|health (camp|scheme)|where can i get tested|vaccination center)\b", re.I)),
    (Intent.MEDICATION, re.compile(r"\b(medicine|dosage|dose|tablet|drug|prescri\w*)\b", re.I)),
    (Intent.PREVENTION, re.compile(r"\b(prevent|avoid getting|how (do|can) i avoid|precaution)\b", re.I)),
    (Intent.SYMPTOMS, re.compile(r"\b(symptom|sign of|warning sign|how (do i|to) know if)\b", re.I)),
    (Intent.TREATMENT_INFO, re.compile(r"\b(treat\w*|cure|remedy|how is .* (treated|managed))\b", re.I)),
    (Intent.RISK_ASSESSMENT, re.compile(r"\b(should i (worry|see a doctor|go to (the )?hospital)|is this serious|my (child|son|daughter|father|mother) has)\b", re.I)),
]


def classify(text: str) -> Intent:
    for intent, pattern in _RULES:
        if pattern.search(text):
            return intent
    # Fall back: if it names a known disease, treat as awareness; else general
    if re.search(r"\b(dengue|malaria|tuberculosis|tb|diabetes|hypertension|influenza|flu|covid|cholera|typhoid|hepatitis)\b", text, re.I):
        return Intent.DISEASE_AWARENESS
    return Intent.GENERAL_HEALTH
