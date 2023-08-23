import { test as jupyterLabTest, galata, IJupyterLabPageFixture, expect } from '@jupyterlab/galata';
import { APIRequestContext, Locator } from '@playwright/test';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

import { test as notebookTest } from './utils/notebook_fixtures';
import {
  executeCommand,
  createEnv,
  waitForErrorModal,
  closeErrorModal,
  waitForSuccessModal,
  closeSuccessModal} from './utils/test_utils';

const testDir = process.env.NBGRADER_TEST_DIR || '';
if (!testDir){
  throw new Error('Test directory not provided');
}
if (!fs.existsSync(testDir)){
  throw new Error(`Test directory ${testDir} doesn't exists`);
}

const isWindows = os.platform().startsWith('win');

const tempPath = 'nbgrader-assignment-list-test';

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
test.afterEach(async ({ request, tmpPath }) => {
  if (!isWindows) {
    fs.rmSync(exchange_dir, { recursive: true, force: true });
    fs.rmSync(cache_dir, { recursive: true, force: true });
  }

  if (request === undefined) throw new Error("Request is undefined.");
  const contents = galata.newContentsHelper(request);
  await contents.deleteDirectory(tmpPath);

  if (await contents.fileExists("nbgrader_config.py"))
    contents.deleteFile("nbgrader_config.py");
  contents.uploadFile(
    path.resolve(__dirname, "./files/nbgrader_config.py"),
    "nbgrader_config.py"
  );
});

/*
 * Create a nbgrader file system and modify config
 */
const addCourses = async (request: APIRequestContext, tmpPath: string) => {
  const contents = galata.newContentsHelper(request);

  // copy files from the user guide
  const source = path.resolve(
    __dirname,
    "..",
    "..",
    "docs",
    "source",
    "user_guide",
    "source"
  );
  await contents.uploadDirectory(source, `${tmpPath}/source`);
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
  // don't run autotest in the ui tests
  await contents.deleteFile(
    `${tmpPath}/source/Problem Set 1/problem3.ipynb`
  );

  await contents.createDirectory(`${tmpPath}/source/ps.01`);
  await contents.uploadFile(
    path.resolve(__dirname, "files", "empty.ipynb"),
    `${tmpPath}/source/ps.01/problem 1.ipynb`
  );

  // Necessary to generate and release assignments
  fs.copyFileSync(
    path.resolve(testDir, "nbgrader_config.py"),
    path.resolve(testDir, tmpPath, "nbgrader_config.py")
  );
};

/*
 * Open the assignment list tab from palette
 */
const openAssignmentList = async (page: IJupyterLabPageFixture) => {
  await expect(page.locator(`${mainPanelId} .lm-TabBar-tab`)).toHaveCount(
    mainPanelTabCount
  );

  await page.keyboard.press("Control+Shift+c");
  await page
    .locator(
      '#modal-command-palette li[data-command="nbgrader:open-assignment-list"]'
    )
    .click();

  var tabs = page.locator(`${mainPanelId} .lm-TabBar-tab`);
  await expect(tabs).toHaveCount(
    mainPanelTabCount + 1
  );

  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Assignments");
};

/*
 * Ensure that list of assignment has been loaded for a specific name ("released", "fetched", "submitted")
 */
const waitForList = async (
  page: IJupyterLabPageFixture,
  name: string,
  nb_rows: number
): Promise<Locator> => {
  await expect(
    page.locator(`#${name}_assignments_list_loading`)
  ).not.toBeVisible();
  await expect(
    page.locator(`#${name}_assignments_list_placeholder`)
  ).not.toBeVisible();
  await expect(
    page.locator(`#${name}_assignments_list_error`)
  ).not.toBeVisible();

  const rows = page.locator(`#${name}_assignments_list > .list_item`);
  await expect(rows).toHaveCount(nb_rows);
  return rows;
};

/*
 * Select a course in dropdown list
 */
const selectCourse = async (page: IJupyterLabPageFixture, course: string) => {
  await page.locator("#course_list_dropdown").click();
  await page.locator(`#course_list > li :text("${course}")`).click();
  await expect(page.locator("#course_list_default")).toHaveText(course);
};

/*
 * Expand a fetched assignment
 */
const expandFetched = async (
  page: IJupyterLabPageFixture,
  assignment: string,
  item_id: string
): Promise<Locator> => {
  await page
    .locator(`#fetched_assignments_list a:text("${assignment}")`)
    .click();
  await page.waitForSelector(`${item_id}.collapse.in`);

  const rows = page.locator(`${item_id} .list_item`);
  for (var i = 1; i < (await rows.count()); i++) {
    expect(rows.nth(i)).toBeVisible();
  }
  return rows;
};

