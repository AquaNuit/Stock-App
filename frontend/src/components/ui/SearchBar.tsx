import { useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { Search, TrendingUp, X } from 'lucide-react'
import clsx from 'clsx'
import { useDebounce } from '@/hooks/useDebounce'
import { useSearch } from '@/hooks/api'
import { Spinner } from './StateViews'
import { formatPct, changeColor } from '@/lib/format'

interface SearchBarProps {
  placeholder?: string
  autoFocus?: boolean
  onNavigate?: () => void
}

export function SearchBar({ placeholder = 'Search NSE stocks, ticker or sector…', autoFocus, onNavigate }: SearchBarProps) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const debounced = useDebounce(q, 250)
  const navigate = useNavigate()
  const boxRef = useRef<HTMLDivElement>(null)

  const { data, isFetching } = useSearch(debounced, 8)
  const items = data?.items ?? []

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  useEffect(() => {
    setActive(0)
  }, [debounced])

  function go(symbol: string) {
    navigate(`/stocks/${symbol}`)
    setOpen(false)
    setQ('')
    onNavigate?.()
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (!open || items.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((a) => Math.min(a + 1, items.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) => Math.max(a - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      const item = items[active]
      if (item) go(item.symbol)
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="searchbar" ref={boxRef}>
      <div className="searchbar__input">
        <Search size={16} className="searchbar__icon" />
        <input
          value={q}
          autoFocus={autoFocus}
          placeholder={placeholder}
          onChange={(e) => {
            setQ(e.target.value)
            setOpen(true)
          }}
          onFocus={() => q && setOpen(true)}
          onKeyDown={onKeyDown}
          aria-label="Search stocks"
        />
        {q && (
          <button className="searchbar__clear" onClick={() => setQ('')} aria-label="Clear">
            <X size={14} />
          </button>
        )}
      </div>

      {open && q.trim() && (
        <div className="searchbar__dropdown glass">
          {isFetching && !data && (
            <div className="searchbar__row searchbar__row--muted">
              <Spinner />
            </div>
          )}
          {!isFetching && items.length === 0 && (
            <div className="searchbar__row searchbar__row--muted">No matches for “{q}”</div>
          )}
          {items.map((it, i) => (
            <button
              key={it.symbol}
              className={clsx('searchbar__row', i === active && 'is-active')}
              onMouseEnter={() => setActive(i)}
              onClick={() => go(it.symbol)}
            >
              <span className="searchbar__sym">
                <TrendingUp size={14} />
                {it.symbol}
              </span>
              <span className="searchbar__name">{it.company_name}</span>
              {it.sector && <span className="searchbar__sector">{it.sector}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
