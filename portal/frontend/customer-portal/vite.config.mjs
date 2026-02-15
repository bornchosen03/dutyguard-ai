import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    watch: {
      // Avoid scanning parent folders or large paths which can slow Vite's watcher
      ignored: ["**/node_modules/**", "**/.git/**", "../../**"]
    }
  },
});
