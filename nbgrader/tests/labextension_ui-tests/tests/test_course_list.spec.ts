import { test, galata, IJupyterLabPageFixture} from '@jupyterlab/galata';
import { expect } from '@playwright/test';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as process from "process";

import { execute_command } from './test_utils';

test.use({ tmpPath: 'nbgrader-course-list-test' });

var exchange_dir:string;
var cache_dir: string;

/*
 * Create environment
 */
test.beforeEach(async ({ baseURL, tmpPath }) => {

  const contents = galata.newContentsHelper(baseURL);

  await contents.createDirectory(tmpPath);

});

/*
 * delete temp directories at the end of test
 */
test.afterAll(async ({ baseURL, tmpPath }) => {
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

const create_env = async (page:IJupyterLabPageFixture) => {

  var content = await page.locator('#jupyter-config-data').textContent();
  const rootDir = JSON.parse(content)['serverRoot'];

  /* Add config_file to jupyter root directory, and change to that directory.
  TODO : test on windows, the config file may change (see nbextension test)
  */
  try {
    exchange_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_exchange_test_'));
    cache_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_cache_test_'));
    fs.copyFileSync(path.resolve(__dirname, `../files/nbgrader_config.py`),
                    path.resolve(rootDir, "nbgrader_config.py"));

    var text_to_append = `
c.Exchange.root = "${exchange_dir}"
c.Exchange.cache = "${cache_dir}"
c.CourseDirectory.course_id = "course101"
    `;

    fs.appendFileSync(path.resolve(rootDir, "nbgrader_config.py"), text_to_append);
    process.chdir(path.resolve(rootDir));
  }
  catch (e){
    throw new Error(`ERROR : ${e}`);
  }

  /* Fill database */
  await execute_command("nbgrader db assignment add 'Problem Set 1'");
  await execute_command("nbgrader db assignment add ps.01");
  await execute_command("nbgrader db student add Bitdiddle --first-name Ben --last-name B");
  await execute_command("nbgrader db student add Hacker --first-name Alyssa --last-name H");
  await execute_command("nbgrader db student add Reasoner --first-name Louis --last-name R");
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
  tmpPath
  }) => {

    await create_env(page);
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
  tmpPath
  }) => {

    await create_env(page);

    var text_to_append = `
from nbgrader.auth import JupyterHubAuthPlugin
c.Authenticator.plugin_class = JupyterHubAuthPlugin
    `;

    fs.appendFileSync("nbgrader_config.py", text_to_append);

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
