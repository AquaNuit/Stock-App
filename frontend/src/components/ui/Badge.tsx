import clsx from 'clsx'
import type { ReactNode } from 'react'
import type { ConfidenceLabel, DataSource } from '@/types/api'

export function Badge({
  children,
  tone = 'neutral',
  className,
  title,
}: {
  children: ReactNode
  tone?: 'neutral' | 'up' | 'down' | 'accent' | 'warn' | 'info'
  className?: string
  title?: string
}) {
  return (
    <span className={clsx('badge', `badge--${tone}`, className)} title={title}>
      {children}
    </span>
  )
}

const SOURCE_LABEL: Record<DataSource, string> = {
  nse: 'NSE',
  yfinance: 'Yahoo',
  seed: 'Demo',
  cache: 'Cached',
  db: 'DB',
}

export function SourceBadge({ source }: { source: DataSource | string }) {
  const isDemo = source === 'seed'
  return (
    <Badge tone={isDemo ? 'warn' : 'info'} title={`Data source: ${source}`}>
      {SOURCE_LABEL[source as DataSource] ?? source}
    </Badge>
  )
}

export function ConfidenceBadge({ confidence }: { confidence: ConfidenceLabel | string }) {
  const tone = confidence === 'high' ? 'up' : confidence === 'medium' ? 'warn' : 'down'
  return <Badge tone={tone}>{confidence}</Badge>
}
