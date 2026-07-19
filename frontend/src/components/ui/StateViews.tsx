import { motion } from 'framer-motion'
import { Inbox, ServerCrash, Loader2 } from 'lucide-react'
import type { ReactNode } from 'react'

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="state-view">
      <Loader2 size={26} className="spin" />
      {label && <p className="state-view__label">{label}</p>}
    </div>
  )
}

export function Skeleton({ height = 16, width = '100%', radius = 8 }: { height?: number; width?: number | string; radius?: number }) {
  return <div className="skeleton" style={{ height, width, borderRadius: radius }} />
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state-view state-view--error">
      <ServerCrash size={28} />
      <p className="state-view__label">{message}</p>
      {onRetry && (
        <button className="btn btn--outline btn--sm" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, hint, icon }: { title: string; hint?: string; icon?: ReactNode }) {
  return (
    <motion.div className="state-view" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      {icon ?? <Inbox size={28} />}
      <p className="state-view__label">{title}</p>
      {hint && <p className="state-view__hint">{hint}</p>}
    </motion.div>
  )
}
