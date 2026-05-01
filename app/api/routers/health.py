"""Health check router."""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "capmarkets-client-onboarding",
    }


@router.get("/")
async def root():
    return {"message": "Capital Markets Client Onboarding API v1.0", "status": "running"}
