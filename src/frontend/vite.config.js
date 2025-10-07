import { defineConfig } from 'vite';
import { resolve } from 'path';
import legacy from '@vitejs/plugin-legacy';

export default defineConfig({
  root: '.',
  publicDir: 'static/img',
  base: '/static/',

  build: {
    outDir: '../../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        app: resolve(__dirname, 'src/app.js'),
      },
      output: {
        entryFileNames: '[name]-[hash].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
    manifest: true,
    sourcemap: false,
  },

  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11'],
    }),
  ],

  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': 'http://localhost:5000',
      '/data': 'http://localhost:5000',
      '/manualTask': 'http://localhost:5000',
    },
  },

  css: {
    postcss: './postcss.config.js',
  },
});
