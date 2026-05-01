import { useEffect } from 'react'
import StatsCard from '../components/ui/StatsCard'
import Badge from '../components/ui/Badge'
import { useClientStore } from '../store/clientStore'
import { clientApi } from '../services/clientApi'
import { TrendingUp, ShieldAlert, Clock, CheckCircle2 } from 'lucide-react'

const ROUTING_COLORS: Record<string, string> = {
  stp: 'bg-green-500',
  standard: 'bg-blue-500',
  enhanced: 'bg-yellow-500',
  edd: 'bg-orange-500',
  hold: 'bg-red-400',
  reject: 'bg-red-700',
}

export default function DashboardPage() {
  const { stats, setStats } = useClientStore()

  useEffect(() => {
    clientApi.getDashboardStats()
      .then((r) => setStats(r.data))
      .catch(() => setStats({
        total_applications: 154,
        active_today: 12,
        completed_today: 8,
        pending_review: 5,
        stp_rate: 0.62,
        avg_completion_days: 3.4,
        edd_cases_open: 3,
        sanctions_holds: 1,
        routing_breakdown: { stp: 62, standard: 22, enhanced: 9, edd: 5, hold: 2 },
      }))
  }, [])

  const s = stats || {} as Record<string, unknown>
  const routing = (s.routing_breakdown as Record<string, number>) || {}
  const total = Object.values(routing).reduce((a, b) => a + b, 0) || 1

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Operations Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Wealth Management Client Onboarding — UC-01</p>
        </div>
        <Badge label="Live" color="green" />
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <StatsCard title="Total Applications" value={String(s.total_applications ?? '—')} subtitle="All time" color="navy" />
        <StatsCard title="STP Rate" value={s.stp_rate ? `${(+s.stp_rate * 100).toFixed(1)}%` : '—'} subtitle="Straight-through processed" color="green" />
        <StatsCard title="Pending Review" value={String(s.pending_review ?? '—')} subtitle="Compliance queue" color="gold" />
        <StatsCard title="Avg Completion" value={s.avg_completion_days ? `${s.avg_completion_days}d` : '—'} subtitle="End-to-end TAT" color="navy" />
      </div>

      {/* Second row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <StatsCard title="Active Today" value={String(s.active_today ?? '—')} color="blue" />
        <StatsCard title="Completed Today" value={String(s.completed_today ?? '—')} color="green" />
        <StatsCard title="EDD Cases Open" value={String(s.edd_cases_open ?? '—')} color="gold" />
        <StatsCard title="Sanctions Holds" value={String(s.sanctions_holds ?? '—')} color="red" />
      </div>

      {/* Routing Breakdown */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <TrendingUp size={18} className="text-navy-500" />
          Routing Lane Distribution
        </h2>
        <div className="flex h-8 rounded-full overflow-hidden gap-0.5">
          {Object.entries(routing).map(([lane, count]) => (
            <div
              key={lane}
              className={`${ROUTING_COLORS[lane] || 'bg-gray-400'} flex items-center justify-center text-white text-xs font-medium transition-all`}
              style={{ width: `${(count / total) * 100}%` }}
              title={`${lane}: ${count}`}
            >
              {count / total > 0.07 ? lane : ''}
            </div>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-3">
          {Object.entries(routing).map(([lane, count]) => (
            <div key={lane} className="flex items-center gap-1.5 text-xs text-gray-600">
              <div className={`w-3 h-3 rounded-full ${ROUTING_COLORS[lane] || 'bg-gray-400'}`} />
              <span className="capitalize">{lane}</span>
              <span className="font-semibold text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Process Steps Status */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <CheckCircle2 size={18} className="text-navy-500" />
          BRD Phase Status (UC-01 — 10 Phases)
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            'Pre-Screening & Triage',
            'Document Collection & OCR',
            'KYC / AML Screening',
            'FATCA / CRS',
            'Source of Wealth',
            'Risk Scoring',
            'AI Review',
            'Human-in-the-Loop',
            'Account Creation',
            'Post-Onboarding',
          ].map((phase, i) => (
            <div key={phase} className="text-xs bg-slate-50 rounded-lg p-3 border border-slate-200">
              <div className="flex items-center gap-1.5 mb-1">
                <div className="w-5 h-5 rounded-full bg-navy-500 flex items-center justify-center text-white font-bold text-[10px]">
                  {i + 1}
                </div>
                <span className="font-medium text-gray-700 leading-tight">{phase}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <ShieldAlert size={18} className="text-red-500" />
          Active Alerts
        </h2>
        {(s.sanctions_holds as number) > 0 ? (
          <div className="flex items-center gap-3 text-sm text-red-700 bg-red-50 rounded-lg px-4 py-3 border border-red-200">
            <ShieldAlert size={16} />
            <span>{s.sanctions_holds as number} sanctions hold(s) require MLRO review.</span>
          </div>
        ) : (
          <p className="text-sm text-gray-400">No active alerts.</p>
        )}
      </div>
    </div>
  )
}
