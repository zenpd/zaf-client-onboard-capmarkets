"""Applications listing / dashboard stats endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from api.auth import get_current_user
from shared.logger import get_logger
import random

log = get_logger(__name__)
router = APIRouter()


@router.get("/stats")
async def dashboard_stats(user: dict = Depends(get_current_user)):
    return {
        "total_applications": random.randint(120, 200),
        "active_today":        random.randint(5, 25),
        "completed_today":     random.randint(3, 15),
        "pending_review":      random.randint(2, 12),
        "stp_rate":            round(random.uniform(0.55, 0.70), 3),
        "avg_completion_days": round(random.uniform(2.0, 6.0), 1),
        "edd_cases_open":      random.randint(1, 5),
        "sanctions_holds":     random.randint(0, 2),
        "routing_breakdown": {
            "stp":      random.randint(50, 80),
            "standard": random.randint(20, 40),
            "enhanced": random.randint(5, 15),
            "edd":      random.randint(1, 8),
            "hold":     random.randint(0, 3),
        },
    }


@router.get("/")
async def list_applications(user: dict = Depends(get_current_user)):
    return {"applications": [], "total": 0}
