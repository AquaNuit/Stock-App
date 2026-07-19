import clsx from 'clsx'
import type { ReactNode } from 'react'
import { formatPct, formatSigned, changeColor } from '@/lib/format'

interface StatTileProps {
  label: string
  value: ReactNode
  sub?: ReactNode
  delta?: number
  className?: string
}

export function StatTile({ label, value, sub, delta, className }: StatTileProps) {
  return (
    <div className={clsx('stat-tile', className)}>
      <span className="stat-tile__label">{label}</span>
      <span className="stat-tile__value">{value}</span>
      {(sub || delta !== undefined) && (
        <span className="stat-tile__sub">
          {delta !== undefined && (
            <span style={{ color: changeColor(delta) }}>
              {formatSigned(delta)} ({formatPct(delta)})
            </span>
          )}
          {sub}
        </span>
      )}
    </div>
  )
}
