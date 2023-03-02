/**
 * Configuration for Playwright using default from @jupyterlab/galata
 */

var baseConfig = require('@jupyterlab/galata/lib/playwright-config');

module.exports = {
  ...baseConfig,
  testDir: './nbgrader/tests/ui-tests',
  workers: 1,
  webServer: {
    command: 'jlpm start:test',
    url: 'http://localhost:8888/lab',
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  },

};
