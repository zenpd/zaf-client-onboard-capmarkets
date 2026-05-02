import { Bot, Zap, CheckCircle2 } from 'lucide-react'

const AGENTS = [
  { name: 'supervisor',              role: 'Orchestrates all agent nodes; routes to next step based on journey map', category: 'Core' },
  { name: 'triage',                  role: 'Classifies client type (retail/HNW/UHNW/corporate), scores complexity, sets routing lane', category: 'Core' },
  { name: 'client_education',        role: 'Explains onboarding process, required documents, and regulatory obligations', category: 'Onboarding' },
  { name: 'document_collection',     role: 'Determines required documents per client type and journey, tracks completion', category: 'Onboarding' },
  { name: 'ocr_data_extraction',     role: 'OCR extraction with 85% confidence threshold (BRD FR-D2)', category: 'Onboarding' },
  { name: 'data_validation',         role: 'Validates completeness and consistency of extracted data', category: 'Onboarding' },
  { name: 'entity_resolution',       role: 'Resolves entity against Client Master and deduplicates records', category: 'Onboarding' },
  { name: 'kyb_ubo',                 role: 'Corporate only — UBO identification, beneficial ownership thresholds (>25%)', category: 'KYC/AML' },
  { name: 'sanctions_pep_screening', role: 'Deterministic OFAC/UN/EU/HMT sanctions check + PEP/adverse media. LLM cannot clear sanctions (FR-R2/FR-A4)', category: 'KYC/AML' },
  { name: 'fatca_crs',               role: 'FATCA/CRS determination; missing TIN sets withholding flag, blocks progression (FR-R5)', category: 'KYC/AML' },
  { name: 'source_of_wealth',        role: 'Verifies declared source of wealth with supporting docs + LLM assessment', category: 'KYC/AML' },
  { name: 'corporate_risk_scoring',  role: 'Corporate-specific risk: industry, multi-jurisdiction, regulated entity flags', category: 'Risk' },
  { name: 'risk_scoring',            role: 'Deterministic composite risk score (FR-R3). LLM cannot modify scores', category: 'Risk' },
  { name: 'context_pack_builder',    role: 'Builds versioned immutable Context Pack (FR-D4); PII tokenised before LLM delivery (FR-D5)', category: 'AI' },
  { name: 'ai_review',               role: 'Generates all 8 LLM output types (FR-A1). Validates prohibited phrases (FR-A4)', category: 'AI' },
  { name: 'auto_decision',           role: 'STP all-or-nothing evaluation (FR-R4). Routes to account_creation or human_review', category: 'Decision' },
  { name: 'human_review',            role: 'Queues case for compliance officer with Context Pack, awaits decision signal', category: 'Decision' },
  { name: 'account_creation',        role: 'Posts to Client Master, Core Banking, WM Platform. Creates account number', category: 'Ops' },
  { name: 'alerts_notifications',    role: 'Dispatches welcome, MLRO, compliance, and CRM notifications (FR-AU3)', category: 'Ops' },
  { name: 'guardrails',              role: 'Input guardrails: prompt injection detection, PII filtering, turn limits', category: 'Security' },
]

const CATEGORY_COLORS: Record<string, string> = {
  Core:      'bg-zen-100 text-zen-700',
  Onboarding:'bg-blue-100 text-blue-700',
  'KYC/AML': 'bg-rose-100 text-rose-700',
  Risk:      'bg-amber-100 text-amber-700',
  AI:        'bg-purple-100 text-purple-700',
  Decision:  'bg-orange-100 text-orange-700',
  Ops:       'bg-emerald-100 text-emerald-700',
  Security:  'bg-gray-200 text-gray-700',
}

