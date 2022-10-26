import { test, galata, IJupyterLabPageFixture } from '@jupyterlab/galata';
import { expect } from '@playwright/test';
import * as path from 'path';

import { wait_for_error_modal, close_error_modal } from "./test_utils";

test.use({
  tmpPath: 'nbgrader-create-assignments-test',
  mockSettings: {
    '@jupyterlab/apputils-extension:notification': {
      fetchNews: 'false'
    }
  }
});

const nb_files = ["blank.ipynb", "task.ipynb", "old-schema.ipynb"];

/*
 * copy notebook files before each test
 */
test.beforeEach(async ({ request, tmpPath }) => {

    if (request === undefined) throw new Error("Request is undefined.");

    const contents = galata.newContentsHelper(request);
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
test.afterAll(async ({ request, tmpPath }) => {

    if (request === undefined) throw new Error("Request is undefined.");

    const contents = galata.newContentsHelper(request);
    await contents.deleteDirectory(tmpPath);

    if (await contents.fileExists("nbgrader_config.py")) contents.deleteFile("nbgrader_config.py");
    contents.uploadFile(path.resolve(__dirname, "../files/nbgrader_config.py"), "nbgrader_config.py");
});


/*
 * Open a notebook file
 */
const open_notebook = async (page:IJupyterLabPageFixture, notebook:string) => {

    var filename = notebook + '.ipynb';
    var tab_count = await page.locator("#jp-main-dock-panel .lm-TabBar-tab").count();
    await page.locator(`#filebrowser .jp-DirListing-content .jp-DirListing-itemText span:text-is('${filename}')`).dblclick();
    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab")).toHaveCount(tab_count + 1);
    await page.waitForSelector(".jp-Notebook-cell");

}

/*
 * Save the current notebook file
 */
const save_current_notebook = async (page:IJupyterLabPageFixture) => {
    return await page.evaluate(async () => {
        var nb = window.jupyterapp.shell.currentWidget;
        await nb.context.save();
    });

    // TODO : ensure metadata has been saved
    // Read local file ?
}

/*
 * Activate assignment toolbar in jupyterlab
 */
const activate_toolbar = async (page:IJupyterLabPageFixture) => {

    if (await page.locator('.nbgrader-NotebookWidget').count() > 0){
        if (await page.locator('.nbgrader-NotebookWidget').isVisible()) {
            return;
        }
    }

    const widget_button = page.locator(".lm-TabBar-tab[title='nbgrader Create Assignment']");
    const button_position = await widget_button.boundingBox();

    if (button_position === null) throw new Error("Cannot get the position of the create assignment button.");

    await page.mouse.click(
        button_position.x + button_position.width/2,
        button_position.y + button_position.height/2
    );

    await expect(page.locator('.nbgrader-NotebookWidget')).toBeVisible();
}

/*
 * Get the nbgrader's metadata of a cell
 */
const get_cell_metadata = async (page:IJupyterLabPageFixture, cell_number:Number=0) => {

    return await page.evaluate((cell_num) => {
        var nb = window.jupyterapp.shell.currentWidget;
        return nb.model.cells.get(cell_num).metadata.get("nbgrader");
    }, cell_number);
}

/*
 * Set points to a notebook cell
 */
const set_points = async (page:IJupyterLabPageFixture, points:number=0, index:number=0) => {
    await page.locator(".nbgrader-CellPoints input").nth(index).fill(points.toString());
    await page.keyboard.press("Enter");
}

/*
 * Set id to a notebook cell
 */
const set_id = async (page:IJupyterLabPageFixture, id:string="foo", index:number=0) => {
    await page.locator(".nbgrader-CellId input").nth(index).fill(id);
    await page.keyboard.press("Enter");
}

/*
 * Select type of assignment of a cell in nbgrader toolbar
 */
const select_in_toolbar = async(page:IJupyterLabPageFixture, text:string, index:number=0) => {
    var select = page.locator('.nbgrader-NotebookWidget select').nth(index);
    await select.selectOption(text);
}

/*
 * Get the total points of an assignment
 */
const get_total_points = async (page:IJupyterLabPageFixture, index:number=0) => {
    return parseFloat(await page.locator('.nbgrader-TotalPointsInput').nth(0).inputValue());
}

/*
 * Create a new cell in current notebook
 */
const create_new_cell = async (page:IJupyterLabPageFixture, after:number=0) => {
    await page.locator('.jp-Cell .jp-InputArea-prompt').nth(after).click();
    await page.keyboard.press('b');
}

/*
 * Delete a cell in current notebook
 */
const delete_cell = async (page:IJupyterLabPageFixture, index:number=0) => {
    await page.locator('.jp-Cell .jp-InputArea-prompt').nth(index).click();
    await page.keyboard.press('d');
    await page.keyboard.press('d');
}

/*
 * Test manipulating a manually graded cell
 */
test('manual cell', async ({
    page
  }) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    expect(await get_cell_metadata(page)).toBeUndefined();

    await select_in_toolbar(page, 'manual');

    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', true);
    expect(metadata).toHaveProperty('grade', true);
    expect(metadata).toHaveProperty('locked', false);

    await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

    await set_points(page, 2);
    expect(await get_cell_metadata(page)).toHaveProperty('points', 2);

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();

    await save_current_notebook(page);
});

/*
 * Test manipulating a task cell
 */
test('task cell', async ({
    page
}) => {

    await open_notebook(page, "task");
    await activate_toolbar(page);

    expect(await get_cell_metadata(page)).toBeUndefined();

    await select_in_toolbar(page, 'task');

    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', false);
    expect(metadata).toHaveProperty('grade', false);
    expect(metadata).toHaveProperty('locked', true);

    await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();

    await set_points(page, 2);
    expect(await get_cell_metadata(page)).toHaveProperty('points', 2);

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();

    await save_current_notebook(page);
})

/*
 * Test manipulating a solution graded cell
 */
test('solution cell', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    expect(await get_cell_metadata(page)).toBeUndefined();

    await select_in_toolbar(page, 'solution');

    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', true);
    expect(metadata).toHaveProperty('grade', false);
    expect(metadata).toHaveProperty('locked', false);

    await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();

    await save_current_notebook(page);
})

