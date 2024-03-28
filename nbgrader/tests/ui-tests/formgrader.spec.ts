import { test as jupyterLabTest, galata, IJupyterLabPageFixture } from "@jupyterlab/galata";
import { APIRequestContext, expect, Frame } from "@playwright/test";
import * as path from "path";
import * as os from "os";
import * as fs from "fs";
import { test as notebookTest } from './utils/notebook_fixtures';

import { executeCommand, createEnv } from "./utils/test_utils";

const testDir = process.env.NBGRADER_TEST_DIR || '';
if (!testDir){
  throw new Error('Test directory not provided');
}
if (!fs.existsSync(testDir)){
  throw new Error(`Test directory ${testDir} doesn't exists`);
}

const isWindows = os.platform().startsWith('win');

const tempPath = 'nbgrader-formgrader-test';

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

var exchange_dir:string;
var cache_dir: string;

/*
 * Create environment
 */
test.beforeEach(async ({ request, tmpPath }) => {
  if (request === undefined) throw new Error("Request is undefined.");

  const contents = galata.newContentsHelper(request);

  await contents.createDirectory(tmpPath);

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
  if (!isWindows) {
    fs.rmSync(exchange_dir, { recursive: true, force: true });
    fs.rmSync(cache_dir, { recursive: true, force: true });
  }

  if (request === undefined) throw new Error("Request is undefined.");

  const contents = galata.newContentsHelper(request, page);
  await contents.deleteDirectory(tmpPath);

  if (await contents.fileExists("nbgrader_config.py")){
    await contents.deleteFile("nbgrader_config.py");
  }

  await contents.uploadFile(
    path.resolve(__dirname, "./files/nbgrader_config.py"),
    "nbgrader_config.py"
  );
});

/*
 * Create a nbgrader file system
 */
const addCourses = async (
  request: APIRequestContext,
  page: IJupyterLabPageFixture,
  tmpPath: string
) => {
  const contents = galata.newContentsHelper(request, page);

  // copy files from the user guide
  const source_path = path.resolve(
    __dirname,
    "..",
    "..",
    "docs",
    "source",
    "user_guide",
    "source"
  );
  const submitted_path = path.resolve(
    __dirname,
    "..",
    "..",
    "docs",
    "source",
    "user_guide",
    "submitted"
  );

  await contents.uploadDirectory(source_path, `${tmpPath}/source`);

  const students = ["bitdiddle", "hacker"];
  for (var i = 0; i < 2; i++) {
    await contents.uploadDirectory(
      path.resolve(submitted_path, students[i]),
      `${tmpPath}/submitted/${students[i]}`
    );
  }

  // Rename the files and directory to have spaces in names
  await contents.renameDirectory(
    `${tmpPath}/source/ps1`,
    `${tmpPath}/source/Problem Set 1`
  );
  await contents.renameFile(
    `${tmpPath}/source/Problem Set 1/problem1.ipynb`,
    `${tmpPath}/source/Problem Set 1/Problem 1.ipynb`
  );
  await contents.renameFile(
    `${tmpPath}/source/Problem Set 1/problem2.ipynb`,
    `${tmpPath}/source/Problem Set 1/Problem 2.ipynb`
  );
  await contents.renameDirectory(
    `${tmpPath}/submitted/bitdiddle`,
    `${tmpPath}/submitted/Bitdiddle`
  );
  await contents.renameDirectory(
    `${tmpPath}/submitted/Bitdiddle/ps1`,
    `${tmpPath}/submitted/Bitdiddle/Problem Set 1`
  );
  await contents.renameFile(
    `${tmpPath}/submitted/Bitdiddle/Problem Set 1/problem1.ipynb`,
    `${tmpPath}/submitted/Bitdiddle/Problem Set 1/Problem 1.ipynb`
  );
  await contents.renameFile(
    `${tmpPath}/submitted/Bitdiddle/Problem Set 1/problem2.ipynb`,
    `${tmpPath}/submitted/Bitdiddle/Problem Set 1/Problem 2.ipynb`
  );
  await contents.renameDirectory(
    `${tmpPath}/submitted/hacker`,
    `${tmpPath}/submitted/Hacker`
  );
  await contents.renameDirectory(
    `${tmpPath}/submitted/Hacker/ps1`,
    `${tmpPath}/submitted/Hacker/Problem Set 1`
  );
  await contents.renameFile(
    `${tmpPath}/submitted/Hacker/Problem Set 1/problem1.ipynb`,
    `${tmpPath}/submitted/Hacker/Problem Set 1/Problem 1.ipynb`
  );
  await contents.renameFile(
    `${tmpPath}/submitted/Hacker/Problem Set 1/problem2.ipynb`,
    `${tmpPath}/submitted/Hacker/Problem Set 1/Problem 2.ipynb`
  );

  fs.copyFileSync(
    path.resolve(testDir, "nbgrader_config.py"),
    path.resolve(testDir, tmpPath, "nbgrader_config.py")
  );

  // generate some assignments
  await executeCommand(
    `nbgrader generate_assignment 'Problem Set 1' --IncludeHeaderFooter.header=${path.resolve(
      testDir,
      tmpPath,
      "source",
      "header.ipynb"
    )}`
  );

  // autograde assignment
  await executeCommand("nbgrader autograde 'Problem Set 1'");
};

