import { test as base } from '@jupyterlab/galata';
import { Page } from '@playwright/test';

export const test = base.extend({
  waitForApplication: async ({ baseURL }, use, testInfo) => {
    const waitIsReady = async (page: Page): Promise<void> => {
      await page.locator('#main-panel').waitFor();
    };
    await use(waitIsReady);
  }
});
