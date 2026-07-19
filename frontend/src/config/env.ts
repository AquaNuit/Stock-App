// Centralised runtime configuration. Reads build-time env vars injected by Vite.
//
// API_BASE resolution:
//   - Dev (default):  '/api/v1'  -> served by the Vite dev proxy -> http://localhost:8000
//   - Prod (Netlify): set the Netlify build env `VITE_API_BASE` to your deployed
//     API origin, e.g. https://api.stocksense.app/api/v1
export const API_BASE: string = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') || '/api/v1'

export const APP_NAME = 'StockSense AI'
export const APP_VERSION = '0.1.0'

// Optional: override the default user id used for watchlist/recents (X-User-Id header).
export const DEFAULT_USER_ID = 'guest'

const USER_ID_KEY = 'stocksense:user_id'
const THEME_KEY = 'stocksense:theme'

export function getUserId(): string {
  try {
    return localStorage.getItem(USER_ID_KEY) || DEFAULT_USER_ID
  } catch {
    return DEFAULT_USER_ID
  }
}

export function setUserId(id: string): void {
  try {
    localStorage.setItem(USER_ID_KEY, id.trim() || DEFAULT_USER_ID)
  } catch {
    /* ignore */
  }
}

export function getStoredTheme(): 'dark' | 'light' {
  try {
    const t = localStorage.getItem(THEME_KEY)
    return t === 'light' ? 'light' : 'dark'
  } catch {
    return 'dark'
  }
}

export function setStoredTheme(theme: 'dark' | 'light'): void {
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    /* ignore */
  }
}