/*
 * Open the formgrader tab
 */
const openFormgrader = async (page: IJupyterLabPageFixture) => {
  await expect(page.locator(`${mainPanelId} .lm-TabBar-tab`)).toHaveCount(
    mainPanelTabCount
  );

  await page.keyboard.press("Control+Shift+c");
  await page
    .locator(
      '#modal-command-palette li[data-command="nbgrader:open-formgrader"]'
    )
    .click();

  var tabs = page.locator(`${mainPanelId} .lm-TabBar-tab`);
  await expect(tabs).toHaveCount(
    mainPanelTabCount + 1
  );

  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Formgrader");
};

/*
 * Check formgrader breadcrumbs
 */
const checkFormgraderBreadcrumbs = async (
  iframe: Frame,
  breadcrumbs: string[]
) => {
  await expect(iframe.locator(".breadcrumb li")).toHaveCount(
    breadcrumbs.length
  );

  const elements = iframe.locator(".breadcrumb li");
  const array: string[] = [];
  for (var i = 0; i < (await elements.count()); i++) {
    array.push((await elements.nth(i).textContent()) as string);
  }
  expect(array.sort()).toEqual(breadcrumbs.sort());
};

/*
 * Check formgrader breadcrumbs
 */
const checkFormgradeViewBreadcrumbs = async (
  iframe: Frame,
  breadcrumbs: string[],
  no_submission_count?: boolean
) => {
  await expect(iframe.locator(".breadcrumb li a:visible")).toHaveCount(
    breadcrumbs.length
  );

  const elements = iframe.locator(".breadcrumb li a:visible");
  const in_page_breadcrumbs: string[] = [];
  for (var i = 0; i < (await elements.count()); i++) {
    in_page_breadcrumbs.push(
      ((await elements.nth(i).textContent()) as string).trim()
    );
  }

  if (no_submission_count) {
    expect(in_page_breadcrumbs.slice(0, -1).sort()).toEqual(
      breadcrumbs.slice(0, -1).sort()
    );
    expect(
      in_page_breadcrumbs[in_page_breadcrumbs.length - 1].includes(
        breadcrumbs[-1]
      )
    );
  } else expect(in_page_breadcrumbs.sort()).toEqual(breadcrumbs.sort());
};

/*
 * Click on link by text
 */
const clickLink = async (iframe: Frame, text: string) => {
  await iframe.click(`a:text-is('${text}')`);
};

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
test("Open formgrader tab from menu", async ({ page, tmpPath }) => {

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  const nbgrader_menu = page.locator(`${menuPanelId} div.lm-MenuBar-itemLabel:text("Nbgrader")`);
  const formgrader_menu = page.locator('#jp-mainmenu-nbgrader li[data-command="nbgrader:open-formgrader"]');
  const tabs = page.locator(`${mainPanelId} .lm-TabBar-tab`);
  const lastTab_label = tabs.last().locator('.lm-TabBar-tabLabel');

  await expect(tabs).toHaveCount(mainPanelTabCount);

  // Check main menu exists
  await expect(nbgrader_menu).toHaveCount(1);

  // Open formgrader from the menu
  await nbgrader_menu.click();
  await formgrader_menu.click();

  await expect(tabs).toHaveCount(mainPanelTabCount + 1);
  await expect(lastTab_label).toHaveText('Formgrader');

  // Close the last tab
  await tabs.last().locator('.jp-icon-hover.lm-TabBar-tabCloseIcon').click();
  await expect(tabs).toHaveCount(mainPanelTabCount);

  // Open again
  await nbgrader_menu.click();
  await formgrader_menu.click();

  await expect(tabs).toHaveCount(mainPanelTabCount + 1);
  await expect(lastTab_label).toHaveText('Formgrader');
});

