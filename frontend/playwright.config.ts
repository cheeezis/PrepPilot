import { defineConfig } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendDirectory = fileURLToPath(new URL('.', import.meta.url))
const backendDirectory = fileURLToPath(new URL('../backend/', import.meta.url))
const backendPython = path.join(
  backendDirectory,
  '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
)
const backendPort = process.env.PREPPILOT_E2E_BACKEND_PORT ?? '8000'
const frontendPort = process.env.PREPPILOT_E2E_FRONTEND_PORT ?? '5173'

export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.e2e.ts',
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
  webServer: [
    {
      name: 'Backend',
      command: `"${backendPython}" -m uvicorn preppilot_api.main:app --port ${backendPort}`,
      cwd: backendDirectory,
      url: `http://127.0.0.1:${backendPort}/docs`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
    {
      name: 'Frontend',
      command: 'npm run dev -- --host 127.0.0.1',
      cwd: frontendDirectory,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
})
