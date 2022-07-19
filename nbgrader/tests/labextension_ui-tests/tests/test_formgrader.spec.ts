import { test, galata, IJupyterLabPageFixture } from '@jupyterlab/galata';
import { expect, Frame } from '@playwright/test';

import {
  execute_command,
  create_env
} from './test_utils';

// import * as sqlite3 from 'sqlite3';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

const is_windows = os.platform().startsWith('win')

test.use({
  tmpPath: 'nbgrader-formgrader-test',
  mockSettings: {
    '@jupyterlab/apputils-extension:notification': {
      fetchNews: 'false'
    }
  }
});

// const db = new sqlite3.Database("gradebook.db");

var exchange_dir:string;
var cache_dir: string;

/*
 * Create environment
 */
test.beforeEach(async ({ baseURL, tmpPath }) => {

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  const contents = galata.newContentsHelper(baseURL);

  await contents.createDirectory(tmpPath);

  if (!is_windows){
    exchange_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_exchange_test_'));
    cache_dir = fs.mkdtempSync(path.join(os.tmpdir(), 'nbgrader_cache_test_'));
  }
});

/*
 * delete temp directories at the end of test
 */
test.afterEach(async ({ baseURL, tmpPath }) => {
  if (!is_windows){
    fs.rmSync(exchange_dir, { recursive: true, force: true });
    fs.rmSync(cache_dir, { recursive: true, force: true });
  }

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  const contents = galata.newContentsHelper(baseURL);
  await contents.deleteDirectory(tmpPath);

  if (await contents.fileExists("nbgrader_config.py")) contents.deleteFile("nbgrader_config.py");
  contents.uploadFile(path.resolve(__dirname, "../files/nbgrader_config.py"), "nbgrader_config.py");
});

/*
 * Create a nbgrader file system
 */
const add_courses = async (page:IJupyterLabPageFixture, baseURL:string, tmpPath:string) => {

  const contents = galata.newContentsHelper(baseURL);

  // copy files from the user guide
  const source_path = path.resolve(__dirname, "..", "..", "..", "docs", "source", "user_guide", "source");
  const submitted_path = path.resolve(__dirname, "..", "..", "..", "docs", "source", "user_guide", "submitted");

  await contents.uploadDirectory(source_path, `${tmpPath}/source`);

  const students = ["bitdiddle", "hacker"];
  for (var i=0; i<2; i++){
    await contents.uploadDirectory(
      path.resolve(submitted_path, students[i]),
      `${tmpPath}/submitted/${students[i]}`
    )
  }

  // Rename the files and directory to have spaces in names
  await contents.renameDirectory(`${tmpPath}/source/ps1`, `${tmpPath}/source/Problem Set 1`);
  await contents.renameFile(`${tmpPath}/source/Problem Set 1/problem1.ipynb`, `${tmpPath}/source/Problem Set 1/Problem 1.ipynb`);
  await contents.renameFile(`${tmpPath}/source/Problem Set 1/problem2.ipynb`, `${tmpPath}/source/Problem Set 1/Problem 2.ipynb`);
  await contents.renameDirectory(`${tmpPath}/submitted/bitdiddle`, `${tmpPath}/submitted/Bitdiddle`);
  await contents.renameDirectory(`${tmpPath}/submitted/Bitdiddle/ps1`, `${tmpPath}/submitted/Bitdiddle/Problem Set 1`);
  await contents.renameFile(`${tmpPath}/submitted/Bitdiddle/Problem Set 1/problem1.ipynb`, `${tmpPath}/submitted/Bitdiddle/Problem Set 1/Problem 1.ipynb`);
  await contents.renameFile(`${tmpPath}/submitted/Bitdiddle/Problem Set 1/problem2.ipynb`, `${tmpPath}/submitted/Bitdiddle/Problem Set 1/Problem 2.ipynb`);
  await contents.renameDirectory(`${tmpPath}/submitted/hacker`, `${tmpPath}/submitted/Hacker`);
  await contents.renameDirectory(`${tmpPath}/submitted/Hacker/ps1`, `${tmpPath}/submitted/Hacker/Problem Set 1`);
  await contents.renameFile(`${tmpPath}/submitted/Hacker/Problem Set 1/problem1.ipynb`, `${tmpPath}/submitted/Hacker/Problem Set 1/Problem 1.ipynb`);
  await contents.renameFile(`${tmpPath}/submitted/Hacker/Problem Set 1/problem2.ipynb`, `${tmpPath}/submitted/Hacker/Problem Set 1/Problem 2.ipynb`);

  const jupyter_config_content = await page.locator('#jupyter-config-data').textContent();
  if (jupyter_config_content === null) throw new Error("Cannot get the server root directory.");
  const rootDir = JSON.parse(jupyter_config_content)['serverRoot'];

  fs.copyFileSync(path.resolve(rootDir, "nbgrader_config.py"), path.resolve(rootDir, tmpPath, "nbgrader_config.py"));

  // generate some assignments
  await execute_command(`nbgrader generate_assignment 'Problem Set 1' --IncludeHeaderFooter.header=${path.resolve(rootDir, tmpPath, "source", "header.ipynb")}`);

  // autograde assignment
  await execute_command("nbgrader autograde 'Problem Set 1'");

}

