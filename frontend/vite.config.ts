import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Forwards to the FastAPI dev server (`uv run uvicorn app.main:app
      // --reload`, standard port). Frontend code fetches "/api/..." —
      // same-origin from the browser's point of view (issue #26).
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
