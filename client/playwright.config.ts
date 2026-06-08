import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright config for the planilha-notas-alunos project.
 *
 * Story 8.6: full-stack cutover verification — boots Vite (5173) and FastAPI
 * (8000) together via `npm run dev`, then runs the cutover E2E suite.
 *
 * Notes:
 * - We rely on the unified dev script (Story 8.3) which uses `concurrently`
 *   to start backend and client in one process.
 * - The dev server is reused when the suite is run multiple times in a row
 *   (`reuseExistingServer: true`) to avoid 30s+ cold boots.
 * - Only chromium is configured for Story 8.6; the matrix can expand later.
 */
export default defineConfig({
  testDir: 'tests/e2e',
  // E2E cuts across the full stack; allow generous timeouts.
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run dev --prefix ..',
    cwd: '..',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
})
