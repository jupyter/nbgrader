import { test, galata, IJupyterLabPageFixture} from '@jupyterlab/galata';
import { expect } from '@playwright/test';
import { create_env } from './test_utils';

import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';


test.use({ tmpPath: 'nbgrader-course-list-test' });

var exchange_dir:string;
var cache_dir: string;

/*
 * Create environment
 */
test.beforeEach(async ({ baseURL, tmpPath }) => {

  const contents = galata.newContentsHelper(baseURL);

  await contents.createDirectory(tmpPath);

  exchange_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_exchange_test_'));
  cache_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_cache_test_'));
});

/*
 * delete temp directories at the end of test
 */
test.afterEach(async ({ baseURL, tmpPath }) => {
  const contents = galata.newContentsHelper(baseURL);
  await contents.deleteDirectory(tmpPath);
  fs.rmSync(exchange_dir, { recursive: true, force: true });
  fs.rmSync(cache_dir, { recursive: true, force: true });
});

/*
 * Open a courses list tab
 */
const open_courses_list = async (page:IJupyterLabPageFixture) => {

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(1);

  await page.keyboard.press('Control+Shift+c');
  await page.locator('#modal-command-palette li[data-command="nbgrader:course-list"]').click();

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(2);

  var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab");
  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel.p-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Courses");
  await page.waitForSelector("#formgrader_list");
}

/*
 * Modify config file
 */
const update_config = async (page:IJupyterLabPageFixture, baseURL:string, tmpPath:string) => {

  const contents = galata.newContentsHelper(baseURL);

  const jupyter_config_content = await page.locator('#jupyter-config-data').textContent();
  const rootDir = JSON.parse(jupyter_config_content)['serverRoot'];

  var text_to_append = `
c.Exchange.assignment_dir = "${path.resolve(rootDir, tmpPath)}"
c.CourseDirectory.root = "${path.resolve(rootDir, tmpPath)}"
c.CourseDirectory.course_id = "course101"
`

  fs.appendFileSync(path.resolve(rootDir, "nbgrader_config.py"), text_to_append);
}

/*
 * TODO: package the 4 extensions individually to be able to install/enable/disable each.
*/
// test('No formgrader', async ({
//   page
//   }) => {

//     await open_courses_list(page);

//   }
// );


/*
 * Test a local formgrader, expecting existing courses are local and opening formgrader works
 */
test('local formgrader', async ({
  page,
  baseURL,
  tmpPath
  }) => {
    await create_env(page, tmpPath, exchange_dir, cache_dir);

    await update_config(page, baseURL, tmpPath);

    await open_courses_list(page);
    await expect(page.locator("#formgrader_list_loading")).not.toBeVisible();
    await expect(page.locator("#formgrader_list_placeholder")).not.toBeVisible();
    await expect(page.locator("#formgrader_list_error")).not.toBeVisible();
    await expect(page.locator("#formgrader_list > .list_item")).toHaveCount(1);

    await expect(page.locator("#formgrader_list > .list_item")).toHaveText("course101local");

    await expect(page.locator("#formgrader_list > .list_item a")).toHaveCount(1);

    await page.locator("#formgrader_list > .list_item a").click();
    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(3);

    var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab");
    var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel.p-TabBar-tabLabel");
    await expect(newTab_label).toHaveText("Formgrader");

  }
);


/*
 * Test using JupyterHub authenticator without jupyterHub, expecting same results as previous tests
 */
test('No jupyterhub', async ({
  page,
  baseURL,
  tmpPath
  }) => {

    await create_env(page, tmpPath, exchange_dir, cache_dir);

    await update_config(page, baseURL, tmpPath);

    var text_to_append = `
from nbgrader.auth import JupyterHubAuthPlugin
c.Authenticator.plugin_class = JupyterHubAuthPlugin
    `;

    fs.appendFileSync("../nbgrader_config.py", text_to_append);

    await open_courses_list(page);
    await expect(page.locator("#formgrader_list_loading")).not.toBeVisible();
    await expect(page.locator("#formgrader_list_placeholder")).not.toBeVisible();
    await expect(page.locator("#formgrader_list_error")).not.toBeVisible();
    await expect(page.locator("#formgrader_list > .list_item")).toHaveCount(1);

    await expect(page.locator("#formgrader_list > .list_item")).toHaveText("course101local");

    await expect(page.locator("#formgrader_list > .list_item a")).toHaveCount(1);

    await page.locator("#formgrader_list > .list_item a").click();
    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(3);

    var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab");
    var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel.p-TabBar-tabLabel");
    await expect(newTab_label).toHaveText("Formgrader");

  }
);
