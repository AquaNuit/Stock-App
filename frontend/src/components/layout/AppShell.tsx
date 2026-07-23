import type { ReactNode } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { MarketStatusBanner } from '../ui/MarketStatusBanner'

export default function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <MarketStatusBanner />
        <Topbar />
        <main className="app-content">{children}</main>
      </div>
    </div>
  )
}
