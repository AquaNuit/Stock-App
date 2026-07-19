import { API_BASE, getUserId } from '@/config/env'

export class ApiError extends Error {
  status: number
  code: string
  constructor(message: string, status: number, code = 'ERROR') {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

type QueryParam = string | number | boolean | undefined | null

function buildQuery(params?: Record<string, QueryParam>): string {
  if (!params) return ''
  const usp = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) usp.set(k, String(v))
  }
  const qs = usp.toString()
  return qs ? `?${qs}` : ''
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}/${path.replace(/^\//, '')}`
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body) headers.set('Content-Type', 'application/json')
  const userId = getUserId()
  if (userId) headers.set('X-User-Id', userId)

  let res: Response
  try {
    res = await fetch(url, { ...init, headers })
  } catch (err) {
    throw new ApiError('Network error — is the backend running?', 0, 'NETWORK')
  }

  if (res.status === 204) return undefined as T

  let body: unknown = null
  const text = await res.text()
  if (text) {
    try {
      body = JSON.parse(text)
    } catch {
      body = text
    }
  }

  if (!res.ok) {
    const detail =
      (body && typeof body === 'object' && 'detail' in body
        ? String((body as Record<string, unknown>).detail)
        : null) ||
      res.statusText ||
      'Request failed'
    const code = body && typeof body === 'object' && 'code' in body
      ? String((body as Record<string, unknown>).code)
      : 'ERROR'
    throw new ApiError(detail, res.status, code)
  }

  return body as T
}

export const api = {
  get: <T>(path: string, params?: Record<string, QueryParam>) =>
    request<T>(`${path}${buildQuery(params)}`),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

// Trigger a file download from a binary endpoint (export routes).
export async function downloadFile(
  path: string,
  filename: string,
  params?: Record<string, QueryParam>,
): Promise<void> {
  const url = `${API_BASE}/${path.replace(/^\//, '')}${buildQuery(params)}`
  const headers = new Headers()
  const userId = getUserId()
  if (userId) headers.set('X-User-Id', userId)

  const res = await fetch(url, { headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const j = await res.json()
      detail = j.detail || detail
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status, 'EXPORT_FAILED')
  }
  const blob = await res.blob()
  const href = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(href)
}
