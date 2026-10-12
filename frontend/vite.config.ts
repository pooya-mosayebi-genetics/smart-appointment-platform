import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true, // اجازه دسترسی از خارج کانتینر
    proxy: {
      '/api': {
        // target: 'http://127.0.0.1:8081', // ❌ حذف شد
        target: 'http://backend:8000',     // ✅ اضافه شد: نام سرویس در docker-compose + پورت داخلی
        changeOrigin: true,
        secure: false,
      },
    },
  },
})