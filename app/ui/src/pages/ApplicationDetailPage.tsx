import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { clientApi } from '../services/clientApi'
import { Loader2 } from 'lucide-react'
import Badge from '../components/ui/Badge'

const LANE_COLORS: Record<string, 'green' | 'blue' | 'yellow' | 'red' | 'purple' | 'gray'> = {
  stp: 'green', standard: 'blue', enhanced: 'yellow', edd: 'purple', hold: 'red', reject: 'red',
}

export default function ApplicationDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) return
    clientApi.getSession(sessionId)
      .then((r) => setData(r.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading) return <div className="flex h-full items-center justify-center"><Loader2 className="animate-spin text-navy-500" size={32} /></div>
  if (!data) return <div className="p-8 text-red-600">Session not found: {sessionId}</div>

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Application Detail</h1>
        <Badge
          label={String(data.routing_lane || 'pending')}
          color={LANE_COLORS[String(data.routing_lane)] || 'gray'}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {([
          ['Session ID',    String(data.session_id ?? '—')],
          ['Journey Type',  String(data.journey_type ?? '—')],
          ['Client Type',   String(data.client_type ?? '—')],
          ['Current Step',  String(data.current_step ?? '—')],
          ['Risk Band',     (data.risk_score as Record<string,string>)?.risk_band || '—'],
          ['Account No.',   String(data.account_number ?? '—')],
        ] as [string, string][]).map(([label, value]) => (
          <div key={label} className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
            <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">{label}</p>
            <p className="text-base font-semibold text-gray-900 mt-1 capitalize">{value}</p>
          </div>
        ))}
      </div>

      {/* Completed Steps */}
      {Array.isArray(data.completed_steps) && data.completed_steps.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <h2 className="font-semibold text-gray-800 mb-3">Completed Steps</h2>
          <div className="flex flex-wrap gap-2">
            {(data.completed_steps as string[]).map((s) => (
              <span key={s} className="text-xs bg-green-100 text-green-700 rounded-full px-3 py-1 font-medium capitalize">{s.replace(/_/g, ' ')}</span>
            ))}
          </div>
        </div>
      )}

      {/* AI Review Outputs */}
      {data.llm_case_summary != null && (
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <h2 className="font-semibold text-gray-800 mb-3">AI Case Summary</h2>
          <p className="text-sm text-gray-700 leading-relaxed">{String(data.llm_case_summary)}</p>
        </div>
      )}

      {/* Audit Trail */}
      {Array.isArray(data.audit_trail) && data.audit_trail.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <h2 className="font-semibold text-gray-800 mb-3">Audit Trail</h2>
          <div className="space-y-2">
            {(data.audit_trail as Record<string,string>[]).map((e, i) => (
              <div key={i} className="text-xs p-2 bg-slate-50 rounded border border-slate-200">
                <span className="font-semibold text-navy-500">{e.event}</span>
                <span className="ml-2 text-gray-500">{e.timestamp}</span>
                {e.decision && <span className="ml-2 text-gray-700">· {e.decision}</span>}
                {e.actor && <span className="ml-2 text-gray-400">by {e.actor}</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
