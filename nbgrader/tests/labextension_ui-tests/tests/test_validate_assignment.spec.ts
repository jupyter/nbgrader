import { test, galata, IJupyterLabPageFixture } from '@jupyterlab/galata';
import { expect } from '@playwright/test';
import * as path from 'path';

import {
    wait_for_success_modal,
    close_success_modal,
    wait_for_error_modal,
    close_error_modal
} from "./test_utils";

test.use({ tmpPath: 'nbgrader-create-assignments-test' });

const nb_files = [
    "data.txt",
    "submitted-changed.ipynb",
    "submitted-unchanged.ipynb",
    "submitted-grade-cell-changed.ipynb",
    "submitted-locked-cell-changed.ipynb",
    "open_relative_file.ipynb",
    "submitted-grade-cell-type-changed.ipynb",
    "submitted-answer-cell-type-changed.ipynb"
];

/*
 * copy notebook files before each test
 */
test.beforeEach(async ({ baseURL, tmpPath }) => {
    const contents = galata.newContentsHelper(baseURL);
    nb_files.forEach(elem => {
         contents.uploadFile(
            path.resolve(
                __dirname,
                `../files/${elem}`
            ),
            `${tmpPath}/${elem}`
        );
    });
});

/*
 * delete temp directory at the end of test
 */
test.afterAll(async ({ baseURL, tmpPath }) => {
    const contents = galata.newContentsHelper(baseURL);
    await contents.deleteDirectory(tmpPath);

    if (contents.fileExists("nbgrader_config.py")) contents.deleteFile("nbgrader_config.py");
    contents.uploadFile(path.resolve(__dirname, "../files/nbgrader_config.py"), "nbgrader_config.py");
});


/*
 * Open a notebook file and wait for validate button
 */
const open_notebook = async (page:IJupyterLabPageFixture, notebook:string) => {

    var filename = notebook + '.ipynb';
    var tab_count = await page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab").count();
    await page.locator(`#filebrowser .jp-DirListing-content .jp-DirListing-itemText span:text-is('${filename}')`).dblclick();
    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(tab_count + 1);
    await page.waitForSelector(".jp-Notebook-cell");

    await page.waitForSelector("button.validate-button")
}

/*
 * Test validation success
 */
test('Validation success', async ({
    page
  }) => {

    // open the notebook
    await open_notebook(page, "submitted-changed");

    // click on validate, and expect a success modal
    await page.locator('button.validate-button').click();
    await wait_for_success_modal(page);

    // close the modal
    await close_success_modal(page);

});

/*
 * Test validation failure
 */
test('Validation failure', async ({
    page
  }) => {

    // open the notebook
    await open_notebook(page, "submitted-unchanged");

    // click on validate, and expect an error modal
    await page.locator('button.validate-button').click();
    await wait_for_error_modal(page);

    await page.waitForSelector('.nbgrader-ErrorDialog .validation-failed');

    // close the modal
    await close_error_modal(page);

});


/*
 * Test validation with grade cell changed
 */
test('Validation grade cell changed', async ({
    page
  }) => {

    // open the notebook
    await open_notebook(page, "submitted-grade-cell-changed");

    // click on validate, and expect an error modal
    await page.locator('button.validate-button').click();
    await wait_for_error_modal(page);

    await page.waitForSelector('.nbgrader-ErrorDialog .validation-changed');

    // close the modal
    await close_error_modal(page);

});

/*
 * Test validation with locked cell changed
 */
test('Validation locked cell changed', async ({
    page
  }) => {

    // open the notebook
    await open_notebook(page, "submitted-locked-cell-changed");

    // click on validate, and expect an error modal
    await page.locator('button.validate-button').click();
    await wait_for_error_modal(page);

    await page.waitForSelector('.nbgrader-ErrorDialog .validation-changed');

    // close the modal
    await close_error_modal(page);

});

/*
 * Test validation opening relative file
 */
test('Validation open relative file', async ({
    page
  }) => {

    // open the notebook
    await open_notebook(page, "open_relative_file");

    // click on validate, and expect a success modal
    await page.locator('button.validate-button').click();
    await wait_for_success_modal(page);

    await page.waitForSelector('.nbgrader-SuccessDialog .validation-success');

    // close the modal
    await close_success_modal(page);

});

/*
 * Test validation with grade cell type changed
 */
test('Validation grade cell type changed', async ({
    page
  }) => {

    // open the notebook
    await open_notebook(page, "submitted-grade-cell-type-changed");

    // click on validate, and expect an error modal
    await page.locator('button.validate-button').click();
    await wait_for_error_modal(page);

    await page.waitForSelector('.nbgrader-ErrorDialog .validation-type-changed');

    // close the modal
    await close_error_modal(page);

});

/*
* Test validation with answer cell type changed
*/
test('Validation answer cell type changed', async ({
   page
 }) => {

   // open the notebook
   await open_notebook(page, "submitted-answer-cell-type-changed");

   // click on validate, and expect an error modal
   await page.locator('button.validate-button').click();
   await wait_for_error_modal(page);

   await page.waitForSelector('.nbgrader-ErrorDialog .validation-type-changed');

   // close the modal
   await close_error_modal(page);

});
