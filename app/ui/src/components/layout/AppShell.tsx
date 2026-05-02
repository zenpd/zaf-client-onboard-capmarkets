import { useState, useEffect } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Users, ShieldCheck, FileText,
  Settings, Zap, ChevronRight, Bot, ScrollText,
  Bell, Search, AlertTriangle, CheckCircle2, Clock, X,
} from 'lucide-react'
import clsx from 'clsx'
import { clientApi } from '../../services/clientApi'

/* ─── Navigation ─────────────────────────────────────────── */
const BASE_NAV = [
  { label: 'Dashboard',           icon: LayoutDashboard, path: '/dashboard' },
  { label: 'New Client',          icon: Users,            path: '/onboard' },
  { label: 'Compliance Queue',    icon: ShieldCheck,      path: '/compliance', badgeKey: 'compliance' },
  { label: 'Applications',        icon: FileText,         path: '/applications' },
  { label: 'Audit Trail',         icon: ScrollText,       path: '/audit' },
  { label: 'AI Agents',           icon: Bot,              path: '/agents' },
]
const BOTTOM_NAV = [
  { label: 'Settings', icon: Settings, path: '/settings' },
]

/* ─── Notifications ──────────────────────────────────────── */
const NOTIFS = [
  { id: 1, icon: AlertTriangle,  iconBg: 'bg-rose-100',    iconColor: 'text-rose-600',    title: 'High-risk application flagged', body: 'PEP match on session #3f2a — MLRO review required.', time: '4m ago',  unread: true },
  { id: 2, icon: Clock,          iconBg: 'bg-amber-100',   iconColor: 'text-amber-600',   title: 'KYC/AML review pending',       body: '2 EDD cases awaiting compliance officer sign-off.',  time: '22m ago', unread: true },
  { id: 3, icon: CheckCircle2,   iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600', title: 'Individual onboarding STP',    body: 'Client approved — Account No. WM-00412 created.',   time: '1h ago',  unread: false },
]

/* ─── Sidebar ────────────────────────────────────────────── */
function Sidebar({ pendingCount }: { pendingCount: number | null }) {
  const NAV = BASE_NAV.map(item =>
    item.badgeKey === 'compliance' && pendingCount
      ? { ...item, badge: String(pendingCount) }
      : item
  )
  return (
    <aside className="fixed top-0 left-0 bottom-0 w-[240px] bg-white shadow-sidebar z-30 flex flex-col">
      {/* Logo */}
      <div className="h-[60px] flex items-center px-5 border-b border-gray-100 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="relative w-8 h-8 rounded-xl bg-gradient-zen flex items-center justify-center shadow-glow-zen flex-shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <span className="font-extrabold text-gray-900 text-base tracking-tight">ZenLabs</span>
            <span className="block text-[10px] font-medium text-gray-400 -mt-0.5 tracking-wide uppercase">Cap Markets</span>
          </div>
        </div>
      </div>

      {/* Main nav */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <p className="section-title px-1 mb-2">Navigation</p>
        <nav className="space-y-0.5">
          {NAV.map(({ label, icon: Icon, path, badge }: any) => (
            <NavLink key={path} to={path} end={path === '/dashboard'}
              className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}>
              <Icon size={16} />
              <span className="flex-1">{label}</span>
              {badge && (
                <span className="ml-auto text-[10px] font-bold bg-rose-500 text-white px-1.5 py-0.5 rounded-full min-w-[18px] text-center shadow-sm">
                  {badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="my-4 border-t border-gray-100" />
        <p className="section-title px-1 mb-2">Journeys</p>
        <nav className="space-y-0.5">
          {[
            { label: 'Individual / HNW',  letter: 'I', gradient: 'bg-gradient-individual', path: '/onboard' },
            { label: 'Corporate / UBO',   letter: 'C', gradient: 'bg-gradient-corporate',  path: '/onboard' },
            { label: 'Trust / Foundation',letter: 'T', gradient: 'bg-gradient-trust',      path: '/onboard' },
          ].map(j => (
            <NavLink key={j.label} to={j.path}
              className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}>
              <span className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-extrabold flex-shrink-0 text-white ${j.gradient} shadow-sm`}>
                {j.letter}
              </span>
              <span className="flex-1 text-xs">{j.label}</span>
              <ChevronRight size={12} className="text-gray-300" />
            </NavLink>
          ))}
        </nav>
      </div>

      {/* System status */}
      <div className="px-4 py-2.5 border-t border-gray-100">
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-emerald-50 border border-emerald-100">
          <span className="live-dot flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-bold text-emerald-700 uppercase tracking-wide">All systems operational</p>
            <p className="text-[10px] text-emerald-600/70">API · Temporal · Agents</p>
          </div>
        </div>
      </div>

      {/* Bottom nav */}
      <div className="px-3 pb-3 space-y-0.5">
        {BOTTOM_NAV.map(({ label, icon: Icon, path }) => (
          <NavLink key={path} to={path}
            className={({ isActive }) => clsx('sidebar-link', isActive && 'active')}>
            <Icon size={16} />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </aside>
  )
}

/* ─── Header ─────────────────────────────────────────────── */
function Header({ title, subtitle }: { title?: string; subtitle?: string }) {
  const [notifOpen, setNotifOpen] = useState(false)
  const [notifs, setNotifs] = useState(NOTIFS)
  const unread = notifs.filter(n => n.unread).length

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      const target = e.target as HTMLElement
      if (!target.closest('#notif-dropdown')) setNotifOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <header className="fixed top-0 left-[240px] right-0 h-[60px] bg-white shadow-header z-20 flex items-center justify-between px-6 gap-4">
      <div className="min-w-0">
        {title && <h1 className="text-sm font-semibold text-gray-900 truncate">{title}</h1>}
        {subtitle && <p className="text-xs text-gray-400 truncate">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative hidden md:block">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input placeholder="Search sessions…"
            className="pl-8 pr-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-xl w-52 focus:outline-none focus:ring-2 focus:ring-zen-400 focus:border-zen-400 transition-all" />
        </div>

        {/* Notifications */}
        <div id="notif-dropdown" className="relative">
          <button onClick={() => setNotifOpen(v => !v)}
            className="relative w-9 h-9 flex items-center justify-center rounded-xl hover:bg-gray-100 text-gray-500 transition-colors">
            <Bell size={16} />
            {unread > 0 && <span className="notif-badge">{unread}</span>}
          </button>
          {notifOpen && (
            <div className="absolute right-0 top-11 w-80 card shadow-card-hover animate-slide-up z-50">
              <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
                <span className="text-sm font-semibold text-gray-900">Notifications</span>
                <div className="flex items-center gap-2">
                  <button onClick={() => setNotifs(prev => prev.map(n => ({ ...n, unread: false })))}
                    className="text-xs text-zen-600 hover:underline">Mark all read</button>
                  <button onClick={() => setNotifOpen(false)} className="text-gray-400 hover:text-gray-600"><X size={14} /></button>
                </div>
              </div>
              <div className="divide-y divide-gray-50 max-h-72 overflow-y-auto">
                {notifs.map(n => {
                  const Icon = n.icon
                  return (
                    <div key={n.id} className={`flex gap-3 px-4 py-3 transition-colors ${n.unread ? 'bg-zen-50/40' : ''}`}>
                      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${n.iconBg}`}>
                        <Icon size={14} className={n.iconColor} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-gray-800">{n.title}</p>
                        <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.body}</p>
                        <p className="text-[10px] text-gray-400 mt-1">{n.time}</p>
                      </div>
                      {n.unread && <span className="mt-1 w-1.5 h-1.5 rounded-full bg-zen-500 flex-shrink-0" />}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Avatar */}
        <div className="w-8 h-8 rounded-xl bg-gradient-zen flex items-center justify-center text-white text-xs font-bold shadow-sm">
          CO
        </div>
      </div>
    </header>
  )
}

/* ─── Footer ─────────────────────────────────────────────── */
function Footer() {
  return (
    <footer className="fixed bottom-0 left-[240px] right-0 h-[44px] bg-white border-t border-gray-100 z-20
      flex items-center justify-between px-6 text-[11px] text-gray-400">
      <span>ZenLabs AgentFoundry · Cap Markets Onboarding · BRD UC-01</span>
      <span className="flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
        Temporal Orchestration Active
      </span>
    </footer>
  )
}

/* ─── AppShell ───────────────────────────────────────────── */
export default function AppShell() {
  const [pendingCount, setPendingCount] = useState<number | null>(null)
  const [pageTitle] = useState<string | undefined>(undefined)

  useEffect(() => {
    let cancelled = false
    async function fetch() {
      try {
        const { data } = await clientApi.getComplianceQueue()
        if (!cancelled) setPendingCount(Array.isArray(data) ? data.length : (data.total_pending ?? 0))
      } catch { /* ignore */ }
    }
    fetch()
    const id = setInterval(fetch, 60_000)
    return () => { cancelled = true; clearInterval(id) }
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar pendingCount={pendingCount} />
      <Header title={pageTitle} />
      <main className="ml-[240px] mt-[60px] mb-[44px] min-h-[calc(100vh-104px)] overflow-y-auto">
        <div className="p-6 animate-fade-in">
          <Outlet />
        </div>
      </main>
      <Footer />
    </div>
  )
}

