import { test, galata, IJupyterLabPageFixture} from '@jupyterlab/galata';
import { expect } from '@playwright/test';
import { create_env } from './test_utils';

import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

test.use({
  tmpPath: 'nbgrader-course-list-test',
  mockSettings: {
    '@jupyterlab/apputils-extension:notification': {
      fetchNews: 'false'
    }
  }
});

var exchange_dir:string;
var cache_dir: string;

const is_windows = os.platform().startsWith('win')

/*
 * Create environment
 */
test.beforeEach(async ({ request, tmpPath }) => {
  if (request === undefined) throw new Error("Request is undefined.");
  const contents = galata.newContentsHelper(request);

  await contents.createDirectory(tmpPath);

  if (!is_windows){
    exchange_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_exchange_test_'));
    cache_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_cache_test_'));
  }
});

/*
 * delete temp directories at the end of test
 */
test.afterEach(async ({ request, tmpPath }) => {
  if (request === undefined) throw new Error("Request is undefined.");
  const contents = galata.newContentsHelper(request);
  await contents.deleteDirectory(tmpPath);

  if (!is_windows){
    fs.rmSync(exchange_dir, { recursive: true, force: true });
    fs.rmSync(cache_dir, { recursive: true, force: true });
  }

  if (await contents.fileExists("nbgrader_config.py")) contents.deleteFile("nbgrader_config.py");
  contents.uploadFile(path.resolve(__dirname, "../files/nbgrader_config.py"), "nbgrader_config.py");
});

/*
 * Open a courses list tab
 */
const open_courses_list = async (page:IJupyterLabPageFixture) => {

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab")).toHaveCount(1);

  await page.keyboard.press('Control+Shift+c');
  await page.locator('#modal-command-palette li[data-command="nbgrader:open-course-list"]').click();

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab")).toHaveCount(2);

  var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab");
  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Courses");
  await page.waitForSelector("#formgrader_list");
}

/*
 * Modify config file
 */
const update_config = async (page:IJupyterLabPageFixture, rootDir:string) => {

  var text_to_append = `
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

//     test.skip(is_windows, 'This feature is not implemented for Windows');
//     await open_courses_list(page);

//   }
// );

/*
 * Test opening course list tab from menu
 */
test('Open course list tab from menu', async({
  page
  }) => {

    const nbgrader_menu = page.locator('#jp-menu-panel div.lm-MenuBar-itemLabel:text("Nbgrader")');
    const courseList_menu = page.locator('#jp-mainmenu-nbgrader-menu li[data-command="nbgrader:open-course-list"]');
    const tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab");
    const lastTab_label = tabs.last().locator(".lm-TabBar-tabLabel");

    await expect(tabs).toHaveCount(1);

    // Check main menu exists
    await expect(nbgrader_menu).toHaveCount(1);

    // Open course list from the menu
    await nbgrader_menu.click();
    await courseList_menu.click();

    await expect(tabs).toHaveCount(2);
    await expect(lastTab_label).toHaveText("Courses");

    // Close the last tab
    await tabs.last().locator(".jp-icon-hover.lm-TabBar-tabCloseIcon").click();
    await expect(tabs).toHaveCount(1);

    // Open again
    await nbgrader_menu.click();
    await courseList_menu.click();

    await expect(tabs).toHaveCount(2);
    await expect(lastTab_label).toHaveText("Courses");

});

/*
 * Test a local formgrader, expecting existing courses are local and opening formgrader works
 */
test('local formgrader', async ({
  page,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    const rootDir = await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);

    await update_config(page, rootDir);

    await open_courses_list(page);
    await expect(page.locator("#formgrader_list_loading")).not.toBeVisible();
    await expect(page.locator("#formgrader_list_placeholder")).not.toBeVisible();
    await expect(page.locator("#formgrader_list_error")).not.toBeVisible();
    await expect(page.locator("#formgrader_list > .list_item")).toHaveCount(1);

    await expect(page.locator("#formgrader_list > .list_item")).toHaveText("course101local");

    await expect(page.locator("#formgrader_list > .list_item a")).toHaveCount(1);

    await page.locator("#formgrader_list > .list_item a").click();
    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab")).toHaveCount(3);

    var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab");
    var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel");
    await expect(newTab_label).toHaveText("Formgrader");

  }
);


// /*
//  * Test using JupyterHub authenticator without jupyterHub, expecting same results as previous tests
//  */
// test('No jupyterhub', async ({
//   page,
//   baseURL,
//   tmpPath,

//   }) => {

//     test.skip(is_windows, 'This feature is not implemented for Windows');

//     const rootDir = await create_env(page, tmpPath, exchange_dir, cache_dir);

//     await update_config(page, rootDir);

//     var text_to_append = `
// from nbgrader.auth import JupyterHubAuthPlugin
// c.Authenticator.plugin_class = JupyterHubAuthPlugin
//     `;

//     fs.appendFileSync(path.resolve(rootDir, "nbgrader_config.py"), text_to_append);

//     await open_courses_list(page);
//     await expect(page.locator("#formgrader_list_loading")).not.toBeVisible();
//     await expect(page.locator("#formgrader_list_placeholder")).not.toBeVisible();
//     await expect(page.locator("#formgrader_list_error")).not.toBeVisible();
//     await expect(page.locator("#formgrader_list > .list_item")).toHaveCount(1);

//     await expect(page.locator("#formgrader_list > .list_item")).toHaveText("course101local");

//     await expect(page.locator("#formgrader_list > .list_item a")).toHaveCount(1);

//     await page.locator("#formgrader_list > .list_item a").click();
//     await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab")).toHaveCount(3);

//     var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab");
//     var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel");
//     await expect(newTab_label).toHaveText("Formgrader");

//   }
// );
