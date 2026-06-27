import { sveltekit } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/analyze': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
