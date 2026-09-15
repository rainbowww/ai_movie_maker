import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Frontend (Vite dev server, :5173) proxies API + generated media requests
// to the Python backend (uvicorn, :8000) — see README.md for how to run both.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/media': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
  },
});
