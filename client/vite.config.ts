import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [
    tailwindcss(),
    react(),
    tsconfigPaths(),
  ],
  build: {
    outDir: '../public/app',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      // Story 8.3: unified dev script (Vite :5173 + FastAPI :8000 via single `npm run dev`).
      // All backend routes proxied through Vite to FastAPI on :8000.
      // Single regex covers /api, /whatsapp, /students, /grades, /broadcast (and future paths).
      '^/(api|whatsapp|students|grades|broadcast)': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
