import { defineConfig } from "@playwright/test";
import development from "./playwright.config";

export default defineConfig({
  ...development,
  testMatch: ["**/*.spec.ts", "**/*.local.ts"],
  use: { ...development.use, baseURL: "http://127.0.0.1:8766" },
  webServer: undefined,
});