/*
 * Collapse an expended fetched assignment
 */
const collapseFetched = async (
  page: IJupyterLabPageFixture,
  assignment: string,
  item_id: string
) => {
  await page
    .locator(`#fetched_assignments_list a:text("${assignment}")`)
    .click();
  await expect(page.locator(`${item_id}.collapse`)).not.toHaveClass("in");
};

/*
 * Test opening assignment list tab from menu
 */
test("Open assignment list tab from menu", async ({ page, tmpPath }) => {

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  const nbgrader_menu = page.locator(`${menuPanelId} div.lm-MenuBar-itemLabel:text("Nbgrader")`);
  const assignmentList_menu = page.locator(
    '#jp-mainmenu-nbgrader li[data-command="nbgrader:open-assignment-list"]'
  );
  const tabs = page.locator(`${mainPanelId} .lm-TabBar-tab`);
  const lastTab_label = tabs.last().locator('.lm-TabBar-tabLabel');

  await expect(tabs).toHaveCount(mainPanelTabCount);

  // Check main menu exists
  await expect(nbgrader_menu).toHaveCount(1);

  // Open assignment list from the menu
  await nbgrader_menu.click();
  await assignmentList_menu.click();

  await expect(tabs).toHaveCount(mainPanelTabCount + 1);
  await expect(lastTab_label).toHaveText('Assignments');

  // Close the last tab
  await tabs.last().locator('.jp-icon-hover.lm-TabBar-tabCloseIcon').click();
  await expect(tabs).toHaveCount(mainPanelTabCount);

  // Open again
  await nbgrader_menu.click();
  await assignmentList_menu.click();

  await expect(tabs).toHaveCount(mainPanelTabCount + 1);
  await expect(lastTab_label).toHaveText('Assignments');
});

/*
 * Test showing assignment list
 */
test("Show assignment list", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // Wait for DOM of each status
  await page.waitForSelector("#released_assignments_list");
  await page.waitForSelector("#fetched_assignments_list");
  await page.waitForSelector("#submitted_assignments_list");

  // release an assignment
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );

  // refresh assignments
  await page.locator("#refresh_assignments_list").click();

  // expect finding the released assignment
  const rows = await waitForList(page, "released", 1);
  expect(rows.first().locator(".item_name")).toHaveText("Problem Set 1");
  expect(rows.first().locator(".item_course")).toHaveText("abc101");
});

/*
 * Test multiple released assignments
 */
test("Multiple released assignments", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release two assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignments
  await page.locator("#refresh_assignments_list").click();

  // select a course
  await selectCourse(page, "xyz 200");

  // expect finding the released assignment for selected course
  const rows = await waitForList(page, "released", 1);
  expect(rows.first().locator(".item_name")).toHaveText("ps.01");
  expect(rows.first().locator(".item_course")).toHaveText("xyz 200");
});

/*
 * Test fetch assignment
 */
test("Fetch assignments", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release some assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignment list
  await page.locator("#refresh_assignments_list").click();

  // select one course
  await selectCourse(page, "xyz 200");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // check that there is only one fetched
  rows = await waitForList(page, "fetched", 1);
  expect(rows.first().locator(".item_name").first()).toHaveText("ps.01");
  expect(rows.first().locator(".item_course").first()).toHaveText("xyz 200");

  // check that the directory has been created
  const contents = galata.newContentsHelper(request);
  expect(contents.directoryExists("ps.01"));

  // expand assignment notebooks
  rows = await expandFetched(page, "ps.01", "#nbgrader-xyz_200-ps01");
  await expect(rows).toHaveCount(2);
  await expect(rows.last().locator(".item_name")).toHaveText("problem 1");

  // collapse assignments notebooks
  await collapseFetched(page, "ps.01", "#nbgrader-xyz_200-ps01");
});

/*
 * Test submit assignment
 */
