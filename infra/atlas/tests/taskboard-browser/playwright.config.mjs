import { defineConfig, devices } from "@playwright/test";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const testRoot = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(testRoot, "../../ansible/roles/atlas_homeserver/files/taskboard");
const liveBaseUrl = process.env.TASKBOARD_BASE_URL;

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  reporter: "line",
  use: {
    baseURL: liveBaseUrl || "http://127.0.0.1:43917",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: liveBaseUrl ? undefined : {
    command: "python3 taskboard.py",
    cwd: appRoot,
    env: {
      TASKBOARD_ALLOW_NO_AUTH: "1",
      TASKBOARD_HOST: "127.0.0.1",
      TASKBOARD_PORT: "43917",
    },
    port: 43917,
    reuseExistingServer: false,
  },
});