/*
 * Open the formgrader tab
 */
const open_formgrader = async (page:IJupyterLabPageFixture) => {

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(1);

  await page.keyboard.press('Control+Shift+c');
  await page.locator('#modal-command-palette li[data-command="nbgrader:open-formgrader"]').click();

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(2);

  var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab");
  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel.p-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Formgrader");

}

/*
 * Check jupyter lab file browser breadcrumbs
 */
const check_jl_breadcrumbs = async (page:IJupyterLabPageFixture, breadcrumbs:string) => {
  await page.waitForSelector(`.jp-FileBrowser-crumbs > span.jp-BreadCrumbs-item[title="${breadcrumbs}"]`);
}

/*
 * Check formgrader breadcrumbs
 */
const check_formgrader_breadcrumbs = async (iframe:Frame, breadcrumbs:string[]) => {

  await expect(iframe.locator(".breadcrumb li")).toHaveCount(breadcrumbs.length);

  const elements = iframe.locator(".breadcrumb li");
  const array: string[] = [];
  for (var i=0; i<await elements.count(); i++){
    array.push(await elements.nth(i).textContent() as string);
  }
  expect(array.sort()).toEqual(breadcrumbs.sort());
}

/*
 * Check formgrader breadcrumbs
 */
const check_formgrade_view_breadcrumbs = async (
  iframe:Frame,
  breadcrumbs:string[],
  no_submission_count?: boolean
  ) => {

  await expect(iframe.locator(".breadcrumb li a:visible")).toHaveCount(breadcrumbs.length);

  const elements = iframe.locator(".breadcrumb li a:visible");
  const in_page_breadcrumbs: string[] = [];
  for (var i=0; i<await elements.count(); i++){
    in_page_breadcrumbs.push((await elements.nth(i).textContent() as string).trim());
  }

  if (no_submission_count) {
    expect(in_page_breadcrumbs.slice(0, -1).sort()).toEqual(breadcrumbs.slice(0, -1).sort());
    expect(in_page_breadcrumbs[in_page_breadcrumbs.length - 1].includes(breadcrumbs[-1]));
  }
  else expect(in_page_breadcrumbs.sort()).toEqual(breadcrumbs.sort());
}

/*
 * Click on link by text
 */
const click_link = async (iframe:Frame, text:string) => {
  await iframe.click(`a:text-is('${text}')`);
}

// /*
//  * Get comment box
//  */
// const get_comment_box = async (iframe:Frame, index:number) => {
//   await expect(await iframe.locator('.comment').count()).toBeGreaterThanOrEqual(index);
//   await expect poll(() => iframe.locator('.comment').count()).toBeGreaterThan(3);
// }


/*
 * Test opening formgrader tab from menu
 */
