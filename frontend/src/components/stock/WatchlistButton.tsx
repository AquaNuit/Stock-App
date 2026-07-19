import { useNavigate } from 'react-router-dom'
import { Star } from 'lucide-react'
import { useState } from 'react'
import { useAddWatchlist, useRemoveWatchlist, useWatchlist } from '@/hooks/api'
import { useToast } from '@/context/ToastContext'
import { Button } from '@/components/ui/Button'

export function WatchlistButton({ symbol, size = 'md' }: { symbol: string; size?: 'sm' | 'md' }) {
  const { data: watchlist } = useWatchlist()
  const add = useAddWatchlist()
  const remove = useRemoveWatchlist()
  const toast = useToast()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)

  const inList = (watchlist?.items ?? []).some((w) => w.symbol.toUpperCase() === symbol.toUpperCase())

  async function onClick() {
    setBusy(true)
    try {
      if (inList) {
        await remove.mutateAsync(symbol)
        toast.info(`${symbol} removed from watchlist`)
      } else {
        await add.mutateAsync(symbol)
        toast.success(`${symbol} added to watchlist`)
      }
    } catch (e) {
      toast.error((e as Error).message || 'Could not update watchlist')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Button
      variant={inList ? 'outline' : 'primary'}
      size={size}
      loading={busy || add.isPending || remove.isPending}
      icon={<Star size={15} fill={inList ? 'currentColor' : 'none'} />}
      onClick={onClick}
      onDoubleClick={() => navigate('/watchlist')}
      title="Add to / remove from watchlist"
    >
      {inList ? 'Watching' : 'Watch'}
    </Button>
  )
}
