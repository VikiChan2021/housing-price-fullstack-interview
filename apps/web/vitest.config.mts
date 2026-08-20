import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

export default defineConfig({
  resolve: {
    alias: {
      // Match the @/ imports configured for the Next.js application.
      "@": fileURLToPath(new URL(".", import.meta.url)),
    },
  },
  test: {
    // jsdom supplies browser APIs needed by the interactive React components.
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
  },
});
