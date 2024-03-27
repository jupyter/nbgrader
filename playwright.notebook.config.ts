/**
 * Configuration for Playwright using default from @jupyterlab/galata
 */

import baseConfig from '@jupyterlab/galata/lib/playwright-config';

module.exports = {
  ...baseConfig,
  testDir: './nbgrader/tests/ui-tests',
  workers: 1,
  use: {
    ...baseConfig.use,
    appPath: '',
  },
  webServer: {
    command: 'jlpm start:test',
    url: 'http://localhost:8888/tree',
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  }
};
