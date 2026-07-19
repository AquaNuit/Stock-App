import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// StockSense AI — Vite config.
// - Dev: relative `/api/v1` calls are proxied to the local FastAPI backend
//   (http://localhost:8000) so you can run the SPA and backend side-by-side
//   with zero CORS friction. See src/config/env.ts (VITE_API_BASE).
// - Prod: point VITE_API_BASE at your deployed API (Netlify build env) OR
//   use a Netlify `/api/*` rewrite (see netlify.toml).

const API_TARGET = process.env.API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4173,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          echarts: ['echarts', 'echarts-for-react'],
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query'],
          motion: ['framer-motion'],
        },
      },
    },
  },
})