test('Open formgrader tab from menu', async({
  page
  }) => {

    const nbgrader_menu = page.locator('#jp-menu-panel div.lm-MenuBar-itemLabel.p-MenuBar-itemLabel:text("Nbgrader")');
    const formgrader_menu = page.locator('#jp-mainmenu-nbgrader-menu li[data-command="nbgrader:open-formgrader"]');
    const tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab");
    const lastTab_label = tabs.last().locator(".lm-TabBar-tabLabel.p-TabBar-tabLabel");

    await expect(tabs).toHaveCount(1);

    // Check main menu exists
    await expect(nbgrader_menu).toHaveCount(1);

    // Open course list from the menu
    await nbgrader_menu.click();    
    await formgrader_menu.click();

    await expect(tabs).toHaveCount(2);        
    await expect(lastTab_label).toHaveText("Formgrader");

    // Close the last tab
    await tabs.last().locator(".jp-icon-hover.lm-TabBar-tabCloseIcon").click();
    await expect(tabs).toHaveCount(1);

    // Open again
    await nbgrader_menu.click();
    await formgrader_menu.click();

    await expect(tabs).toHaveCount(2);
    await expect(lastTab_label).toHaveText("Formgrader");

});

/*
 * Load manage assignments
 */
test('Load manage assignments', async ({
    page,
    baseURL,
    tmpPath
  }) => {

    test.skip(is_windows, 'This test does not work on Windows');

    if (baseURL === undefined) throw new Error("BaseURL is undefined.");

    // create environment
    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_formgrader(page);

    // get formgrader iframe and check for breadcrumbs
    const iframe = page.mainFrame().childFrames()[0];

    await check_formgrader_breadcrumbs(iframe, ["Assignments"]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader`));

    await page.waitForSelector(`.jp-FileBrowser-crumbs > span.jp-BreadCrumbs-item[title="${tmpPath}"]`);

    // click on the "Problem Set 1" link and check if file browser has changed of directory
    click_link(iframe, "Problem Set 1");
    await page.waitForSelector(`.jp-FileBrowser-crumbs > span.jp-BreadCrumbs-item[title="${tmpPath.concat("/source/Problem Set 1")}"]`);

    // click on preview link and check if file browser has changed of directory
    iframe.locator("td.preview .glyphicon").click();
    await page.waitForSelector(`.jp-FileBrowser-crumbs > span.jp-BreadCrumbs-item[title="${tmpPath.concat("/release/Problem Set 1")}"]`);

    // click on the first number of submissions and check that iframe has change URL
    await iframe.click("td.num-submissions a");
    await check_formgrader_breadcrumbs(iframe, ["Assignments", "Problem Set 1"]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/manage_submissions/Problem Set 1`));
  }
);

/*
 * Load manage submissions
 */
test('Load manage submissions', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to manage_submissions
  await iframe.goto(`${baseURL}/formgrader/manage_submissions/Problem Set 1`);

  // await iframe.click("td.num-submissions a");
  await check_formgrader_breadcrumbs(iframe, ["Assignments", "Problem Set 1"]);

  // clicking on breadcrumbs should go back to manage_assignments
  await click_link(iframe, "Assignments");
  await check_formgrader_breadcrumbs(iframe, ["Assignments"]);
  expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/manage_assignments`));

  // page.goBack(); // seems endless
  await iframe.goto(`${baseURL}/formgrader/manage_submissions/Problem Set 1`);
  await check_formgrader_breadcrumbs(iframe, ["Assignments", "Problem Set 1"]);

  // Check students links
  await expect(iframe.locator("td.student-name")).toHaveCount(2);
  for (var i=0; i<await iframe.locator("td.student-name").count(); i++){
    var student_name = await iframe.locator("td.student-name").nth(i).getAttribute("data-order") as string;
    var student_id = await iframe.locator("td.student-id").nth(i).getAttribute("data-order") as string;
    await click_link(iframe, student_name);
    await check_formgrader_breadcrumbs(iframe, ["Students", student_id, "Problem Set 1"]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/manage_students/${student_id}/Problem Set 1`));
    await iframe.goto(`${baseURL}/formgrader/manage_submissions/Problem Set 1`);
  }
});

/*
 * Load gradebook1
 */
