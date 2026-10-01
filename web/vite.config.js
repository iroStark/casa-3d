import { defineConfig } from "vite";
export default defineConfig({
  base: process.env.BASE || "./",
  build: { outDir: "dist", assetsInlineLimit: 0, chunkSizeWarningLimit: 900 },
  server: { port: 5178 },
});
