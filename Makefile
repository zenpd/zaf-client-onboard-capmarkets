.PHONY: help dev dev-ui install install-ui build up down logs clean test

APP_DIR := app
UI_DIR  := app/ui

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Install ────────────────────────────────────────────────────────────────────
install: ## Install Python dependencies
	cd $(APP_DIR) && pip install -r requirements.txt

install-ui: ## Install frontend npm dependencies
	cd $(UI_DIR) && npm install

# ── Development ────────────────────────────────────────────────────────────────
dev: ## Start FastAPI backend in dev mode (hot reload)
	cd $(APP_DIR) && uvicorn api.main:app --reload --host 0.0.0.0 --port 8001

dev-ui: ## Start Vite frontend dev server
	cd $(UI_DIR) && npm run dev

# ── Docker ─────────────────────────────────────────────────────────────────────
build: ## Build Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

up-core: ## Start infra only (DB, Redis, Temporal)
	docker compose up -d db redis temporal temporal-ui

down: ## Stop all services
	docker compose down

logs: ## Tail logs (all services)
	docker compose logs -f

logs-api: ## Tail backend logs
	docker compose logs -f backend

# ── Database ───────────────────────────────────────────────────────────────────
db-init: ## Create DB tables (SQLite dev)
	cd $(APP_DIR) && python -c "import asyncio; from db.base import create_all_tables; asyncio.run(create_all_tables())"

# ── Tests ──────────────────────────────────────────────────────────────────────
test: ## Run backend tests
	cd $(APP_DIR) && python -m pytest tests/ -v

# ── Util ───────────────────────────────────────────────────────────────────────
clean: ## Remove generated artefacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete

env: ## Copy .env.example to .env
	cp $(APP_DIR)/.env.example $(APP_DIR)/.env && echo "Created app/.env — fill in your credentials."
