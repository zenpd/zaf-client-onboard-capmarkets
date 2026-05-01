import { FileText, Info } from 'lucide-react'

export default function AuditTrailPage() {
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