test('Load gradebook1', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook
  await iframe.goto(`${baseURL}/formgrader/gradebook`);

  // await iframe.click("td.num-submissions a");
  await check_formgrader_breadcrumbs(iframe, ["Manual Grading"]);

  // click on assignment
  await click_link(iframe, "Problem Set 1");
  await check_formgrader_breadcrumbs(iframe, ["Manual Grading", "Problem Set 1"]);
  expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/gradebook/Problem Set 1`));

  // test that the task column is present
  await expect(iframe.locator('th:text-is("Avg. Task Score")')).toHaveCount(1);

});

/*
 * Load gradebook2
 */
test('Load gradebook2', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);
  await check_formgrader_breadcrumbs(iframe, ["Manual Grading", "Problem Set 1"]);

  // clicking on breadcrumbs should go back to manual grading
  await iframe.click('ol.breadcrumb a:text-is("Manual Grading")');
  await check_formgrader_breadcrumbs(iframe, ["Manual Grading"]);
  expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/gradebook`));

  // Send back iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);

  // test problems links
  await expect(iframe.locator("td.name")).toHaveCount(2);
  for (var i=0; i<await iframe.locator("td.name").count(); i++){
    var problem_name = await iframe.locator("td.name").nth(i).getAttribute("data-order") as string;
    await click_link(iframe, problem_name);
    await check_formgrader_breadcrumbs(iframe, ["Manual Grading", "Problem Set 1", problem_name]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`));
    await expect(iframe.locator('th:text-is("Task Score")')).toHaveCount(1);
    await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);
  }
});

/*
 * Load gradebook3
 */
test('Load gradebook3', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);

  // for each problem
  await expect(iframe.locator("td.name")).toHaveCount(2);
  for (var i=0; i<await iframe.locator("td.name").count(); i++){
    var problem_name = await iframe.locator("td.name").nth(i).getAttribute("data-order") as string;
    await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`);
    await check_formgrader_breadcrumbs(iframe, ["Manual Grading", "Problem Set 1", problem_name]);

    // test click on breadcrumb 'Manual Grading' to change iframe URL, then go back
    await iframe.click('ol.breadcrumb a:text-is("Manual Grading")');
    await check_formgrader_breadcrumbs(iframe, ["Manual Grading"]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/gradebook`));
    await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`);

    // test click on breadcrumb 'Problem Set 1' to change iframe URL, then go back
    await iframe.click('ol.breadcrumb a:text-is("Problem Set 1")');
    await check_formgrader_breadcrumbs(iframe, ["Manual Grading", "Problem Set 1"]);
    await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`);

    // test submissions links
    await expect(iframe.locator("td.name")).toHaveCount(2);
    for (var j=0; j<await iframe.locator("td.name").count(); j++){
      var submission_id = parseInt(await iframe.locator("td.name").nth(j).getAttribute("data-order") as string) + 1;
      await click_link(iframe, `Submission #${submission_id.toString()}`);
      await check_formgrade_view_breadcrumbs(
        iframe,
        ["Manual Grading",
         "Problem Set 1",
         problem_name,
         `Submission #${submission_id.toString()}`]
      );
      // TODO: find the submission ID to check URL ?

      if (problem_name == "Problem 1"){
        await expect(iframe.locator('span:text-is("Student\'s task")')).toHaveCount(1);
      }
      await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`);
    }
  }
});

/*
 * Gradebook3 show/hide students names
 */
test('Gradebook3 show hide names', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/Problem 1`);
  await check_formgrader_breadcrumbs(iframe, ["Manual Grading", "Problem Set 1", "Problem 1"]);

  const col2 = iframe.locator("td.name").first();
  const hidden = iframe.locator("td .glyphicon.name-hidden").first();
  const shown = iframe.locator("td .glyphicon.name-shown").first();

  // check shown and hidden elements
  await expect(col2).toHaveText(/Submission #[1-2]/, {useInnerText: true});
  await expect(hidden).toBeVisible();
  await expect(shown).toBeHidden();

  // show name
  await hidden.click();
  await expect(col2).toHaveText(/(H, Alyssa|B, Ben)/, {useInnerText: true});
  await expect(hidden).toBeHidden();
  await expect(shown).toBeVisible();

  // hide name again
  await shown.click();
  await expect(col2).toHaveText(/Submission #[1-2]/, {useInnerText: true});
  await expect(hidden).toBeVisible();
  await expect(shown).toBeHidden();

});

