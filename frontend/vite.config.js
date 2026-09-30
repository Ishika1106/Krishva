import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Vercel/read-only static hosts cannot bind the preview to localhost only.
    host: true,
  },
});
