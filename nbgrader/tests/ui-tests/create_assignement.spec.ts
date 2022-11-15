import { test as jupyterLabTest, galata, IJupyterLabPageFixture } from "@jupyterlab/galata";
import { expect } from "@playwright/test";
import * as path from "path";
import * as fs from 'fs';

import { test as notebookTest } from './utils/notebook_fixtures';
import { waitForErrorModal, closeErrorModal } from "./utils/test_utils";

const testDir = process.env.NBGRADER_TEST_DIR || '';
if (!testDir){
  throw new Error('Test directory not provided');
}
if (!fs.existsSync(testDir)){
  throw new Error(`Test directory ${testDir} doesn't exists`);
}

const tempPath = 'nbgrader-create-assignments-test';

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

const nbFiles = ["blank.ipynb", "task.ipynb", "old-schema.ipynb"];

/*
 * Copy notebook files before each test.
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
 * Delete temp directory at the end of test.
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
 * Save the current notebook file.
 */
const saveCurrentNotebook = async (page: IJupyterLabPageFixture) => {
  return await page.evaluate(async () => {
    var nb = window.jupyterapp.shell.currentWidget;
    await nb.context.save();
  });

  // TODO : ensure metadata has been saved
  // Read local file ?
};

/*
 * Activate assignment toolbar.
 */
const activateToolbar = async (page: IJupyterLabPageFixture) => {
  if ((await page.locator(".nbgrader-NotebookWidget").count()) > 0) {
    if (await page.locator(".nbgrader-NotebookWidget").isVisible()) {
      return;
    }
  }

  if (isNotebook) {
    await page.menu.clickMenuItem(
      "View>Right Sidebar>Show Nbgrader Create Assignment"
    );
  } else {
    const widget_button = page.locator(
      ".lm-TabBar-tab[title='Nbgrader Create Assignment']"
    );
    const button_position = await widget_button.boundingBox();

    if (button_position === null)
      throw new Error("Cannot get the position of the create assignment button.");

    await page.mouse.click(
      button_position.x + button_position.width / 2,
      button_position.y + button_position.height / 2
    );
  }

  await expect(page.locator(".nbgrader-NotebookWidget")).toBeVisible();
};

/*
 * Get the nbgrader's metadata of a cell.
 */
const getCellMetadata = async (
  page: IJupyterLabPageFixture,
  cell_number: number = 0
) => {
  return await page.evaluate((cell_num) => {
    var nb = window.jupyterapp.shell.currentWidget;
    return nb.model.cells.get(cell_num).metadata.get("nbgrader");
  }, cell_number);
};

/*
 * Set points to a notebook cell.
 */
const setPoints = async (
  page: IJupyterLabPageFixture,
  points: number = 0,
  index: number = 0
) => {
  await page
    .locator(".nbgrader-CellPoints input")
    .nth(index)
    .fill(points.toString());
  await page.keyboard.press("Enter");
};

/*
 * Set id to a notebook cell
 */
const setId = async (
  page: IJupyterLabPageFixture,
  id: string = "foo",
  index: number = 0
) => {
  await page.locator(".nbgrader-CellId input").nth(index).fill(id);
  await page.keyboard.press("Enter");
};

/*
 * Select type of assignment of a cell in nbgrader toolbar
 */
const selectInToolbar = async (
  page: IJupyterLabPageFixture,
  text: string,
  index: number = 0
) => {
  var select = page.locator(".nbgrader-NotebookWidget select").nth(index);
  await select.selectOption(text);
};

/*
 * Get the total points of an assignment
 */
const getTotalPoints = async (
  page: IJupyterLabPageFixture,
  index: number = 0
) => {
  return parseFloat(
    await page.locator(".nbgrader-TotalPointsInput").nth(0).inputValue()
  );
};

/*
 * Create a new cell in current notebook
 */
const createNewCell = async (
  page: IJupyterLabPageFixture,
  after: number = 0
) => {
  await page.locator(".jp-Cell .jp-InputArea-prompt").nth(after).click();
  await page.keyboard.press("b");
};

/*
 * Delete a cell in current notebook
 */
const deleteCell = async (page: IJupyterLabPageFixture, index: number = 0) => {
  await page.locator(".jp-Cell .jp-InputArea-prompt").nth(index).click();
  await page.keyboard.press("d");
  await page.keyboard.press("d");
};

