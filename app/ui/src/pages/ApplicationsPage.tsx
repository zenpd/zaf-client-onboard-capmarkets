import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { clientApi } from '../services/clientApi'
import { Loader2, FileText, ArrowRight, RefreshCw } from 'lucide-react'

type App = {
  session_id: string
  journey_type: string
  routing_lane?: string
  current_step?: string
  account_number?: string
  created_at?: string
}

const JOURNEY_PILL: Record<string, string> = {
  individual: 'journey-individual',
  joint: 'journey-joint',
  corporate: 'journey-corporate',
  trust: 'journey-trust',
}

const LANE_BADGE: Record<string, string> = {
  stp: 'status-complete',
  standard: 'status-active',
  enhanced: 'status-review',
  edd: 'status-review',
  hold: 'status-failed',
  reject: 'status-failed',
}

export default function ApplicationsPage() {
  const [apps, setApps] = useState<App[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    setError(null)
    clientApi.listApplications()
      .then(r => setApps(Array.isArray(r.data) ? r.data : (r.data.items ?? [])))
      .catch(() => setError('Failed to load applications.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <FileText size={20} className="text-zen-600" />
            Applications
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {loading ? 'Loading…' : `${apps.length} application${apps.length !== 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} disabled={loading} className="btn-ghost btn-sm">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <Link to="/onboard" className="btn-primary btn-sm">+ New Client</Link>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={24} className="animate-spin text-zen-500" />
        </div>
      )}

      {error && (
        <div className="card p-4 border-l-4 border-l-rose-400 bg-rose-50 text-rose-700 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && apps.length === 0 && (
        <div className="card p-12 flex flex-col items-center gap-4 text-center">
          <FileText size={36} className="text-gray-300" />
          <p className="text-gray-400 text-sm">No applications yet.</p>
          <Link to="/onboard" className="btn-primary btn-sm">Start First Onboarding</Link>
        </div>
      )}

      {!loading && apps.length > 0 && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-bold text-gray-500 uppercase tracking-widest">Session</th>
                <th className="text-left px-4 py-3 text-xs font-bold text-gray-500 uppercase tracking-widest">Journey</th>
                <th className="text-left px-4 py-3 text-xs font-bold text-gray-500 uppercase tracking-widest">Lane</th>
                <th className="text-left px-4 py-3 text-xs font-bold text-gray-500 uppercase tracking-widest">Step</th>
                <th className="text-left px-4 py-3 text-xs font-bold text-gray-500 uppercase tracking-widest">Account</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {apps.map(app => (
                <tr key={app.session_id} className="hover:bg-gray-50 transition-colors group">
                  <td className="px-4 py-3">
                    <code className="text-xs font-mono text-gray-600">{app.session_id.slice(0, 16)}…</code>
                  </td>
                  <td className="px-4 py-3">
                    {app.journey_type && (
                      <span className={JOURNEY_PILL[app.journey_type] || 'journey-individual'}>
                        {app.journey_type}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {app.routing_lane && (
                      <span className={LANE_BADGE[app.routing_lane] || 'status-pending'}>
                        {app.routing_lane}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-gray-600 capitalize">{app.current_step?.replace(/_/g, ' ') || '—'}</span>
                  </td>
                  <td className="px-4 py-3">
                    {app.account_number
                      ? <code className="text-xs font-mono text-emerald-600 font-semibold">{app.account_number}</code>
                      : <span className="text-xs text-gray-300">—</span>
                    }
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/applications/${app.session_id}`}
                      className="btn-ghost btn-sm opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      View <ArrowRight size={12} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
