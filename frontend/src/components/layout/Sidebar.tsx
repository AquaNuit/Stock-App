import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import { BrainCircuit, GitCompareArrows, LayoutDashboard, Search, Star, TrendingUp, X } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'
import { APP_NAME } from '@/config/env'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/search', label: 'Search', icon: Search, end: false },
  { to: '/predict', label: 'AI Forecast', icon: BrainCircuit, end: false },
  { to: '/watchlist', label: 'Watchlist', icon: Star, end: false },
  { to: '/compare', label: 'Compare', icon: GitCompareArrows, end: false },
]

export default function Sidebar() {
  const open = useUIStore((s) => s.sidebarOpen)
  const setSidebar = useUIStore((s) => s.setSidebar)

  return (
    <>
      {open && <div className="sidebar-scrim" onClick={() => setSidebar(false)} />}
      <aside className={clsx('sidebar', open && 'is-open')}>
        <div className="sidebar__brand">
          <span className="sidebar__logo">
            <TrendingUp size={20} />
          </span>
          <div>
            <strong>{APP_NAME}</strong>
            <small style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', display: 'block' }}>Developed By Aarav Trivedi</small>
          </div>
          <button className="sidebar__close" onClick={() => setSidebar(false)} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar__nav">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) => clsx('sidebar__link', isActive && 'is-active')}
              onClick={() => setSidebar(false)}
            >
              <n.icon size={18} />
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>

          <span className="sidebar__ver">v{import.meta.env.VITE_APP_VERSION ?? '0.1.0'}</span>
      </aside>
    </>
  )
}
