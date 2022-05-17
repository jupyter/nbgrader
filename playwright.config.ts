/**
 * Configuration for Playwright using default from @jupyterlab/galata
 */

import type { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  testDir: './nbgrader/tests/labextension_ui-tests',
  testMatch: '**/*.spec.ts',
  testIgnore: '**/node_modules/**/*',
  timeout: 30000,
  reporter: [[process.env.CI ? 'dot' : 'list'], ['html']],
  workers: 1,
  use: {
  // Browser options
  // headless: false,
  // slowMo: 500,
  // Context options
  viewport: { width: 1024, height: 768 },
  // Artifacts
  video: 'retain-on-failure'
  },

  webServer: {
    command: 'jlpm start:test',
    url: 'http://localhost:8888/lab',
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  },

};

export default config;