/*
 * Load manage assignments
 */
test("Load manage assignments", async ({ page, baseURL, request, tmpPath }) => {

  /**
   * Switch active tab (Notebook only)
   * NOTE:
  *   this function must be used only for notebook tests, not for jupyterLab tests.
  */
  const switchTab = async (page: IJupyterLabPageFixture, tabLabel: string) => {
    if (isNotebook) {
      await page.locator(`role=tab >> text=${tabLabel}`).click();
    }
  };

  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe and check for breadcrumbs
  const iframe = page.mainFrame().childFrames()[0];

  await checkFormgraderBreadcrumbs(iframe, ["Assignments"]);
  expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader`));

  // expect the current path in tree tab to be the tmpPath.
  await switchTab(page, 'Files');
  const breadCrumbs = page.locator('.jp-FileBrowser-crumbs');
  await breadCrumbs.getByTitle(tmpPath).waitFor();

  // click on the "Problem Set 1" link and check if file browser has changed of directory
  await switchTab(page, 'Formgrader');

  await clickLink(iframe, "Problem Set 1");
  await switchTab(page, 'Files');
  await breadCrumbs
    .getByTitle(tmpPath.concat("/source/Problem Set 1"))
    .waitFor();

  // click on preview link and check if file browser has changed of directory
  await switchTab(page, 'Formgrader');
  await iframe.locator("td.preview .glyphicon").click();
  await switchTab(page, 'Files');
  await breadCrumbs
    .getByTitle(tmpPath.concat("/release/Problem Set 1"))
    .waitFor();

  // click on the first number of submissions and check that iframe has change URL
  await switchTab(page, 'Formgrader');
  await iframe.click("td.num-submissions a");
  await checkFormgraderBreadcrumbs(iframe, ["Assignments", "Problem Set 1"]);
  expect(iframe.url()).toBe(
    encodeURI(`${baseURL}/formgrader/manage_submissions/Problem Set 1`)
  );
});

/*
 * Load manage submissions
 */
test("Load manage submissions", async ({ page, baseURL, request, tmpPath }) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to manage_submissions
  await iframe.goto(`${baseURL}/formgrader/manage_submissions/Problem Set 1`);

  // await iframe.click("td.num-submissions a");
  await checkFormgraderBreadcrumbs(iframe, ["Assignments", "Problem Set 1"]);

  // clicking on breadcrumbs should go back to manage_assignments
  await clickLink(iframe, "Assignments");
  await checkFormgraderBreadcrumbs(iframe, ["Assignments"]);
  expect(iframe.url()).toBe(
    encodeURI(`${baseURL}/formgrader/manage_assignments`)
  );

  // page.goBack(); // seems endless
  await iframe.goto(`${baseURL}/formgrader/manage_submissions/Problem Set 1`);
  await checkFormgraderBreadcrumbs(iframe, ["Assignments", "Problem Set 1"]);

  // Check students links
  await expect(iframe.locator("td.student-name")).toHaveCount(2);
  for (var i = 0; i < (await iframe.locator("td.student-name").count()); i++) {
    var student_name = (await iframe
      .locator("td.student-name")
      .nth(i)
      .getAttribute("data-order")) as string;
    var student_id = (await iframe
      .locator("td.student-id")
      .nth(i)
      .getAttribute("data-order")) as string;
    await clickLink(iframe, student_name);
    await checkFormgraderBreadcrumbs(iframe, [
      "Students",
      student_id,
      "Problem Set 1",
    ]);
    expect(iframe.url()).toBe(
      encodeURI(
        `${baseURL}/formgrader/manage_students/${student_id}/Problem Set 1`
      )
    );
    await iframe.goto(`${baseURL}/formgrader/manage_submissions/Problem Set 1`);
  }
});

/*
 * Load gradebook1
 */
test("Load gradebook1", async ({ page, baseURL, request, tmpPath }) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook
  await iframe.goto(`${baseURL}/formgrader/gradebook`);

  // await iframe.click("td.num-submissions a");
  await checkFormgraderBreadcrumbs(iframe, ["Manual Grading"]);

  // click on assignment
  await clickLink(iframe, "Problem Set 1");
  await checkFormgraderBreadcrumbs(iframe, ["Manual Grading", "Problem Set 1"]);
  expect(iframe.url()).toBe(
    encodeURI(`${baseURL}/formgrader/gradebook/Problem Set 1`)
  );

  // test that the task column is present
  await expect(iframe.locator('th:text-is("Avg. Task Score")')).toHaveCount(1);
});

/*
 * Load gradebook2
 */
test("Load gradebook2", async ({ page, baseURL, request, tmpPath }) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);
  await checkFormgraderBreadcrumbs(iframe, ["Manual Grading", "Problem Set 1"]);

  // clicking on breadcrumbs should go back to manual grading
  await iframe.click('ol.breadcrumb a:text-is("Manual Grading")');
  await checkFormgraderBreadcrumbs(iframe, ["Manual Grading"]);
  expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/gradebook`));

  // Send back iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);

  // test problems links
  await expect(iframe.locator("td.name")).toHaveCount(2);
  for (var i = 0; i < (await iframe.locator("td.name").count()); i++) {
    var problem_name = (await iframe
      .locator("td.name")
      .nth(i)
      .getAttribute("data-order")) as string;
    await clickLink(iframe, problem_name);
    await checkFormgraderBreadcrumbs(iframe, [
      "Manual Grading",
      "Problem Set 1",
      problem_name,
    ]);
    expect(iframe.url()).toBe(
      encodeURI(`${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`)
    );
    await expect(iframe.locator('th:text-is("Task Score")')).toHaveCount(1);
    await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);
  }
});

