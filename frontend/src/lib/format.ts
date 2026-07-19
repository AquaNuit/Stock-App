// Display formatters (INR-centric, Indian number grouping where useful).

const INR = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

const NUM = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 })
const INT = new Intl.NumberFormat('en-IN')

export function formatINR(value: number | null | undefined, fallback = '—'): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback
  return INR.format(value)
}

export function formatNumber(value: number | null | undefined, fallback = '—'): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback
  return NUM.format(value)
}

export function formatInt(value: number | null | undefined, fallback = '—'): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback
  return INT.format(value)
}

// Compact volume: 1.2M, 3.4B, etc.
export function formatCompact(value: number | null | undefined, fallback = '—'): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback
  const abs = Math.abs(value)
  const sign = value < 0 ? '-' : ''
  if (abs >= 1e9) return `${sign}${(abs / 1e9).toFixed(2)}B`
  if (abs >= 1e7) return `${sign}${(abs / 1e7).toFixed(2)}Cr`
  if (abs >= 1e5) return `${sign}${(abs / 1e5).toFixed(2)}L`
  return sign + INT.format(Math.round(abs))
}

export function formatPct(value: number | null | undefined, digits = 2, fallback = '—'): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}%`
}

export function formatSigned(value: number | null | undefined, digits = 2, fallback = '—'): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return fallback
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(digits)}`
}

export function formatDate(iso: string | null | undefined, pattern = 'dd MMM yyyy'): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  const day = String(d.getDate()).padStart(2, '0')
  const month = d.toLocaleString('en-IN', { month: 'short' })
  const year = d.getFullYear()
  if (pattern === 'dd MMM yyyy') return `${day} ${month} ${year}`
  if (pattern === 'dd MMM') return `${day} ${month}`
  return `${day} ${month} ${year}`
}

// "2h ago", "3d ago" relative formatter for recents.
export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return ''
  const d = new Date(iso).getTime()
  if (Number.isNaN(d)) return ''
  const diff = Date.now() - d
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const days = Math.floor(h / 24)
  return `${days}d ago`
}

export function changeColor(value: number | null | undefined): string {
  if (value === null || value === undefined || value === 0) return 'var(--text-dim)'
  return value > 0 ? 'var(--up)' : 'var(--down)'
}

export function marketCapLabel(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  const cr = value / 1e7
  if (cr >= 1e5) return `${formatNumber(cr / 1e5)} Lakh Cr`
  if (cr >= 1e3) return `${formatNumber(cr / 1e3)} K Cr`
  return `${formatNumber(cr)} Cr`
}
