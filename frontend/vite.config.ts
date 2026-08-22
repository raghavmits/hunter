import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/contacts": "http://localhost:8000",
      "/companies": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
