"""LangGraph Supervisor graph — Wealth Management Client Onboarding.

BRD 25-Step Process across 10 phases, 6 domains.
Supervisor-loop architecture with per-turn step limiting.
"""
from __future__ import annotations
from langgraph.graph import StateGraph, END

from agents.state import OnboardingState
from agents.nodes.supervisor import supervisor_node, next_agent
from agents.nodes.triage import triage_node
from agents.nodes.client_education import client_education_node
from agents.nodes.document_collection import document_collection_node
from agents.nodes.ocr_data_extraction import ocr_data_extraction_node
from agents.nodes.data_validation import data_validation_node
from agents.nodes.entity_resolution import entity_resolution_node
from agents.nodes.kyb_ubo import kyb_ubo_node
from agents.nodes.sanctions_pep_screening import sanctions_pep_screening_node
from agents.nodes.fatca_crs import fatca_crs_node
from agents.nodes.source_of_wealth import source_of_wealth_node
from agents.nodes.corporate_risk_scoring import corporate_risk_scoring_node
from agents.nodes.risk_scoring import risk_scoring_node
from agents.nodes.context_pack_builder import context_pack_builder_node
from agents.nodes.ai_review import ai_review_node
from agents.nodes.auto_decision import auto_decision_node
from agents.nodes.account_creation import account_creation_node
from agents.nodes.alerts_notifications import alerts_notifications_node
from agents.guardrails import guardrails_node
from agents.human_in_loop import human_review_node


def _completion_node(state: OnboardingState) -> OnboardingState:
    state["current_step"] = "completed"
    state["step_status"] = "completed"
    return state


def _error_node(state: OnboardingState) -> OnboardingState:
    state["step_status"] = "failed"
    return state


def _respond_and_wait_node(state: OnboardingState) -> OnboardingState:
    return state


def _awaiting_review_node(state: OnboardingState) -> OnboardingState:
    state["current_step"] = "human_review"
    state["step_status"] = "escalated"
    msgs = state.get("messages", [])
    if msgs and msgs[-1].get("role") == "user":
        state.setdefault("messages", []).append({
            "role": "assistant",
            "agent": "awaiting_review",
            "content": (
                "⏳ **Application still under compliance review.**\n\n"
                "Our team is assessing your case. You will be notified by email once a decision is made."
            ),
        })
    return state


def build_graph() -> StateGraph:
    g = StateGraph(OnboardingState)

    # ── Register all nodes ────────────────────────────────────────────────────
    g.add_node("supervisor",               supervisor_node)
    g.add_node("guardrails",               guardrails_node)
    g.add_node("triage",                   triage_node)
    g.add_node("client_education",         client_education_node)
    g.add_node("document_collection",      document_collection_node)
    g.add_node("ocr_data_extraction",      ocr_data_extraction_node)
    g.add_node("data_validation",          data_validation_node)
    g.add_node("entity_resolution",        entity_resolution_node)
    g.add_node("kyb_ubo",                  kyb_ubo_node)
    g.add_node("sanctions_pep_screening",  sanctions_pep_screening_node)
    g.add_node("fatca_crs",               fatca_crs_node)
    g.add_node("source_of_wealth",         source_of_wealth_node)
    g.add_node("corporate_risk_scoring",   corporate_risk_scoring_node)
    g.add_node("risk_scoring",             risk_scoring_node)
    g.add_node("context_pack_builder",     context_pack_builder_node)
    g.add_node("ai_review",                ai_review_node)
    g.add_node("auto_decision",            auto_decision_node)
    g.add_node("human_review",             human_review_node)
    g.add_node("account_creation",         account_creation_node)
    g.add_node("alerts_notifications",     alerts_notifications_node)
    g.add_node("awaiting_review",          _awaiting_review_node)
    g.add_node("respond_and_wait",         _respond_and_wait_node)
    g.add_node("onboarding_complete",      _completion_node)
    g.add_node("error_handler",            _error_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    g.set_entry_point("guardrails")
    g.add_edge("guardrails", "supervisor")

    # ── Supervisor conditional routing ────────────────────────────────────────
    g.add_conditional_edges(
        "supervisor",
        next_agent,
        {
            "triage":                  "triage",
            "client_education":        "client_education",
            "document_collection":     "document_collection",
            "ocr_data_extraction":     "ocr_data_extraction",
            "data_validation":         "data_validation",
            "entity_resolution":       "entity_resolution",
            "kyb_ubo":                 "kyb_ubo",
            "sanctions_pep_screening": "sanctions_pep_screening",
            "fatca_crs":               "fatca_crs",
            "source_of_wealth":        "source_of_wealth",
            "corporate_risk_scoring":  "corporate_risk_scoring",
            "risk_scoring":            "risk_scoring",
            "context_pack_builder":    "context_pack_builder",
            "ai_review":               "ai_review",
            "auto_decision":           "auto_decision",
            "human_review":            "human_review",
            "account_creation":        "account_creation",
            "alerts_notifications":    "alerts_notifications",
            "awaiting_review":         "awaiting_review",
            "respond_and_wait":        "respond_and_wait",
            "onboarding_complete":     "onboarding_complete",
            "error_handler":           "error_handler",
        },
    )

    # ── All domain nodes loop back to supervisor ──────────────────────────────
    for node in [
        "triage", "client_education", "document_collection", "ocr_data_extraction",
        "data_validation", "entity_resolution", "kyb_ubo", "sanctions_pep_screening",
        "fatca_crs", "source_of_wealth", "corporate_risk_scoring", "risk_scoring",
        "context_pack_builder", "ai_review", "auto_decision",
        "account_creation", "alerts_notifications",
    ]:
        g.add_edge(node, "supervisor")

    # ── Human review / terminal nodes ─────────────────────────────────────────
    g.add_edge("human_review", "supervisor")
    g.add_edge("awaiting_review", END)
    g.add_edge("respond_and_wait", END)
    g.add_edge("onboarding_complete", END)
    g.add_edge("error_handler", END)

    return g


# Compile once at module load
compiled_graph = build_graph().compile()
