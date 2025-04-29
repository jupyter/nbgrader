import { test as jupyterLabTest, galata, IJupyterLabPageFixture, expect } from "@jupyterlab/galata";

import * as fs from "fs";
import * as os from "os";
import * as path from "path";

import { test as notebookTest } from './utils/notebook_fixtures';
import { createEnv } from "./utils/test_utils";

const testDir = process.env.NBGRADER_TEST_DIR || '';
if (!testDir){
  throw new Error('Test directory not provided');
}
if (!fs.existsSync(testDir)){
  throw new Error(`Test directory ${testDir} doesn't exists`);
}

const isWindows = os.platform().startsWith('win');

const tempPath = 'nbgrader-course-list-test';

let test = jupyterLabTest;
let mainPanelId = '#jp-main-dock-panel';
let menuPanelId = '#jp-menu-panel';
let mainPanelTabCount = 1;

const baseTestUse = {
  tmpPath: tempPath,
  mockSettings: {
    '@jupyterlab/apputils-extension:notification': {
      fetchNews: 'false'
    }
  }
}

const isNotebook = process.env.NBGRADER_TEST_IS_NOTEBOOK;
if (isNotebook) {
  test = notebookTest;
  test.use({
    ...baseTestUse,
    autoGoto: false
  });
  mainPanelId = '#main-panel';
  menuPanelId = '#menu-panel';
  mainPanelTabCount = 2;
}
else {
  test.use(baseTestUse);
}

var exchange_dir: string;
var cache_dir: string;

/*
 * Create environment
 */
test.beforeEach(async ({ request, tmpPath }) => {
  if (request === undefined) throw new Error("Request is undefined.");
  const contents = galata.newContentsHelper(request);

  await contents.createDirectory(tmpPath);

  if (await contents.fileExists("nbgrader_config.py")){
    await contents.deleteFile("nbgrader_config.py");
  }
  await contents.uploadFile(
    path.resolve(__dirname, "./files/nbgrader_config.py"),
    "nbgrader_config.py"
  );

  if (!isWindows) {
    exchange_dir = fs.mkdtempSync(
      path.join(os.tmpdir(), "nbgrader_exchange_test_")
    );
    cache_dir = fs.mkdtempSync(path.join(os.tmpdir(), "nbgrader_cache_test_"));
  }
});

/*
 * delete temp directories at the end of test
 */
test.afterEach(async ({ request, page, tmpPath }) => {
  if (request === undefined) throw new Error("Request is undefined.");
  const contents = galata.newContentsHelper(request, page);
  await contents.deleteDirectory(tmpPath);

  if (!isWindows) {
    fs.rmSync(exchange_dir, { recursive: true, force: true });
    fs.rmSync(cache_dir, { recursive: true, force: true });
  }
});

/*
 * Open a courses list tab
 */
const openCoursesList = async (page: IJupyterLabPageFixture) => {
  await expect(page.locator(`${mainPanelId} .lm-TabBar-tab`)).toHaveCount(
    mainPanelTabCount
  );

  await page.keyboard.press("ControlOrMeta+Shift+c");
  await page
    .locator(
      '#modal-command-palette li[data-command="nbgrader:open-course-list"]'
    )
    .click();

  var tabs = page.locator(`${mainPanelId} .lm-TabBar-tab`);
  await expect(tabs).toHaveCount(
    mainPanelTabCount + 1
  );

  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Courses");
  await page.locator("#formgrader_list").waitFor();
};

/*
 * Modify config file
 */
const updateConfig = async () => {
  var text_to_append = `
c.CourseDirectory.course_id = "course101"
`;
  fs.appendFileSync(
    path.resolve(testDir, "nbgrader_config.py"),
    text_to_append
  );
};

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
test("Open course list tab from menu", async ({ page, tmpPath }) => {
  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  const nbgrader_menu = page.locator(`${menuPanelId} div.lm-MenuBar-itemLabel:text("Nbgrader")`);
  const courseList_menu = page.locator(
    '#jp-mainmenu-nbgrader li[data-command="nbgrader:open-course-list"]'
  );
  const tabs = page.locator(`${mainPanelId} .lm-TabBar-tab`);
  const lastTab_label = tabs.last().locator('.lm-TabBar-tabLabel');


  await expect(tabs).toHaveCount(mainPanelTabCount);

  // Check main menu exists
  await expect(nbgrader_menu).toHaveCount(1);

  // Open course list from the menu
  await nbgrader_menu.click();
  await courseList_menu.click();

  await expect(tabs).toHaveCount(mainPanelTabCount + 1);
  await expect(lastTab_label).toHaveText('Courses');

  // Close the last tab
  await tabs.last().locator('.jp-icon-hover.lm-TabBar-tabCloseIcon').click();
  await expect(tabs).toHaveCount(mainPanelTabCount);

  // Open again
  await nbgrader_menu.click();
  await courseList_menu.click();

  await expect(tabs).toHaveCount(mainPanelTabCount + 1);
  await expect(lastTab_label).toHaveText('Courses');
});

/*
 * Test a local formgrader, expecting existing courses are local and opening formgrader works
 */
test("local formgrader", async ({ page, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);

  await updateConfig();

  await openCoursesList(page);
  await expect(page.locator("#formgrader_list_loading")).not.toBeVisible();
  await expect(page.locator("#formgrader_list_placeholder")).not.toBeVisible();
  await expect(page.locator("#formgrader_list_error")).not.toBeVisible();
  await expect(page.locator("#formgrader_list > .list_item")).toHaveCount(1);

  await expect(page.locator("#formgrader_list > .list_item")).toHaveText(
    "course101local"
  );

  await expect(page.locator("#formgrader_list > .list_item a")).toHaveCount(1);

  await page.locator("#formgrader_list > .list_item a").click();

  var tabs = page.locator(`${mainPanelId} .lm-TabBar-tab`);
  await expect(tabs).toHaveCount(
    mainPanelTabCount + 2
  );

  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Formgrader");
});

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
