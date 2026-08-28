import { defineConfig } from 'vite';

export default defineConfig({
  worker: {
    format: 'es',
    plugins: []
  },
  optimizeDeps: {
    exclude: ['force-graph-3d']
  }
});