/*
 * Test manipulating a manually graded cell
 */
test("manual cell", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  expect(await getCellMetadata(page)).toBeUndefined();

  await selectInToolbar(page, "manual");

  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", true);
  expect(metadata).toHaveProperty("grade", true);
  expect(metadata).toHaveProperty("locked", false);

  await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

  await setPoints(page, 2);
  expect(await getCellMetadata(page)).toHaveProperty("points", 2);

  expect((await getCellMetadata(page))["grade_id"]).toEqual(
    expect.stringMatching("^cell-")
  );
  await setId(page);
  expect(await getCellMetadata(page)).toHaveProperty("grade_id", "foo");

  await saveCurrentNotebook(page);

  await selectInToolbar(page, "");
  expect(await getCellMetadata(page)).toBeUndefined();

  await saveCurrentNotebook(page);
});

/*
 * Test manipulating a task cell
 */
test("task cell", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/task.ipynb`);
  } else {
    await openNotebook(page, "task");
  }

  await activateToolbar(page);

  expect(await getCellMetadata(page)).toBeUndefined();

  await selectInToolbar(page, "task");

  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", false);
  expect(metadata).toHaveProperty("grade", false);
  expect(metadata).toHaveProperty("locked", true);

  await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();

  await setPoints(page, 2);
  expect(await getCellMetadata(page)).toHaveProperty("points", 2);

  expect((await getCellMetadata(page))["grade_id"]).toEqual(
    expect.stringMatching("^cell-")
  );
  await setId(page);
  expect(await getCellMetadata(page)).toHaveProperty("grade_id", "foo");

  await saveCurrentNotebook(page);

  await selectInToolbar(page, "");
  expect(await getCellMetadata(page)).toBeUndefined();

  await saveCurrentNotebook(page);
});

/*
 * Test manipulating a solution graded cell
 */
test("solution cell", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  expect(await getCellMetadata(page)).toBeUndefined();

  await selectInToolbar(page, "solution");

  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", true);
  expect(metadata).toHaveProperty("grade", false);
  expect(metadata).toHaveProperty("locked", false);

  await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();

  expect((await getCellMetadata(page))["grade_id"]).toEqual(
    expect.stringMatching("^cell-")
  );
  await setId(page);
  expect(await getCellMetadata(page)).toHaveProperty("grade_id", "foo");

  await saveCurrentNotebook(page);

  await selectInToolbar(page, "");
  expect(await getCellMetadata(page)).toBeUndefined();

  await saveCurrentNotebook(page);
});

/*
 * Test manipulating a test graded cell
 */
test("tests cell", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  expect(await getCellMetadata(page)).toBeUndefined();

  await selectInToolbar(page, "tests");

  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", false);
  expect(metadata).toHaveProperty("grade", true);
  expect(metadata).toHaveProperty("locked", true);

  await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

  await setPoints(page, 2);
  expect(await getCellMetadata(page)).toHaveProperty("points", 2);

  expect((await getCellMetadata(page))["grade_id"]).toEqual(
    expect.stringMatching("^cell-")
  );
  await setId(page);
  expect(await getCellMetadata(page)).toHaveProperty("grade_id", "foo");

  await saveCurrentNotebook(page);

  await selectInToolbar(page, "");
  expect(await getCellMetadata(page)).toBeUndefined();

  await saveCurrentNotebook(page);
});

/*
 * Test converting cell's type
 */
test("tests to solution cell", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  expect(await getCellMetadata(page)).toBeUndefined();

  await selectInToolbar(page, "tests");

  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", false);
  expect(metadata).toHaveProperty("grade", true);
  expect(metadata).toHaveProperty("locked", true);

  await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

  await setPoints(page, 2);
  expect(await getCellMetadata(page)).toHaveProperty("points", 2);

  expect((await getCellMetadata(page))["grade_id"]).toEqual(
    expect.stringMatching("^cell-")
  );
  await setId(page);
  expect(await getCellMetadata(page)).toHaveProperty("grade_id", "foo");

  await saveCurrentNotebook(page);

  await selectInToolbar(page, "solution");
  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", true);
  expect(metadata).toHaveProperty("grade", false);
  expect(metadata).toHaveProperty("locked", false);
  expect(metadata["points"]).toBeUndefined();
  await saveCurrentNotebook(page);

  await selectInToolbar(page, "");
  expect(await getCellMetadata(page)).toBeUndefined();
  await saveCurrentNotebook(page);
});

/*
 * Tests on locked cell
 */
test("locked cell", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  expect(await getCellMetadata(page)).toBeUndefined();

  await selectInToolbar(page, "readonly");

  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", false);
  expect(metadata).toHaveProperty("grade", false);
  expect(metadata).toHaveProperty("locked", true);

  await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
  await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

  expect((await getCellMetadata(page))["grade_id"]).toEqual(
    expect.stringMatching("^cell-")
  );
  await setId(page);
  expect(await getCellMetadata(page)).toHaveProperty("grade_id", "foo");

  await saveCurrentNotebook(page);

  await selectInToolbar(page, "");
  expect(await getCellMetadata(page)).toBeUndefined();
  await saveCurrentNotebook(page);
});

/*
 * Test focus using TAB key
 */
test("tab key", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  // make the cell manually grading
  await selectInToolbar(page, "manual");

  // focus on cell type
  await page.locator(".nbgrader-CellType select").focus();
  await expect(page.locator(".nbgrader-CellType select")).toBeFocused();

  // press tab and focus on ID input
  await page.keyboard.press("Tab");
  await expect(page.locator(".nbgrader-CellId input")).toBeFocused();

  // press tab again and focus on points input
  await page.keyboard.press("Tab");
  await expect(page.locator(".nbgrader-CellPoints input")).toBeFocused();
});

/*
 * Test the total points of a notebook
 */
test("total points", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  // make sure the total points is zero
  expect(await getTotalPoints(page)).toBe(0);

  // make it autograder tests and set the points to two
  await selectInToolbar(page, "tests");
  await setPoints(page, 2);
  await setId(page);
  expect(await getTotalPoints(page)).toBe(2);

  // make it manually graded
  await selectInToolbar(page, "manual");
  expect(await getTotalPoints(page)).toBe(2);

  // make it a solution make sure the total points is zero
  await selectInToolbar(page, "solution");
  expect(await getTotalPoints(page)).toBe(0);

  // make it task
  await selectInToolbar(page, "task");
  expect(await getTotalPoints(page)).toBe(0);
  await setPoints(page, 2);
  expect(await getTotalPoints(page)).toBe(2);

  // create a new cell
  await createNewCell(page);

  // make it a test cell and check if total points is 3
  await selectInToolbar(page, "tests", 1);
  await setPoints(page, 1, 1);
  await setId(page, "bar", 1);
  expect(await getTotalPoints(page)).toBe(3);

  // delete the first cell
  await deleteCell(page);
  expect(await getTotalPoints(page)).toBe(1);

  // delete the new cell
  await deleteCell(page);
  expect(await getTotalPoints(page)).toBe(0);
});

/*
 * Test the total points of a notebook using task cell
 */
test("task total points", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/task.ipynb`);
  } else {
    await openNotebook(page, "task");
  }

  await activateToolbar(page);

  // make sure the total points is zero
  expect(await getTotalPoints(page)).toBe(0);

  // make cell autograded task and set the points to two
  await selectInToolbar(page, "task");
  await setPoints(page, 2);
  await setId(page);
  expect(await getTotalPoints(page)).toBe(2);

  // make cell manually graded
  await selectInToolbar(page, "manual");
  expect(await getTotalPoints(page)).toBe(2);

  // make cell a none graded and make sure the total points is zero
  await selectInToolbar(page, "");
  expect(await getTotalPoints(page)).toBe(0);

  // make cell a task again
  await selectInToolbar(page, "task");
  expect(await getTotalPoints(page)).toBe(0);
  await setPoints(page, 2);
  expect(await getTotalPoints(page)).toBe(2);

  // create a new cell
  await createNewCell(page);

  // make it a test cell and check if total points is 3
  await selectInToolbar(page, "tests", 1);
  await setPoints(page, 1, 1);
  await setId(page, "bar", 1);
  expect(await getTotalPoints(page)).toBe(3);

  // delete the first cell
  await deleteCell(page);
  expect(await getTotalPoints(page)).toBe(1);

  // delete the new cell
  await deleteCell(page);
  expect(await getTotalPoints(page)).toBe(0);
});