/*
 * Load gradebook3
 */
test("Load gradebook3", async ({ page, baseURL, request, tmpPath }) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1`);

  // for each problem
  await expect(iframe.locator("td.name")).toHaveCount(2);
  for (var i = 0; i < (await iframe.locator("td.name").count()); i++) {
    var problem_name = (await iframe
      .locator("td.name")
      .nth(i)
      .getAttribute("data-order")) as string;
    await iframe.goto(
      `${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`
    );
    await checkFormgraderBreadcrumbs(iframe, [
      "Manual Grading",
      "Problem Set 1",
      problem_name,
    ]);

    // test click on breadcrumb 'Manual Grading' to change iframe URL, then go back
    await iframe.click('ol.breadcrumb a:text-is("Manual Grading")');
    await checkFormgraderBreadcrumbs(iframe, ["Manual Grading"]);
    expect(iframe.url()).toBe(encodeURI(`${baseURL}/formgrader/gradebook`));
    await iframe.goto(
      `${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`
    );

    // test click on breadcrumb 'Problem Set 1' to change iframe URL, then go back
    await iframe.click('ol.breadcrumb a:text-is("Problem Set 1")');
    await checkFormgraderBreadcrumbs(iframe, [
      "Manual Grading",
      "Problem Set 1",
    ]);
    await iframe.goto(
      `${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`
    );

    // test submissions links
    await expect(iframe.locator("td.name")).toHaveCount(2);
    for (var j = 0; j < (await iframe.locator("td.name").count()); j++) {
      var submission_id =
        parseInt(
          (await iframe
            .locator("td.name")
            .nth(j)
            .getAttribute("data-order")) as string
        ) + 1;
      await clickLink(iframe, `Submission #${submission_id.toString()}`);
      await checkFormgradeViewBreadcrumbs(iframe, [
        "Manual Grading",
        "Problem Set 1",
        problem_name,
        `Submission #${submission_id.toString()}`,
      ]);
      // TODO: find the submission ID to check URL ?

      if (problem_name == "Problem 1") {
        await expect(
          iframe.locator('span:text-is("Student\'s task")')
        ).toHaveCount(1);
      }
      await iframe.goto(
        `${baseURL}/formgrader/gradebook/Problem Set 1/${problem_name}`
      );
    }
  }
});

/*
 * Gradebook3 show/hide students names
 */
