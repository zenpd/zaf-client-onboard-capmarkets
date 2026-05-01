# Capital Markets Wealth Management Client Onboarding Platform

> AI-augmented intelligent automation for wealth management middle- and back-office operations.  
> Built on **LangGraph + Temporal + FastAPI + React**, fully spec'd against the internal BRD (UC-01).

---

## Architecture

```
┌───────────────────────────────────────────────────────┐
│                React 18 + Vite + Tailwind UI          │
│       Dashboard · Onboard · Compliance · Audit        │
└──────────────────────────┬────────────────────────────┘
                           │ REST /api/v1
┌──────────────────────────▼────────────────────────────┐
│              FastAPI  (api/main.py)                    │
│  /onboard  /documents  /review  /applications         │
└──────────────────────────┬────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────┐
│        LangGraph — Supervisor-Loop (agents/graph.py)   │
│  19 specialist agents  ·  4 terminal nodes             │
│  Journey maps: individual | joint | corporate | trust  │
└──────────────────────────┬────────────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     ▼                     ▼                     ▼
  Redis (sessions)    SQLite/Postgres       Temporal (durable)
```

---

## BRD Compliance Matrix (UC-01)

| Ref     | Requirement                                       | Implementation                              |
|---------|---------------------------------------------------|---------------------------------------------|
| FR-D2   | OCR confidence ≥ 85% threshold                    | `ocr_data_extraction` node + FR-D2 check    |
| FR-D4   | Versioned immutable Context Pack                  | `context_pack_builder` node                 |
| FR-D5   | PII tokenisation before LLM delivery              | `_tokenise_pii()` in context_pack_builder   |
| FR-R2   | Sanctions hit → auto hold; LLM cannot clear       | Deterministic check before LLM in screening |
| FR-R3   | Deterministic risk scoring; no LLM                | `shared/scoring.py` — pure Python           |
| FR-R4   | STP all-or-nothing evaluation                     | `auto_decision` node                        |
| FR-R5   | Missing FATCA/CRS blocks progression              | `fatca_crs` node                            |
| FR-A1   | 8 LLM output types per review                     | `ai_review` node — single structured call  |
| FR-A3   | LLM output schema + PII boundary validation       | `_validate_llm_output()` in ai_review       |
| FR-A4   | Prohibited LLM phrases (sanctions, PEP, SAR)      | `_PROHIBITED_PHRASES` regex list            |
| FR-A5   | Raw LLM response logged verbatim                  | structlog in ai_review                      |
| FR-H1–4 | Human-in-the-loop: 4 decisions + rationale + audit| `human_in_loop.py` + compliance UI          |
| FR-AU1–3| Immutable append-only audit trail, 7-year retention| `AuditEvent` DB model + audit_trail state  |

---

## Journey Types

| Journey    | Client Types               | Key Extra Steps              |
|------------|---------------------------|------------------------------|
| individual | retail, hnw, uhnw          | Standard 16-step flow         |
| joint      | retail, hnw, uhnw          | Joint holder verification     |
| corporate  | corporate_simple, complex  | KYB + UBO + corporate risk    |
| trust      | trust                      | Trust deed, beneficiary check |

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Desktop (for full stack)
- Azure OpenAI credentials

### Local Development

```bash
# 1. Clone and enter the project
cd client_onboard_capmarkets

# 2. Create .env from template
make env

# 3. Edit app/.env with your Azure OpenAI credentials

# 4. Install Python deps
make install

# 5. Initialise the database
make db-init

# 6. Start backend (hot reload)
make dev
# → http://localhost:8001/docs

# 7. In another terminal, start frontend
make install-ui
make dev-ui
# → http://localhost:5174
```

### Docker Compose (Full Stack)

```bash
# Copy and populate .env
cp app/.env.example app/.env

# Start infrastructure (DB, Redis, Temporal)
make up-core

# Build and start everything
make up

# Tail logs
make logs
```

**Service URLs:**
- Frontend UI:   http://localhost:3001
- Backend API:   http://localhost:8001/docs
- Temporal UI:   http://localhost:8080

---

## API Reference

| Method | Path                            | Description                          |
|--------|---------------------------------|--------------------------------------|
| POST   | `/api/v1/onboard/start`         | Start new client onboarding session  |
| POST   | `/api/v1/onboard/resume`        | Resume session with user input       |
| GET    | `/api/v1/onboard/session/{id}`  | Get full session state               |
| POST   | `/api/v1/documents/upload`      | Upload document (multipart)          |
| GET    | `/api/v1/documents/session/{id}`| List documents for session           |
| POST   | `/api/v1/review/decide`         | Submit compliance decision           |
| GET    | `/api/v1/review/queue`          | Get compliance review queue          |
| GET    | `/api/v1/applications/stats`    | Dashboard KPI stats                  |
| GET    | `/health`                       | Health check                         |

---

## Project Structure

```
client_onboard_capmarkets/
├── app/
│   ├── api/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── auth.py              # JWT + dev bypass
│   │   ├── dependencies.py      # Redis factory
│   │   └── routers/
│   │       ├── onboard.py       # Core onboarding endpoints
│   │       ├── documents.py     # Document upload + OCR
│   │       ├── review.py        # Compliance review
│   │       └── applications.py  # Dashboard stats
│   ├── agents/
│   │   ├── graph.py             # LangGraph StateGraph
│   │   ├── state.py             # TypedDict schema
│   │   ├── guardrails.py        # Input guardrails
│   │   ├── human_in_loop.py     # Human review node
│   │   ├── nodes/               # 18 specialist agent nodes
│   │   └── tools/               # OCR, sanctions check
│   ├── db/
│   │   ├── base.py              # Async engine + session
│   │   └── models.py            # ClientApplication, DocumentRecord, AuditEvent
│   ├── shared/
│   │   ├── config.py            # Pydantic settings
│   │   ├── llm.py               # Azure OpenAI factory
│   │   ├── scoring.py           # Deterministic risk scoring (FR-R3)
│   │   └── risk_constants.py    # Risk thresholds & constants
│   ├── workflows/
│   │   ├── activities.py        # Temporal activities
│   │   └── client_onboarding_workflow.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── app/ui/                      # React 18 + Vite frontend
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/               # Dashboard, Onboard, Compliance, Audit, Agents, Settings
│   │   ├── components/          # AppShell, StatsCard, Badge
│   │   ├── store/               # Zustand clientStore
│   │   └── services/            # axios API clients
│   └── Dockerfile
├── docker-compose.yml
└── Makefile
```

---

## Development Notes

- **Dev mode**: Set `APP_ENV=development` — enables JWT bypass (any token accepted), SQLite DB, mock LLM fallback
- **Azure OpenAI**: Ensure deployment name matches `AZURE_OPENAI_DEPLOYMENT` in .env
- **Temporal workers**: Not auto-started — run separately with `temporal server start-dev` for local development
- **Sanctions API**: Stub implementation in `agents/tools/sanctions_check.py` — wire to real vendor API in production
