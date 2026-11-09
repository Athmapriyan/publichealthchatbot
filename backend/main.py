"""
Public Health Chatbot — FastAPI backend entrypoint.
Run: uvicorn backend.main:app --reload --port 8000
"""
import logging
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models.schemas import (
    ChatRequest, ChatResponse,
    RiskAssessmentRequest, RiskAssessmentResponse,
    MisinformationCheckRequest, MisinformationCheckResponse,
)
from backend.services.chat_service import handle_chat
from backend.risk.risk_model import assess, RiskInput
from backend.misinformation.checker import check_claim

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("main")

app = FastAPI(
    title="Odisha Public Health Chatbot API",
    description="AI-driven public health awareness, risk screening, and misinformation checking.",
    version="0.1.0-mvp",
)

# NOTE: tighten allow_origins to the deployed frontend domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "public-health-chatbot", "env": settings.APP_ENV}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.language not in settings.SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Supported: {settings.SUPPORTED_LANGUAGES}")
    try:
        return handle_chat(req.message, req.language)
    except Exception as e:
        logger.exception("Unhandled error in /chat")
        raise HTTPException(status_code=500, detail="Internal error processing chat request.") from e


@app.post("/risk-assessment", response_model=RiskAssessmentResponse)
def risk_assessment(req: RiskAssessmentRequest):
    result = assess(RiskInput(
        age_group=req.age_group,
        symptoms=req.symptoms,
        duration_days=req.duration_days,
        temperature_celsius=req.temperature_celsius,
        existing_conditions=req.existing_conditions,
        pregnant=req.pregnant,
    ))
    return RiskAssessmentResponse(
        risk_level=result.risk_level.value,
        factors_considered=result.factors_considered,
        recommendation=result.recommendation,
        disclaimer=result.disclaimer,
    )


@app.post("/misinformation-check", response_model=MisinformationCheckResponse)
def misinformation_check(req: MisinformationCheckRequest):
    result = check_claim(req.claim)
    return MisinformationCheckResponse(**result)


@app.get("/diseases")
def list_diseases():
    path = Path(settings.KNOWLEDGE_BASE_PATH)
    if not path.exists():
        return {"diseases": []}
    docs = json.loads(path.read_text(encoding="utf-8"))
    diseases = sorted({d["disease"] for d in docs})
    return {"diseases": diseases, "count": len(diseases)}


@app.get("/health-resources")
def health_resources():
    # Placeholder — Phase-later integration point for verified Govt of Odisha APIs.
    # Deliberately NOT fabricating hospital names/numbers per spec section 15.
    return {
        "message": "Location-specific government health resources are not yet connected to a live data source.",
        "official_links": [
            {"name": "Ministry of Health & Family Welfare, India", "url": "https://mohfw.gov.in/"},
            {"name": "National Health Mission Odisha", "url": "https://nhm.odisha.gov.in/"},
            {"name": "Odisha State Health & Family Welfare Department", "url": "https://health.odisha.gov.in/"},
        ],
    }


@app.get("/sources")
def sources():
    path = Path(settings.KNOWLEDGE_BASE_PATH)
    docs = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    seen = {}
    for d in docs:
        seen[d["source"]] = d.get("url", "")
    return {"trusted_sources": [{"name": k, "url": v} for k, v in seen.items()]}
