import { defineConfig } from "@playwright/test";
import path from "path";

const hmiDir = path.join(__dirname, "..");

export default defineConfig({
  testDir: ".",
  testMatch: "smoke.spec.ts",
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  timeout: 45_000,
  use: {
    baseURL: "http://127.0.0.1:5199",
    trace: "on-first-retry",
  },
  webServer: {
    command: "npx http-server . -p 5199 -c-1 --silent",
    cwd: hmiDir,
    url: "http://127.0.0.1:5199/l3_sa_bootcamp.html",
    reuseExistingServer: !process.env.CI,
  },
});
