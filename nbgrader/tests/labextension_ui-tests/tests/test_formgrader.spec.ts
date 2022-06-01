import { test, galata } from '@jupyterlab/galata';
import { expect } from '@playwright/test';
import * as os from 'os';

const is_windows = os.platform().startsWith('win')

test('Formgrader command', async ({
    page
  }) => {

    console.log(`######### PLATFORM : ${os.platform()}`)

    test.skip(is_windows, 'This feature is not implemented for Windows');

    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(1);

    await page.keyboard.press('Control+Shift+c');
    await page.locator('#modal-command-palette li[data-command="nbgrader:formgrader"]').click();

    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(2);

    var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab");
    var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel.p-TabBar-tabLabel");
    await expect(newTab_label).toHaveText("Formgrader");

  }
);
