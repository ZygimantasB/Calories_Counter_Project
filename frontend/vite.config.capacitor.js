import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Build config for the standalone Capacitor (Android) app.
// Differs from vite.config.js (Django build) in two ways:
//   - base: './'   -> relative asset URLs for the file:// webview
//   - outDir: dist -> Capacitor's webDir (copied into ../android_calories_app on `cap sync`)
// The Django web deployment keeps using vite.config.js untouched.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
