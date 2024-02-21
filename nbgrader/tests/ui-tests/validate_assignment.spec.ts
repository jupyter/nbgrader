import { test as jupyterLabTest, galata, IJupyterLabPageFixture } from "@jupyterlab/galata";
import { expect } from "@playwright/test";
import * as path from "path";
import * as fs from 'fs';

import { test as notebookTest } from "./utils/notebook_fixtures";

import {
  waitForSuccessModal,
  closeSuccessModal,
  waitForErrorModal,
  closeErrorModal,
} from "./utils/test_utils";

const testDir = process.env.NBGRADER_TEST_DIR || '';
if (!testDir){
  throw new Error('Test directory not provided');
}
if (!fs.existsSync(testDir)){
  throw new Error(`Test directory ${testDir} doesn't exists`);
}

const tempPath = 'nbgrader-validate-assignments-test';

let test = jupyterLabTest;

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
}
else {
  test.use(baseTestUse);
}

const nbFiles = [
  "data.txt",
  "submitted-changed.ipynb",
  "submitted-unchanged.ipynb",
  "submitted-grade-cell-changed.ipynb",
  "submitted-locked-cell-changed.ipynb",
  "open_relative_file.ipynb",
  "submitted-grade-cell-type-changed.ipynb",
  "submitted-answer-cell-type-changed.ipynb",
];

/*
 * Copy notebook files before each test
 */
test.beforeEach(async ({ request, tmpPath }) => {
  if (request === undefined) throw new Error("Request is undefined.");

  const contents = galata.newContentsHelper(request);
  nbFiles.forEach((elem) => {
    contents.uploadFile(
      path.resolve(__dirname, `./files/${elem}`),
      `${tmpPath}/${elem}`
    );
  });
});

/*
 * Delete temp directory at the end of test
 */
test.afterAll(async ({ request, tmpPath }) => {
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
 * Open a notebook file.
 * NOTES:
 *  This function is only useful if testing extension in JupyterLab.
 *  In Notebook tests we open a new browser tab instead.
 */
const openNotebook = async (page: IJupyterLabPageFixture, notebook: string) => {
  var filename = notebook + ".ipynb";
  var tab_count = await page
    .locator("#jp-main-dock-panel .lm-TabBar-tab")
    .count();
  await page
    .locator(
      `#filebrowser .jp-DirListing-content .jp-DirListing-itemText span:text-is('${filename}')`
    )
    .dblclick();
  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab")).toHaveCount(
    tab_count + 1
  );
  await page.waitForSelector(".jp-Notebook-cell");
};

/*
 * Test validation success
 */
test("Validation success", async ({ page, tmpPath }) => {

  // open the notebook
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/submitted-changed.ipynb`);
  } else {
    await openNotebook(page, "submitted-changed");
  }

  // click on validate, and expect a success modal
  await page.locator("jp-button.validate-button").click();
  await waitForSuccessModal(page);

  // close the modal
  await closeSuccessModal(page);
});

/*
 * Test validation failure
 */
test("Validation failure", async ({ page, tmpPath }) => {

  // open the notebook
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/submitted-unchanged.ipynb`);
  } else {
    await openNotebook(page, "submitted-unchanged");
  }

  // click on validate, and expect an error modal
  await page.locator("jp-button.validate-button").click();
  await waitForErrorModal(page);

  await page.waitForSelector(".nbgrader-ErrorDialog .validation-failed");

  // close the modal
  await closeErrorModal(page);
});

/*
 * Test validation with grade cell changed
 */
test("Validation grade cell changed", async ({ page, tmpPath }) => {

  // open the notebook
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/submitted-grade-cell-changed.ipynb`);
  } else {
    await openNotebook(page, "submitted-grade-cell-changed");
  }

  // click on validate, and expect an error modal
  await page.locator("jp-button.validate-button").click();
  await waitForErrorModal(page);

  await page.waitForSelector(".nbgrader-ErrorDialog .validation-changed");

  // close the modal
  await closeErrorModal(page);
});

/*
 * Test validation with locked cell changed
 */
test("Validation locked cell changed", async ({ page, tmpPath }) => {

  // open the notebook
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/submitted-locked-cell-changed.ipynb`);
  } else {
    await openNotebook(page, "submitted-locked-cell-changed");
  }

  // click on validate, and expect an error modal
  await page.locator("jp-button.validate-button").click();
  await waitForErrorModal(page);

  await page.waitForSelector(".nbgrader-ErrorDialog .validation-changed");

  // close the modal
  await closeErrorModal(page);
});

/*
 * Test validation opening relative file
 */
test("Validation open relative file", async ({ page, tmpPath }) => {

  // open the notebook
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/open_relative_file.ipynb`);
  } else {
    await openNotebook(page, "open_relative_file");
  }

  // click on validate, and expect a success modal
  await page.locator("jp-button.validate-button").click();
  await waitForSuccessModal(page);

  await page.waitForSelector(".nbgrader-SuccessDialog .validation-success");

  // close the modal
  await closeSuccessModal(page);
});

/*
 * Test validation with grade cell type changed
 */
test("Validation grade cell type changed", async ({ page, tmpPath }) => {

  // open the notebook
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/submitted-grade-cell-type-changed.ipynb`);
  } else {
    await openNotebook(page, "submitted-grade-cell-type-changed");
  }

  // click on validate, and expect an error modal
  await page.locator("jp-button.validate-button").click();
  await waitForErrorModal(page);

  await page.waitForSelector(".nbgrader-ErrorDialog .validation-type-changed");

  // close the modal
  await closeErrorModal(page);
});

/*
 * Test validation with answer cell type changed
 */
test("Validation answer cell type changed", async ({ page, tmpPath }) => {

  // open the notebook
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/submitted-answer-cell-type-changed.ipynb`);
  } else {
    await openNotebook(page, "submitted-answer-cell-type-changed");
  }

  // click on validate, and expect an error modal
  await page.locator("jp-button.validate-button").click();
  await waitForErrorModal(page);

  await page.waitForSelector(".nbgrader-ErrorDialog .validation-type-changed");

  // close the modal
  await closeErrorModal(page);
});
