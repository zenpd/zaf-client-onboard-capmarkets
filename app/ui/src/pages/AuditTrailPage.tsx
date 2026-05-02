import { ScrollText, Shield, Lock, Clock, Info } from 'lucide-react'

const RULES = [
  { code: 'FR-AU1', text: 'All state transitions recorded with timestamp, actor identity, and data hash' },
  { code: 'FR-AU2', text: 'Every manual override logged with reviewer identity and rationale' },
  { code: 'FR-AU3', text: 'Immutable log — no edit or delete operations permitted' },
  { code: 'FR-AU4', text: '7-year minimum retention in encrypted storage conforming to COBS 9A' },
]

export default function AuditTrailPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <ScrollText size={20} className="text-zen-600" />
            Audit Trail
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">BRD FR-AU1 — Immutable append-only event log, 7-year retention</p>
        </div>
      </div>

      {/* Rules */}
      <div className="grid grid-cols-2 gap-4">
        {RULES.map(r => (
          <div key={r.code} className="card p-4 border-l-4 border-l-zen-400 flex items-start gap-3">
            <div className="w-8 h-8 rounded-xl bg-zen-50 flex items-center justify-center flex-shrink-0">
              <Shield size={14} className="text-zen-600" />
            </div>
            <div>
              <p className="text-xs font-bold text-zen-700">{r.code}</p>
              <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{r.text}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-gray-50 border border-gray-200 flex items-center justify-center">
            <Clock size={16} className="text-gray-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-700">Session-level audit trail</p>
            <p className="text-xs text-gray-400">Audit events are recorded per-session on the backend</p>
          </div>
        </div>
        <div className="bg-gray-50 border border-gray-200 border-dashed rounded-2xl py-10 flex flex-col items-center gap-3">
          <Lock size={32} className="text-gray-300" />
          <p className="text-sm text-gray-400">Navigate to an <span className="text-zen-600 font-medium">Application Detail</span> page to view the session audit log.</p>
          <p className="text-xs text-gray-400">All events are stored with cryptographic hash and actor identity.</p>
        </div>
      </div>

      {/* Storage info */}
      <div className="card p-4 bg-gradient-to-r from-gray-50 to-white flex items-start gap-3">
        <Info size={14} className="text-gray-400 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-gray-500 leading-relaxed">
          Audit logs are stored in an append-only event store per BRD FR-AU3. This UI renders a read-only view.
          Administrative access to the full audit log requires direct database access with appropriate RBAC permissions.
        </p>
      </div>
    </div>
  )
}
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FileText className="text-navy-500" />
          Audit Trail
        </h1>
        <p className="text-sm text-gray-500 mt-1">BRD FR-AU1 — Immutable append-only event log, 7-year retention</p>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex gap-3 text-sm text-blue-800">
        <Info size={18} className="flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">BRD Audit Requirements</p>
          <ul className="mt-1 space-y-0.5 text-xs list-disc ml-4">
            <li>FR-AU1: All state transitions recorded with timestamp, actor, data hash</li>
            <li>FR-AU2: Every manual override logged with reviewer identity</li>
            <li>FR-AU3: Immutable — no edit or delete operations permitted</li>
            <li>7-year minimum retention in encrypted storage</li>
          </ul>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
        <p className="text-sm text-gray-400 text-center py-10">
          Audit events are stored per-session. Navigate to an Application Detail page to see the session audit trail.
        </p>
      </div>
    </div>
  )
}