/*
  Toggle name visibility button
 */
test('Gradebook toggle names button', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/Problem 1`);
  await check_formgrader_breadcrumbs(iframe, ["Manual Grading", "Problem Set 1", "Problem 1"]);

  const button = iframe.locator("[id='toggle_names']").first()
  const hidden = iframe.locator("td .glyphicon.name-hidden").first();
  const shown = iframe.locator("td .glyphicon.name-shown").first();

  // At the start, all names are hidden
  await expect(button).toHaveText("Show All Names", {useInnerText: true});
  await expect(hidden).toBeVisible();
  await expect(shown).toBeHidden();

  // Clicking should make names shown
  await button.click();
  await expect(button).toHaveText("Hide All Names", {useInnerText: true});
  await expect(hidden).toBeHidden();
  await expect(shown).toBeVisible();

  // If there is at least one hidden, button should default to showing all names
  await shown.click();
  await expect(button).toHaveText("Show All Names", {useInnerText: true});
  await button.click();
  await expect(hidden).toBeHidden();
  await expect(shown).toBeVisible();

});

/*
 * Load students and test students links
 */
test('Load students', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to students
  await iframe.goto(`${baseURL}/formgrader/manage_students`);
  await check_formgrader_breadcrumbs(iframe, ["Students"]);

  // Check students links
  await expect(iframe.locator("td.name")).toHaveCount(3);
  for (var i=0; i < await iframe.locator("td.name").count(); i++){
    var student_name = await iframe.locator("td.name").nth(i).getAttribute("data-order") as string;
    var student_id = await iframe.locator("td.id").nth(i).getAttribute("data-order") as string;
    await click_link(iframe, student_name);
    await check_formgrader_breadcrumbs(iframe, ["Students", student_id]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/manage_students/${student_id}`));
    await expect(iframe.locator('th:text("Task Score")')).toHaveCount(1);
    await iframe.goto(`${baseURL}/formgrader/manage_students`);
  }

});

/*
 * Test students submissions
 */
test('Load students submissions', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  const student_ids = ["Bitdiddle", "Hacker"];

  for(var i=0; i<2; i++){ // foreach loop does not work (raise at goto statement)
    // Change iframe URL to student
    await iframe.goto(`${baseURL}/formgrader/manage_students/${student_ids[i]}`);
    await check_formgrader_breadcrumbs(iframe, ["Students", student_ids[i]]);

    // Click on an assignment
    await click_link(iframe, "Problem Set 1");
    // await iframe.waitForNavigation({'url': encodeURI(`${baseURL}/formgrader/manage_students/${student_ids[i]}/Problem Set 1`)});
    await check_formgrader_breadcrumbs(iframe, ["Students", student_ids[i], "Problem Set 1"]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/manage_students/${student_ids[i]}/Problem Set 1`));
    await expect(iframe.locator('th:text("Task Score")')).toHaveCount(1);
  }
});

/*
 * Switch views
 */
test('Switch views', async ({
  page,
  baseURL,
  tmpPath
}) => {

  test.skip(is_windows, 'This test does not work on Windows');

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  // create environment
  await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
  await add_courses(page, baseURL, tmpPath);
  await open_formgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  const pages = ["", "manage_assignments", "gradebook", "manage_students"];
  const links = [
    ["Manage Assignments", "Assignments", "manage_assignments"],
    ["Manual Grading", "Manual Grading", "gradebook"],
    ["Manage Students", "Students", "manage_students"]
  ];

  for (var i=0; i<pages.length; i++) {
    await iframe.goto(`${baseURL}/formgrader/${pages[i]}`);
    for (var j=0; j<links.length; j++) {
      click_link(iframe, links[j][0]);
      await iframe.waitForNavigation({'url': encodeURI(`${baseURL}/formgrader/${links[j][2]}`)});
      await check_formgrader_breadcrumbs(iframe, [links[j][1]]);
      expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/${links[j][2]}`));
    }
  }
});
