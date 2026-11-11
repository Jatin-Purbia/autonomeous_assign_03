const { defineConfig, devices } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 90000,
  expect: { timeout: 10000 },
  fullyParallel: false,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never' }],
    ['json', { outputFile: 'test-results/e2e-results.json' }],
  ],
  use: {
    baseURL: 'http://127.0.0.1:8137',
    headless: true,
    launchOptions: process.env.E2E_BROWSER_PATH
      ? { executablePath: process.env.E2E_BROWSER_PATH }
      : {},
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    // The separate demo recorder captures video; traces/screenshots cover failures.
    // Avoid a video encoder for each test on constrained student laptops.
    video: 'off',
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1080 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } },
  ],
  webServer: {
    command: 'python server.py --port 8137',
    cwd: '..',
    url: 'http://127.0.0.1:8137/api/health',
    reuseExistingServer: false,
    timeout: 30000,
  },
});
