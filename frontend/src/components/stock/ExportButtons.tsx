import { Download } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { downloadFile } from '@/lib/api'
import { useToast } from '@/context/ToastContext'
import type { TimeRange } from '@/types/api'

export function ExportButtons({ symbol, range }: { symbol: string; range: TimeRange }) {
  const toast = useToast()
  const [busy, setBusy] = useState<string | null>(null)

  async function doExport(kind: 'history' | 'predictions', format: 'csv' | 'xlsx') {
    setBusy(`${kind}:${format}`)
    try {
      const path = kind === 'history' ? `export/history/${symbol}` : `export/predictions/${symbol}`
      const params = kind === 'history' ? { range, format } : { format }
      const filename = `stocksense_${symbol}_${kind === 'history' ? range + '_' : ''}${new Date().toISOString().slice(0, 10)}.${format}`
      await downloadFile(path, filename, params)
      toast.success(`Exported ${kind} (${format.toUpperCase()})`)
    } catch (e) {
      toast.error((e as Error).message || 'Export failed')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="export-buttons">
      <Button
        variant="outline"
        size="sm"
        icon={<Download size={14} />}
        loading={busy === 'history:csv'}
        onClick={() => doExport('history', 'csv')}
      >
        History CSV
      </Button>
      <Button
        variant="outline"
        size="sm"
        loading={busy === 'history:xlsx'}
        onClick={() => doExport('history', 'xlsx')}
      >
        History XLSX
      </Button>
      <Button
        variant="outline"
        size="sm"
        loading={busy === 'predictions:csv'}
        onClick={() => doExport('predictions', 'csv')}
      >
        Forecast CSV
      </Button>
      <Button
        variant="outline"
        size="sm"
        loading={busy === 'predictions:xlsx'}
        onClick={() => doExport('predictions', 'xlsx')}
      >
        Forecast XLSX
      </Button>
    </div>
  )
}
