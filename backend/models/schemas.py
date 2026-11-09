from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class Source(BaseModel):
    source: str
    publisher: str
    url: str
    publication_date: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    language: Optional[str] = "en"  # "en" | "hi" | "or" — Phase 6 will auto-detect
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    language: str
    intent: str
    is_emergency: bool
    risk_level: Optional[str] = None
    sources: List[Source] = []
    disclaimer: str
    provider_used: Optional[str] = None


class RiskAssessmentRequest(BaseModel):
    age_group: str
    symptoms: List[str]
    duration_days: Optional[float] = None
    temperature_celsius: Optional[float] = None
    existing_conditions: List[str] = []
    pregnant: bool = False


class RiskAssessmentResponse(BaseModel):
    risk_level: str
    factors_considered: List[str]
    recommendation: str
    disclaimer: str


class MisinformationCheckRequest(BaseModel):
    claim: str = Field(..., min_length=3, max_length=1000)


class MisinformationCheckResponse(BaseModel):
    claim: str
    verdict: str  # supported | misleading | unsupported | false | insufficient_evidence
    explanation: str
    sources: List[Source] = []
