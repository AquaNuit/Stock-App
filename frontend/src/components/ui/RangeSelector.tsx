import clsx from 'clsx'
import type { TimeRange } from '@/types/api'

interface RangeSelectorProps {
  value: TimeRange
  onChange: (r: TimeRange) => void
  options?: { value: TimeRange; label: string }[]
  size?: 'sm' | 'md'
}

export function RangeSelector({ value, onChange, options, size = 'md' }: RangeSelectorProps) {
  const opts = options ?? [
    { value: '1m', label: '1M' },
    { value: '3m', label: '3M' },
    { value: '6m', label: '6M' },
    { value: '1y', label: '1Y' },
    { value: '2y', label: '2Y' },
    { value: '5y', label: '5Y' },
    { value: 'max', label: 'MAX' },
  ]
  return (
    <div className={clsx('range-selector', `range-selector--${size}`)} role="tablist" aria-label="Time range">
      {opts.map((o) => (
        <button
          key={o.value}
          role="tab"
          aria-selected={o.value === value}
          className={clsx('range-selector__item', o.value === value && 'is-active')}
          onClick={() => onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}