/*
 * Test manipulating a test graded cell
 */
test('tests cell', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    expect(await get_cell_metadata(page)).toBeUndefined();

    await select_in_toolbar(page, 'tests');

    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', false);
    expect(metadata).toHaveProperty('grade', true);
    expect(metadata).toHaveProperty('locked', true);

    await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

    await set_points(page, 2);
    expect(await get_cell_metadata(page)).toHaveProperty('points', 2);

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();

    await save_current_notebook(page);
})

/*
 * Test converting cell's type
 */
test('tests to solution cell', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    expect(await get_cell_metadata(page)).toBeUndefined();

    await select_in_toolbar(page, 'tests');

    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', false);
    expect(metadata).toHaveProperty('grade', true);
    expect(metadata).toHaveProperty('locked', true);

    await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-CellPoints >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

    await set_points(page, 2);
    expect(await get_cell_metadata(page)).toHaveProperty('points', 2);

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, 'solution');
    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', true);
    expect(metadata).toHaveProperty('grade', false);
    expect(metadata).toHaveProperty('locked', false);
    expect(metadata['points']).toBeUndefined();
    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();
    await save_current_notebook(page);
})

/*
 * Tests on locked cell
 */
test('locked cell', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    expect(await get_cell_metadata(page)).toBeUndefined();

    await select_in_toolbar(page, 'readonly');

    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', false);
    expect(metadata).toHaveProperty('grade', false);
    expect(metadata).toHaveProperty('locked', true);

    await expect(page.locator(".nbgrader-CellId >> nth=0")).toBeVisible();
    await expect(page.locator(".nbgrader-LockButton >> nth=0")).toBeVisible();

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();
    await save_current_notebook(page);
})

/*
 * Test focus using TAB key
 */
test('tab key', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    // make the cell manually grading
    await select_in_toolbar(page, 'manual');

    // focus on cell type
    await page.locator(".nbgrader-CellType select").focus();
    await expect(page.locator('.nbgrader-CellType select')).toBeFocused();

    // press tab and focus on ID input
    await page.keyboard.press("Tab");
    await expect(page.locator('.nbgrader-CellId input')).toBeFocused();

    // press tab again and focus on points input
    await page.keyboard.press("Tab");
    await expect(page.locator('.nbgrader-CellPoints input')).toBeFocused();

})

/*
 * Test the total points of a notebook
 */
test('total points', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    // make sure the total points is zero
    expect(await get_total_points(page)).toBe(0);

    // make it autograder tests and set the points to two
    await select_in_toolbar(page, 'tests');
    await set_points(page, 2);
    await set_id(page);
    expect(await get_total_points(page)).toBe(2);

    // make it manually graded
    await select_in_toolbar(page, 'manual');
    expect(await get_total_points(page)).toBe(2);

    // make it a solution make sure the total points is zero
    await select_in_toolbar(page, 'solution');
    expect(await get_total_points(page)).toBe(0);

    // make it task
    await select_in_toolbar(page, 'task');
    expect(await get_total_points(page)).toBe(0);
    await set_points(page, 2);
    expect(await get_total_points(page)).toBe(2);

    // create a new cell
    await create_new_cell(page)

    // make it a test cell and check if total points is 3
    await select_in_toolbar(page, 'tests', 1);
    await set_points(page, 1, 1)
    await set_id(page, "bar", 1);
    expect(await get_total_points(page)).toBe(3);

    // delete the first cell
    await delete_cell(page);
    expect(await get_total_points(page)).toBe(1);

    // delete the new cell
    await delete_cell(page);
    expect(await get_total_points(page)).toBe(0);

})

/*
 * Test the total points of a notebook using task cell
 */
