import { useState } from 'react'
import { clientApi, ReviewDecision } from '../services/clientApi'
import { ShieldCheck, Loader2, Check, X, AlertCircle, TrendingUp } from 'lucide-react'

export default function CompliancePage() {
  const [sessionId, setSessionId] = useState('')
  const [decision, setDecision] = useState<ReviewDecision['decision']>('approve')
  const [rationale, setRationale] = useState('')
  const [reviewerId, setReviewerId] = useState('compliance.officer@wealthfirm.com')
  const [seniorApproval, setSeniorApproval] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const submit = async () => {
    if (!sessionId || !rationale) return
    setLoading(true)
    setResult(null)
    try {
      const { data } = await clientApi.submitReviewDecision({
        session_id: sessionId,
        decision,
        rationale,
        reviewer_id: reviewerId,
        senior_approval_required: seniorApproval,
      })
      setResult(`Decision recorded: ${data.decision}. Step: ${data.current_step}${data.account_number ? ` | Account: ${data.account_number}` : ''}`)
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setResult(`Error: ${err.response?.data?.detail || 'Request failed.'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ShieldCheck className="text-navy-500" />
          Compliance Review
        </h1>
        <p className="text-sm text-gray-500 mt-1">BRD FR-H1 to FR-H4 — Human-in-the-Loop decisions</p>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800 space-y-1">
        <p className="font-semibold">BRD Compliance Rules:</p>
        <ul className="list-disc ml-4 space-y-0.5 text-xs">
          <li>FR-H1: Decision options limited to Approve | Reject | RFI | Escalate EDD</li>
          <li>FR-H2: Rejection requires documented rationale (mandatory)</li>
          <li>FR-H3: PEP case approval requires named senior management approver</li>
          <li>FR-H4: All actions logged with reviewer identity and timestamp</li>
        </ul>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Session ID</label>
          <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="e.g. 3f8e1a2b-..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Decision</label>
          <div className="grid grid-cols-4 gap-2">
            {(['approve', 'reject', 'rfi', 'escalate_edd'] as const).map((d) => {
              const icons = { approve: Check, reject: X, rfi: AlertCircle, escalate_edd: TrendingUp }
              const Icon = icons[d]
              const colors: Record<string, string> = {
                approve: 'border-green-500 bg-green-50 text-green-700',
                reject: 'border-red-500 bg-red-50 text-red-700',
                rfi: 'border-yellow-500 bg-yellow-50 text-yellow-700',
                escalate_edd: 'border-orange-500 bg-orange-50 text-orange-700',
              }
              return (
                <button
                  key={d}
                  onClick={() => setDecision(d)}
                  className={`flex flex-col items-center gap-1 p-3 rounded-lg border-2 text-xs font-semibold transition-all ${decision === d ? colors[d] : 'border-gray-200 bg-white text-gray-400'}`}
                >
                  <Icon size={18} />
                  {d.replace(/_/g, ' ').toUpperCase()}
                </button>
              )
            })}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Reviewer ID</label>
          <input
            type="text"
            value={reviewerId}
            onChange={(e) => setReviewerId(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Rationale (required for rejection)</label>
          <textarea
            rows={4}
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            placeholder="Document your decision rationale…"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-navy-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="senior"
            checked={seniorApproval}
            onChange={(e) => setSeniorApproval(e.target.checked)}
            className="rounded border-gray-300 text-navy-500"
          />
          <label htmlFor="senior" className="text-sm text-gray-700">
            Senior management approval obtained (required for PEP cases — FR-H3)
          </label>
        </div>

        <button
          onClick={submit}
          disabled={loading || !sessionId || !rationale}
          className="w-full flex items-center justify-center gap-2 bg-navy-500 hover:bg-navy-700 text-white py-3 rounded-lg font-semibold text-sm transition-all disabled:opacity-60"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <ShieldCheck size={18} />}
          Submit Decision
        </button>

        {result && (
          <div className={`rounded-lg px-4 py-3 text-sm border ${result.startsWith('Error') ? 'bg-red-50 text-red-700 border-red-200' : 'bg-green-50 text-green-700 border-green-200'}`}>
            {result}
          </div>
        )}
      </div>
    </div>
  )
}
