/**
 * Configuration for Playwright using default from @jupyterlab/galata
 */

import type { PlaywrightTestConfig } from '@playwright/test';
import baseConfig from '@jupyterlab/galata/lib/playwright-config';
import { GalataOptions } from '@jupyterlab/galata';

const config: PlaywrightTestConfig<GalataOptions> = {
  ...baseConfig,
  testDir: './nbgrader/tests/ui-tests',
  testMatch: '**/*.spec.ts',
  testIgnore: '**/node_modules/**/*',
  timeout: 60000,
  reporter: [[process.env.CI ? 'dot' : 'list'], ['html', { outputFolder: 'playwright-tests' }]],
  workers: 1,
  use: {
    appPath: '',
    // Context options
    viewport: { width: 1024, height: 768 },
    // Artifacts
    video: 'retain-on-failure'
  },

  webServer: {
    command: 'jlpm start:test:notebook',
    url: 'http://localhost:8888/tree',
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  },

};

export default config;
