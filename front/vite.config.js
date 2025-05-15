import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api/v1/locations': {
        target: 'http://0.0.0.0:8000/api/v1/locations',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/v1\/locations/, '')
      },
      '/api/v1/system': {
        target: 'http://0.0.0.0:8000/api/v1/system',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/v1\/system/, '')
      },
      '/api/v1/index_search': {
        target: 'http://0.0.0.0:8000/api/v1/index_search',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/v1\/index_search/, '')
      },
      '/api/v1/semantic': {
        target: 'http://0.0.0.0:8000/api/v1/semantic',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api\/v1\/semantic/, '')
      }
    }
  },
}); 