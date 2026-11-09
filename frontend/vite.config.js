import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Backend URL for the dev proxy. Default is local Flask on 5000; override with
// VITE_PROXY_TARGET (e.g. VITE_PROXY_TARGET=http://127.0.0.1:5001 for a server
// started on a different port) or wire a production API base via VITE_API_BASE.
const target = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:5000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target, changeOrigin: true },
      '/login/google': { target, changeOrigin: false },
      '/google/callback': { target, changeOrigin: false },
      '/static': { target, changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