/*
 * Tests on cell ids
 */
test("cell ids", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  // turn it into a solution cell with an id
  await selectInToolbar(page, "solution");
  await setId(page, "");

  // wait for error on saving with empty id
  await saveCurrentNotebook(page);
  await waitForErrorModal(page);
  await closeErrorModal(page);

  // set correct id
  await setId(page);

  // create a new cell
  await createNewCell(page);

  // make it a test cell and set the label
  await selectInToolbar(page, "tests", 1);
  await setId(page, "foo", 1);

  // wait for error on saving with empty id
  await saveCurrentNotebook(page);
  await waitForErrorModal(page);
  await closeErrorModal(page);
});

/*
 * Tests on task's cell ids
 */
test("task cell ids", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/task.ipynb`);
  } else {
    await openNotebook(page, "task");
  }

  await activateToolbar(page);

  // turn it into a task cell with an id
  await selectInToolbar(page, "task");
  await setId(page, "");

  // wait for error on saving with empty id
  await saveCurrentNotebook(page);
  await waitForErrorModal(page);
  await closeErrorModal(page);

  // set correct id
  await setId(page);

  // create a new cell
  await createNewCell(page);

  // make it a test cell and set the label
  await selectInToolbar(page, "task", 1);
  await setId(page, "foo", 1);

  // wait for error on saving with empty id
  await saveCurrentNotebook(page);
  await waitForErrorModal(page);
  await closeErrorModal(page);
});

/*
 * Test attributing negative points
 */
test("negative points", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  // make sure the total points is zero
  expect(await getTotalPoints(page)).toBe(0);

  // make it autograder tests and set the points to two
  await selectInToolbar(page, "tests");
  await setPoints(page, 2);
  await setId(page);
  expect(await getTotalPoints(page)).toBe(2);
  expect(await getCellMetadata(page)).toHaveProperty("points", 2);

  // set the points to negative one
  await setPoints(page, -1);
  expect(await getTotalPoints(page)).toBe(0);
  expect(await getCellMetadata(page)).toHaveProperty("points", 0);
});

/*
 * Test attributing negative points on task's cell
 */
test("task negative points", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/task.ipynb`);
  } else {
    await openNotebook(page, "task");
  }

  await activateToolbar(page);

  // make sure the total points is zero
  expect(await getTotalPoints(page)).toBe(0);

  // make it autograder tests and set the points to two
  await selectInToolbar(page, "task");
  await setPoints(page, 2);
  await setId(page);
  expect(await getTotalPoints(page)).toBe(2);
  expect(await getCellMetadata(page)).toHaveProperty("points", 2);

  // set the points to negative one
  await setPoints(page, -1);
  expect(await getTotalPoints(page)).toBe(0);
  expect(await getCellMetadata(page)).toHaveProperty("points", 0);
});

