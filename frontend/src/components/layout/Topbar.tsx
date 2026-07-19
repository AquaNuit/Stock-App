import { useNavigate } from 'react-router-dom'
import { Menu, Moon, Sun, Activity } from 'lucide-react'
import { SearchBar } from '@/components/ui/SearchBar'
import { useUIStore } from '@/store/uiStore'
import { useHealth } from '@/hooks/api'

export default function Topbar() {
  const setSidebar = useUIStore((s) => s.setSidebar)
  const theme = useUIStore((s) => s.theme)
  const toggleTheme = useUIStore((s) => s.toggleTheme)
  const navigate = useNavigate()
  const { data: health } = useHealth()

  return (
    <header className="topbar glass">
      <button className="topbar__menu" onClick={() => setSidebar(true)} aria-label="Open menu">
        <Menu size={20} />
      </button>

      <div className="topbar__search">
        <SearchBar onNavigate={() => setSidebar(false)} />
      </div>

      <div className="topbar__actions">
        <span className={`status-dot ${health?.status === 'ok' ? 'is-up' : 'is-down'}`} title={health ? `API ${health.status}` : 'API'}>
          <Activity size={14} />
          {health?.status === 'ok' ? 'Live' : '…'}
        </span>
        <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <button className="btn btn--primary btn--sm" onClick={() => navigate('/predict')}>
          Forecast
        </button>
      </div>
    </header>
  )
}
