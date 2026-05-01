import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Users, ShieldCheck, FileText,
  ClipboardList, Bot, Settings, ChevronRight,
} from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { to: '/dashboard',  label: 'Dashboard',    icon: LayoutDashboard },
  { to: '/onboard',    label: 'New Client',    icon: Users },
  { to: '/compliance', label: 'Compliance',    icon: ShieldCheck },
  { to: '/audit',      label: 'Audit Trail',   icon: FileText },
  { to: '/agents',     label: 'AI Agents',     icon: Bot },
  { to: '/settings',   label: 'Settings',      icon: Settings },
]

export default function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-gradient-navy text-white flex flex-col shadow-glow-navy">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-gold flex items-center justify-center shadow-glow-gold">
              <span className="text-navy-900 font-bold text-sm">Z</span>
            </div>
            <div>
              <p className="font-bold text-sm leading-tight">ZenLabs Foundry</p>
              <p className="text-white/50 text-xs">Cap Markets Platform</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-gold-500/20 text-gold-300 shadow-inner'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={18} className={isActive ? 'text-gold-300' : ''} />
                  <span className="flex-1">{label}</span>
                  {isActive && <ChevronRight size={14} className="text-gold-300/60" />}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-white/10 text-white/40 text-xs">
          WM Onboarding v1.0 · BRD UC-01
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto bg-slate-50">
        <Outlet />
      </main>
    </div>
  )
}
