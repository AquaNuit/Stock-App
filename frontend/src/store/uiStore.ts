import { create } from 'zustand'
import { getStoredTheme, setStoredTheme } from '@/config/env'

type Theme = 'dark' | 'light'

interface UIState {
  theme: Theme
  sidebarOpen: boolean
  toggleTheme: () => void
  setSidebar: (open: boolean) => void
}

function applyTheme(theme: Theme) {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', theme)
  }
}

const initialTheme = getStoredTheme()
applyTheme(initialTheme)

export const useUIStore = create<UIState>((set, get) => ({
  theme: initialTheme,
  sidebarOpen: false,
  toggleTheme: () => {
    const next: Theme = get().theme === 'dark' ? 'light' : 'dark'
    setStoredTheme(next)
    applyTheme(next)
    set({ theme: next })
  },
  setSidebar: (open: boolean) => set({ sidebarOpen: open }),
}))
