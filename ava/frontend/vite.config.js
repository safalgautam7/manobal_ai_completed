import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/prompt': { target: 'http://localhost:8000', changeOrigin: true },
      '/analyze-emotion': { target: 'http://localhost:8000', changeOrigin: true },
      '/emotion-graph': { target: 'http://localhost:8000', changeOrigin: true },
      '/random-quote': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
})