test("Submit assignments", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create directories and config files, and open assignment_list tab
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release some assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignment list
  await page.locator("#refresh_assignments_list").click();

  // select one course
  await selectCourse(page, "xyz 200");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // check that there is only one fetched and submit
  rows = await waitForList(page, "fetched", 1);
  await rows.first().locator('.item_status button:text("Submit")').click();

  // check that there is only one submitted
  rows = await waitForList(page, "submitted", 1);
  expect(rows.first().locator(".item_name").first()).toHaveText("ps.01");
  expect(rows.first().locator(".item_course").first()).toHaveText("xyz 200");

  // check again that there is only one submitted for that course
  rows = page.locator("#nbgrader-xyz_200-ps01-submissions > .list_item");
  // the first row should be empty
  expect(rows).toHaveCount(2);

  // submit a second time
  rows = await waitForList(page, "fetched", 1);
  await rows.first().locator('.item_status button:text("Submit")').click();

  // check there are two submitted (the first row is empty)
  await expect(
    page.locator("#nbgrader-xyz_200-ps01-submissions > .list_item")
  ).toHaveCount(3);
  rows = page.locator("#nbgrader-xyz_200-ps01-submissions > .list_item");

  const timestamp1 = rows.nth(1).locator(".item_name").textContent();
  const timestamp2 = rows.nth(2).locator(".item_name").textContent();
  expect(timestamp1 != timestamp2);
});

/*
 * Test submitting assignment without notebook
 */
test("submit assignment missing notebook", async ({
  page,
  request,
  tmpPath,
}) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create directories and config files, and open assignment_list tab
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release some assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignment list
  await page.locator("#refresh_assignments_list").click();

  // select one course
  await selectCourse(page, "xyz 200");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // check that there is only one fetched and submit
  rows = await waitForList(page, "fetched", 1);
  await rows.first().locator('.item_status button:text("Submit")').click();

  // check that there is only one submitted
  rows = await waitForList(page, "submitted", 1);
  expect(rows.first().locator(".item_name").first()).toHaveText("ps.01");
  expect(rows.first().locator(".item_course").first()).toHaveText("xyz 200");
  rows = page.locator("#nbgrader-xyz_200-ps01-submissions > .list_item");
  expect(rows).toHaveCount(2);

  // rename the assignment notebook file
  const contents = galata.newContentsHelper(request);
  expect(await contents.fileExists(`${tmpPath}/ps.01/problem 1.ipynb`));
  await contents.renameFile(
    `${tmpPath}/ps.01/problem 1.ipynb`,
    `${tmpPath}/ps.01/my problem 1.ipynb`
  );

  // submit again and check it has submitted
  rows = await waitForList(page, "fetched", 1);
  await rows.first().locator('.item_status button:text("Submit")').click();
  rows = await waitForList(page, "submitted", 1);
  expect(rows.first().locator(".item_name").first()).toHaveText("ps.01");
  expect(rows.first().locator(".item_course").first()).toHaveText("xyz 200");
  rows = page.locator("#nbgrader-xyz_200-ps01-submissions > .list_item");
  expect(rows).toHaveCount(3);

  const timestamp1 = rows.nth(1).locator(".item_name").textContent();
  const timestamp2 = rows.nth(2).locator(".item_name").textContent();
  expect(timestamp1 != timestamp2);

  // Set strict flag
  fs.appendFileSync(
    path.resolve(testDir, tmpPath, "nbgrader_config.py"),
    "c.ExchangeSubmit.strict = True"
  );

  // submit again and check that nothing changes
  rows = await waitForList(page, "fetched", 1);
  await rows.first().locator('.item_status button:text("Submit")').click();

  // wait for error modal and close it
  await waitForErrorModal(page);
  await closeErrorModal(page);

  // check that nothing has change in submitted list
  rows = await waitForList(page, "submitted", 1);
  expect(rows.first().locator(".item_name").first()).toHaveText("ps.01");
  expect(rows.first().locator(".item_course").first()).toHaveText("xyz 200");
  rows = page.locator("#nbgrader-xyz_200-ps01-submissions > .list_item");
  expect(rows).toHaveCount(3);
});

/*
 * Test fetch a second assignment
 */
test("Fetch a second assignment", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release some assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignment list
  await page.locator("#refresh_assignments_list").click();

  // select one course
  await selectCourse(page, "xyz 200");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // select the other course
  await selectCourse(page, "abc101");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // check that there is only one fetched
  rows = await waitForList(page, "fetched", 1);
  expect(rows.first().locator(".item_name").first()).toHaveText(
    "Problem Set 1"
  );
  expect(rows.first().locator(".item_course").first()).toHaveText("abc101");

  // check that the directory has been created
  const contents = galata.newContentsHelper(request);
  expect(contents.directoryExists("Problem Set 1"));

  // expand assignment notebooks
  rows = await expandFetched(
    page,
    "Problem Set 1",
    "#nbgrader-abc101-Problem_Set_1"
  );
  await expect(rows).toHaveCount(3);
  await expect(rows.nth(1).locator(".item_name")).toHaveText("Problem 1");
  await expect(rows.last().locator(".item_name")).toHaveText("Problem 2");

  // collapse assignments notebooks
  await collapseFetched(
    page,
    "Problem Set 1",
    "#nbgrader-abc101-Problem_Set_1"
  );
});

