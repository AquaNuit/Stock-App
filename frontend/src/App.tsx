import { BrowserRouter, Route, Routes } from 'react-router-dom'
import AppShell from '@/components/layout/AppShell'
import DashboardPage from '@/pages/DashboardPage'
import SearchPage from '@/pages/SearchPage'
import StockDetailPage from '@/pages/StockDetailPage'
import PredictPage from '@/pages/PredictPage'
import WatchlistPage from '@/pages/WatchlistPage'
import ComparePage from '@/pages/ComparePage'
import NotFoundPage from '@/pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/stocks/:symbol" element={<StockDetailPage />} />
          <Route path="/predict" element={<PredictPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}
