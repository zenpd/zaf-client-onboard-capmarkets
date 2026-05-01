"""FastAPI application entry point — Capital Markets Wealth Management Onboarding Platform."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.config import get_settings
from shared.logger import setup_logging, get_logger
from observability.tracing import init_tracing
from api.routers import health, onboard, documents, review, applications

log = get_logger("api.main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    init_tracing()
    try:
        from db.base import create_all_tables
        await create_all_tables()
        log.info("db.tables_ready", env=settings.app_env)
    except Exception as exc:
        log.warning("db.table_creation_failed", error=str(exc))
    log.info("api.startup", env=settings.app_env, version="1.0.0",
             service="capmarkets-client-onboarding")
    yield
    log.info("api.shutdown")


app = FastAPI(
    title="Capital Markets Wealth Management Client Onboarding API",
    description=(
        "AI-augmented intelligent automation platform for wealth management middle- and "
        "back-office operations. Powered by LangGraph + 14 specialist agents. "
        "BRD-compliant: 25-step client onboarding (UC-01), deterministic rules engine, "
        "LLM-assisted case analysis, human-in-the-loop compliance workflow."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(health.router,                                         tags=["Health"])
app.include_router(onboard.router,       prefix="/api/v1/onboard",       tags=["Client Onboarding"])
app.include_router(documents.router,     prefix="/api/v1/documents",     tags=["Documents"])
app.include_router(review.router,        prefix="/api/v1/review",        tags=["Compliance Review"])
app.include_router(applications.router,  prefix="/api/v1/applications",  tags=["Applications"])