test("Gradebook3 show hide names", async ({
  page,
  baseURL,
  request,
  tmpPath,
}) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to gradebook Problem Set 1
  await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/Problem 1`);
  await checkFormgraderBreadcrumbs(iframe, [
    "Manual Grading",
    "Problem Set 1",
    "Problem 1",
  ]);

  const col2 = iframe.locator("td.name").first();
  const hidden = iframe.locator("td .glyphicon.name-hidden").first();
  const shown = iframe.locator("td .glyphicon.name-shown").first();

  // check shown and hidden elements
  await expect(col2).toHaveText(/Submission #[1-2]/, { useInnerText: true });
  await expect(hidden).toBeVisible();
  await expect(shown).toBeHidden();

  // show name
  await hidden.click();
  await expect(col2).toHaveText(/(H, Alyssa|B, Ben)/, { useInnerText: true });
  await expect(hidden).toBeHidden();
  await expect(shown).toBeVisible();

  // hide name again
  await shown.click();
  await expect(col2).toHaveText(/Submission #[1-2]/, { useInnerText: true });
  await expect(hidden).toBeVisible();
  await expect(shown).toBeHidden();
});

/*
 * Toggle name visibility button
 */
test('Gradebook toggle names button', async ({
    page,
    baseURL,
    request,
    tmpPath
  }) => {

    test.skip(isWindows, 'This test does not work on Windows');

    if (baseURL === undefined) throw new Error("BaseURL is undefined.");

    if (isNotebook) await page.goto(`tree/${tmpPath}`);

    // create environment
    await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
    await addCourses(request, page, tmpPath);
    await openFormgrader(page);

    // get formgrader iframe
    const iframe = page.mainFrame().childFrames()[0];

    // Change iframe URL to gradebook Problem Set 1
    await iframe.goto(`${baseURL}/formgrader/gradebook/Problem Set 1/Problem 1`);
    await checkFormgraderBreadcrumbs(iframe, [
      "Manual Grading",
      "Problem Set 1",
      "Problem 1"
    ]);

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
test("Load students", async ({ page, baseURL, request, tmpPath }) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  // Change iframe URL to students
  await iframe.goto(`${baseURL}/formgrader/manage_students`);
  await checkFormgraderBreadcrumbs(iframe, ["Students"]);

  // Check students links
  await expect(iframe.locator("td.name")).toHaveCount(3);
  for (var i = 0; i < (await iframe.locator("td.name").count()); i++) {
    var student_name = (await iframe
      .locator("td.name")
      .nth(i)
      .getAttribute("data-order")) as string;
    var student_id = (await iframe
      .locator("td.id")
      .nth(i)
      .getAttribute("data-order")) as string;
    await clickLink(iframe, student_name);
    await checkFormgraderBreadcrumbs(iframe, ["Students", student_id]);
    expect(iframe.url()).toBe(
      encodeURI(`${baseURL}/formgrader/manage_students/${student_id}`)
    );
    await expect(iframe.locator('th:text("Task Score")')).toHaveCount(1);
    await iframe.goto(`${baseURL}/formgrader/manage_students`);
  }
});

/*
 * Test students submissions
 */
test("Load students submissions", async ({
  page,
  baseURL,
  request,
  tmpPath,
}) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  const student_ids = ["Bitdiddle", "Hacker"];

  for (var i = 0; i < 2; i++) {
    // foreach loop does not work (raise at goto statement)
    // Change iframe URL to student
    await iframe.goto(
      `${baseURL}/formgrader/manage_students/${student_ids[i]}`
    );
    await checkFormgraderBreadcrumbs(iframe, ["Students", student_ids[i]]);

    // Click on an assignment
    await clickLink(iframe, "Problem Set 1");
    // await iframe.waitForNavigation({'url': encodeURI(`${baseURL}/formgrader/manage_students/${student_ids[i]}/Problem Set 1`)});
    await checkFormgraderBreadcrumbs(iframe, [
      "Students",
      student_ids[i],
      "Problem Set 1",
    ]);
    expect(iframe.url()).toBe(
      encodeURI(
        `${baseURL}/formgrader/manage_students/${student_ids[i]}/Problem Set 1`
      )
    );
    await expect(iframe.locator('th:text("Task Score")')).toHaveCount(1);
  }
});

/*
 * Switch views
 */
test("Switch views", async ({ page, baseURL, request, tmpPath }) => {
  test.skip(isWindows, "This test does not work on Windows");

  if (baseURL === undefined) throw new Error("BaseURL is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create environment
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, page, tmpPath);
  await openFormgrader(page);

  // get formgrader iframe
  const iframe = page.mainFrame().childFrames()[0];

  const pages = ["", "manage_assignments", "gradebook", "manage_students"];
  const links = [
    ["Manage Assignments", "Assignments", "manage_assignments"],
    ["Manual Grading", "Manual Grading", "gradebook"],
    ["Manage Students", "Students", "manage_students"],
  ];

  for (var i = 0; i < pages.length; i++) {
    await iframe.goto(`${baseURL}/formgrader/${pages[i]}`);
    for (var j = 0; j < links.length; j++) {
      clickLink(iframe, links[j][0]);
      await iframe.waitForNavigation({
        url: encodeURI(`${baseURL}/formgrader/${links[j][2]}`),
      });
      await checkFormgraderBreadcrumbs(iframe, [links[j][1]]);
      expect(iframe.url()).toBe(
        encodeURI(`${baseURL}/formgrader/${links[j][2]}`)
      );
    }
  }
});