test('task total points', async ({
    page
}) => {

    await open_notebook(page, "task");
    await activate_toolbar(page);

    // make sure the total points is zero
    expect(await get_total_points(page)).toBe(0);

    // make cell autograded task and set the points to two
    await select_in_toolbar(page, 'task');
    await set_points(page, 2);
    await set_id(page);
    expect(await get_total_points(page)).toBe(2);

    // make cell manually graded
    await select_in_toolbar(page, 'manual');
    expect(await get_total_points(page)).toBe(2);

    // make cell a none graded and make sure the total points is zero
    await select_in_toolbar(page, '');
    expect(await get_total_points(page)).toBe(0);

    // make cell a task again
    await select_in_toolbar(page, 'task');
    expect(await get_total_points(page)).toBe(0);
    await set_points(page, 2);
    expect(await get_total_points(page)).toBe(2);

    // create a new cell
    await create_new_cell(page)

    // make it a test cell and check if total points is 3
    await select_in_toolbar(page, 'tests', 1);
    await set_points(page, 1, 1)
    await set_id(page, "bar", 1);
    expect(await get_total_points(page)).toBe(3);

    // delete the first cell
    await delete_cell(page);
    expect(await get_total_points(page)).toBe(1);

    // delete the new cell
    await delete_cell(page);
    expect(await get_total_points(page)).toBe(0);

})

/*
 * Tests on cell ids
 */
test('cell ids', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    // turn it into a solution cell with an id
    await select_in_toolbar(page, 'solution');
    await set_id(page, "");

    // wait for error on saving with empty id
    await save_current_notebook(page);
    await wait_for_error_modal(page);
    await close_error_modal(page);

    // set correct id
    await set_id(page);

    // create a new cell
    await create_new_cell(page);

    // make it a test cell and set the label
    await select_in_toolbar(page, 'tests', 1);
    await set_id(page, "foo", 1);

    // wait for error on saving with empty id
    await save_current_notebook(page);
    await wait_for_error_modal(page);
    await close_error_modal(page);

})

/*
 * Tests on task's cell ids
 */
test('task cell ids', async ({
    page
}) => {

    await open_notebook(page, "task");
    await activate_toolbar(page);

    // turn it into a task cell with an id
    await select_in_toolbar(page, 'task');
    await set_id(page, "");

    // wait for error on saving with empty id
    await save_current_notebook(page);
    await wait_for_error_modal(page);
    await close_error_modal(page);

    // set correct id
    await set_id(page);

    // create a new cell
    await create_new_cell(page);

    // make it a test cell and set the label
    await select_in_toolbar(page, 'task', 1);
    await set_id(page, "foo", 1);

    // wait for error on saving with empty id
    await save_current_notebook(page);
    await wait_for_error_modal(page);
    await close_error_modal(page);

})

/*
 * Test attributing negative points
 */
test('negative points', async ({
    page
}) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    // make sure the total points is zero
    expect(await get_total_points(page)).toBe(0);

     // make it autograder tests and set the points to two
    await select_in_toolbar(page, 'tests');
    await set_points(page, 2);
    await set_id(page);
    expect(await get_total_points(page)).toBe(2);
    expect(await get_cell_metadata(page)).toHaveProperty("points", 2);

    // set the points to negative one
    await set_points(page, -1);
    expect(await get_total_points(page)).toBe(0);
    expect(await get_cell_metadata(page)).toHaveProperty("points", 0);

})

/*
 * Test attributing negative points on task's cell
 */
test('task negative points', async ({
    page
}) => {

    await open_notebook(page, "task");
    await activate_toolbar(page);

    // make sure the total points is zero
    expect(await get_total_points(page)).toBe(0);

     // make it autograder tests and set the points to two
    await select_in_toolbar(page, 'task');
    await set_points(page, 2);
    await set_id(page);
    expect(await get_total_points(page)).toBe(2);
    expect(await get_cell_metadata(page)).toHaveProperty("points", 2);

    // set the points to negative one
    await set_points(page, -1);
    expect(await get_total_points(page)).toBe(0);
    expect(await get_cell_metadata(page)).toHaveProperty("points", 0);

})

/*
 * Test nbgrader schema version
 */
test('schema version', async ({
    page
}) => {

    await open_notebook(page, "old-schema");

    // activate toolbar should show an error modal
    await activate_toolbar(page);
    await wait_for_error_modal(page);
    await close_error_modal(page);

})

/*
 * Test an invalid cell type
 */
test('invalid nbgrader cell type', async ({
    page
    }) => {

    await open_notebook(page, "blank");
    await activate_toolbar(page);

    await select_in_toolbar(page, 'solution');

    // make the cell a solution cell
    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', true);
    expect(metadata).toHaveProperty('grade', false);
    expect(metadata).toHaveProperty('locked', false);

    await expect(page.locator(".nbgrader-CellId")).toBeVisible();

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty('grade_id', 'foo');

    await save_current_notebook(page);

    // change the cell to markdown
    await page.locator('.jp-Cell .jp-InputArea-prompt').first().click();
    await page.keyboard.press('m');

    var metadata = await get_cell_metadata(page);
    expect(metadata).toHaveProperty('solution', false);
    expect(metadata).toHaveProperty('grade', false);
    expect(metadata).toHaveProperty('locked', false);
    expect(metadata).toHaveProperty('grade_id', "foo");

});
