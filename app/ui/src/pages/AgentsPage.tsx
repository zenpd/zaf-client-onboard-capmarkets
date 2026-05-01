import { Bot } from 'lucide-react'
import Badge from '../components/ui/Badge'

const AGENTS = [
  { name: 'supervisor',              role: 'Orchestrates all agent nodes; routes to next step based on journey map' },
  { name: 'triage',                  role: 'Classifies client type (retail/HNW/UHNW/corporate), scores complexity, sets routing lane' },
  { name: 'client_education',        role: 'Explains onboarding process, required documents, and regulatory obligations' },
  { name: 'document_collection',     role: 'Determines required documents per client type and journey, tracks completion' },
  { name: 'ocr_data_extraction',     role: 'OCR extraction with 85% confidence threshold (BRD FR-D2)' },
  { name: 'data_validation',         role: 'Validates completeness and consistency of extracted data' },
  { name: 'entity_resolution',       role: 'Resolves entity against Client Master and deduplicates records' },
  { name: 'kyb_ubo',                 role: 'Corporate only — UBO identification, beneficial ownership thresholds (>25%)' },
  { name: 'sanctions_pep_screening', role: 'Deterministic OFAC/UN/EU/HMT sanctions check + PEP/adverse media. LLM cannot clear sanctions (FR-R2/FR-A4)' },
  { name: 'fatca_crs',               role: 'FATCA/CRS determination; missing TIN sets withholding flag, blocks progression (FR-R5)' },
  { name: 'source_of_wealth',        role: 'Verifies declared source of wealth with supporting docs + LLM assessment' },
  { name: 'corporate_risk_scoring',  role: 'Corporate-specific risk: industry, multi-jurisdiction, regulated entity flags' },
  { name: 'risk_scoring',            role: 'Deterministic composite risk score (FR-R3). LLM cannot modify scores' },
  { name: 'context_pack_builder',    role: 'Builds versioned immutable Context Pack (FR-D4); PII tokenised before LLM delivery (FR-D5)' },
  { name: 'ai_review',               role: 'Generates all 8 LLM output types (FR-A1). Validates prohibited phrases (FR-A4)' },
  { name: 'auto_decision',           role: 'STP all-or-nothing evaluation (FR-R4). Routes to account_creation or human_review' },
  { name: 'human_review',            role: 'Queues case for compliance officer with Context Pack, awaits decision signal' },
  { name: 'account_creation',        role: 'Posts to Client Master, Core Banking, WM Platform. Creates account number' },
  { name: 'alerts_notifications',    role: 'Dispatches welcome, MLRO, compliance, and CRM notifications (FR-AU3)' },
  { name: 'guardrails',              role: 'Input guardrails: prompt injection detection, PII filtering, turn limits' },
]

export default function AgentsPage() {
  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Bot className="text-navy-500" />
          AI Agents Registry
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          {AGENTS.length} specialist agents — LangGraph supervisor-loop architecture
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {AGENTS.map((a) => (
          <div key={a.name} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-start gap-4">
            <div className="w-9 h-9 rounded-lg bg-navy-500 flex items-center justify-center flex-shrink-0">
              <Bot size={18} className="text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <code className="text-sm font-semibold text-navy-700">{a.name}</code>
                <Badge label="active" color="green" />
              </div>
              <p className="text-xs text-gray-600 mt-0.5">{a.role}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
