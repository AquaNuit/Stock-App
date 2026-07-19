import { useEffect, useRef, useState } from 'react'
import { Search, TrendingUp } from 'lucide-react'
import clsx from 'clsx'
import { useDebounce } from '@/hooks/useDebounce'
import { useSearch } from '@/hooks/api'

interface SymbolInputProps {
  value: string
  onChange: (symbol: string) => void
  placeholder?: string
}

// Autocomplete input that resolves to a symbol WITHOUT navigating away
// (used by the forecast studio where the symbol stays on the page).
export function SymbolInput({ value, onChange, placeholder = 'Enter NSE ticker (e.g. RELIANCE)' }: SymbolInputProps) {
  const [text, setText] = useState(value)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const debounced = useDebounce(text, 200)
  const boxRef = useRef<HTMLDivElement>(null)
  const { data, isFetching } = useSearch(debounced, 8)
  const items = data?.items ?? []

  useEffect(() => setText(value), [value])
  useEffect(() => setActive(0), [debounced])

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  function select(sym: string) {
    setText(sym)
    onChange(sym)
    setOpen(false)
  }

  function onKey(e: React.KeyboardEvent) {
    if (!open || items.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((a) => Math.min(a + 1, items.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) => Math.max(a - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      select(items[active]?.symbol ?? text.trim().toUpperCase())
    }
  }

  return (
    <div className="symbol-input" ref={boxRef}>
      <div className="symbol-input__field">
        <Search size={15} />
        <input
          value={text}
          placeholder={placeholder}
          onChange={(e) => {
            setText(e.target.value)
            setOpen(true)
          }}
          onFocus={() => text && setOpen(true)}
          onKeyDown={onKey}
          aria-label="Symbol"
        />
      </div>
      {open && text.trim() && (
        <div className="symbol-input__dropdown glass">
          {isFetching && !data && <div className="symbol-input__row symbol-input__row--muted">Searching…</div>}
          {!isFetching && items.length === 0 && (
            <div className="symbol-input__row symbol-input__row--muted">No matches — press Enter to use “{text.trim().toUpperCase()}”</div>
          )}
          {items.map((it, i) => (
            <button
              key={it.symbol}
              className={clsx('symbol-input__row', i === active && 'is-active')}
              onMouseEnter={() => setActive(i)}
              onClick={() => select(it.symbol)}
            >
              <TrendingUp size={13} />
              <strong>{it.symbol}</strong>
              <span>{it.company_name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