/*
 * Test submit another assignment
 */
test("Submit another assignments", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create directories and config files, and open assignment_list tab
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release some assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignment list
  await page.locator("#refresh_assignments_list").click();

  // select one course
  await selectCourse(page, "abc101");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // check that there is only one fetched and submit
  rows = await waitForList(page, "fetched", 1);
  await rows.first().locator('.item_status button:text("Submit")').click();

  // check that there is only one submitted
  rows = await waitForList(page, "submitted", 1);
  expect(rows.first().locator(".item_name").first()).toHaveText(
    "Problem Set 1"
  );
  expect(rows.first().locator(".item_course").first()).toHaveText("abc101");

  // check again that there is only one submitted for that course
  rows = page.locator(
    "#nbgrader-abc101-Problem_Set_1-submissions > .list_item"
  );
  // the first row should be empty
  expect(rows).toHaveCount(2);
});

/*
 * Test validate assignment
 */
test("Validate OK", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create directories and config files, and open assignment_list tab
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release some assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignment list
  await page.locator("#refresh_assignments_list").click();

  // select one course
  await selectCourse(page, "xyz 200");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // check that there is only one fetched and submit
  rows = await waitForList(page, "fetched", 1);

  // expand assignment notebooks
  rows = await expandFetched(page, "ps.01", "#nbgrader-xyz_200-ps01");
  await expect(rows).toHaveCount(2);
  await expect(rows.last().locator(".item_name")).toHaveText("problem 1");

  // Click on validate
  await rows.last().locator('.item_status button:text("Validate")').click();

  await waitForSuccessModal(page);
  await closeSuccessModal(page);
});

/*
 * Test validation failure
 */
test("Validate failure", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create directories and config files, and open assignment_list tab
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);
  await openAssignmentList(page);

  // release some assignments
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );
  await executeCommand("nbgrader generate_assignment 'ps.01' --force");
  await executeCommand(
    "nbgrader release_assignment 'ps.01' --course 'xyz 200' --force"
  );

  // refresh assignment list
  await page.locator("#refresh_assignments_list").click();

  // select one course
  await selectCourse(page, "abc101");

  // check that there is only one released, and fetch it
  var rows = await waitForList(page, "released", 1);
  await rows.first().locator(".item_status button").click();

  // check that there is only one fetched and submit
  rows = await waitForList(page, "fetched", 1);

  // expand assignment notebooks
  rows = await expandFetched(
    page,
    "Problem Set 1",
    "#nbgrader-abc101-Problem_Set_1"
  );
  await expect(rows).toHaveCount(3);
  await expect(rows.nth(1).locator(".item_name")).toHaveText("Problem 1");
  await expect(rows.last().locator(".item_name")).toHaveText("Problem 2");

  // Click on validate
  await rows.last().locator('.item_status button:text("Validate")').click();
  await waitForErrorModal(page);
  await closeErrorModal(page);
});

/*
 * Test missing exchange directory
 */
test("Missing exchange directory", async ({ page, request, tmpPath }) => {
  test.skip(isWindows, "This feature is not implemented for Windows");

  if (request === undefined) throw new Error("Request is undefined.");

  if (isNotebook) await page.goto(`tree/${tmpPath}`);

  // create directories and config files
  await createEnv(testDir, tmpPath, exchange_dir, cache_dir, isWindows);
  await addCourses(request, tmpPath);

  // delete exchange directory
  fs.rmSync(exchange_dir, { recursive: true, force: true });

  // open assignment_list tab
  await openAssignmentList(page);

  // Expecting error on lists and dropdown
  await expect(page.locator(`#released_assignments_list_error`)).toBeVisible();
  await expect(page.locator(`#fetched_assignments_list_error`)).toBeVisible();
  await expect(page.locator(`#submitted_assignments_list_error`)).toBeVisible();

  await expect(page.locator("#course_list_default")).toHaveText(
    "Error fetching courses!"
  );

  // create exchange directory again
  fs.mkdtempSync(exchange_dir);

  // release assignment
  await executeCommand("nbgrader generate_assignment 'Problem Set 1' --force");
  await executeCommand(
    "nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force"
  );

  // refresh assignment list and expect retrieving released assignment
  await page.locator("#refresh_assignments_list").click();
  const rows = await waitForList(page, "released", 1);
  expect(rows.first().locator(".item_name")).toHaveText("Problem Set 1");
  expect(rows.first().locator(".item_course")).toHaveText("abc101");
});