/*
 * Test nbgrader schema version
 */
test("schema version", async ({ page, tmpPath }) => {
  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/old-schema.ipynb`);
  } else {
    await openNotebook(page, "old-schema");
  }

  // activate toolbar should show an error modal
  await activateToolbar(page);
  await waitForErrorModal(page);
  await closeErrorModal(page);
});

/*
 * Test an invalid cell type
 */
test("invalid nbgrader cell type", async ({ page, tmpPath }) => {

  if (isNotebook) {
    await page.goto(`notebooks/${tmpPath}/blank.ipynb`);
  } else {
    await openNotebook(page, "blank");
  }

  await activateToolbar(page);

  await selectInToolbar(page, "solution");

  // make the cell a solution cell
  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", true);
  expect(metadata).toHaveProperty("grade", false);
  expect(metadata).toHaveProperty("locked", false);

  await expect(page.locator(".nbgrader-CellId")).toBeVisible();

  expect((await getCellMetadata(page))["grade_id"]).toEqual(
    expect.stringMatching("^cell-")
  );
  await setId(page);
  expect(await getCellMetadata(page)).toHaveProperty("grade_id", "foo");

  await saveCurrentNotebook(page);

  // change the cell to markdown
  await page.locator(".jp-Cell .jp-InputArea-prompt").first().click();
  await page.keyboard.press("m");

  var metadata = await getCellMetadata(page);
  expect(metadata).toHaveProperty("solution", false);
  expect(metadata).toHaveProperty("grade", false);
  expect(metadata).toHaveProperty("locked", false);
  expect(metadata).toHaveProperty("grade_id", "foo");
});
