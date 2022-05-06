import { test, galata, IJupyterLabPageFixture } from '@jupyterlab/galata';
import { expect } from '@playwright/test';
import * as path from 'path';

test.use({ tmpPath: 'nbgrader-create-assignments-test' });

const nb_files = ["blank.ipynb", "task.ipynb", "old-schema.ipynb"]

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

test.afterAll(async ({ baseURL, tmpPath }) => {
    const contents = galata.newContentsHelper(baseURL);
    await contents.deleteDirectory(tmpPath);
  });


const open_notebook = async (page:IJupyterLabPageFixture, notebook:string) => {

    var filename = notebook + '.ipynb';
    var tab_count = await page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab").count();
    await page.locator(`#filebrowser .jp-DirListing-content .jp-DirListing-itemText span:text-is('${filename}')`).dblclick();
    await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(tab_count + 1);
    await page.waitForSelector(".jp-Notebook-cell");

}

const save_current_notebook = async (page:IJupyterLabPageFixture) => {
    return await page.evaluate(async () => {
        var nb = window.jupyterapp.shell.currentWidget;
        await nb.context.save();
    });

    // TODO : ensure metadata has been saved
    // Read local file ?
}

const activate_toolbar = async (page:IJupyterLabPageFixture) => {

    if (await page.locator('.nbgrader-NotebookWidget').count() > 0){
        if (page.locator('.nbgrader-NotebookWidget').isVisible()) {
            return;
        }
    }
    await page.mouse.click(1010, 160);
    await expect(page.locator('.nbgrader-NotebookWidget')).toBeVisible();
}

const get_cell_metadata = async (page:IJupyterLabPageFixture, cell_number:Number=0) => {

    return await page.evaluate((cell_num) => {
        var nb = window.jupyterapp.shell.currentWidget;
        return nb.model.cells.get(cell_num).metadata.get("nbgrader");
    }, cell_number);
}

const set_points = async (page:IJupyterLabPageFixture, points:number=0, index:number=0) => {
    await page.locator(".nbgrader-CellPoints input").nth(index).fill(points.toString());
    await page.keyboard.press("Enter");
}

const set_id = async (page:IJupyterLabPageFixture, id:string="foo", index:number=0) => {
    await page.locator(".nbgrader-CellId input").nth(index).fill(id);
    await page.keyboard.press("Enter");
}

const select_in_toolbar = async(page:IJupyterLabPageFixture, text:string, index:number=0) => {
    var select = page.locator('.nbgrader-NotebookWidget select').nth(index);
    await select.selectOption(text);
}

const get_total_points = async (page:IJupyterLabPageFixture, index:number=0) => {
    return parseFloat(await page.locator('.nbgrader-TotalPointsInput').nth(0).inputValue());
}

const wait_for_modal = async (page:IJupyterLabPageFixture) => {
    await expect(page.locator(".nbgrader-ErrorDialog")).toHaveCount(1);
}

const close_modal = async (page:IJupyterLabPageFixture) => {
    await page.locator(".nbgrader-ErrorDialog button.jp-Dialog-button").click();
}

const create_new_cell = async (page:IJupyterLabPageFixture, after:number=0) => {
    await page.locator('.jp-Cell .jp-InputArea-prompt').nth(after).click();
    await page.keyboard.press('b');
}

const delete_cell = async (page:IJupyterLabPageFixture, index:number=0) => {
    await page.locator('.jp-Cell .jp-InputArea-prompt').nth(index).click();
    await page.keyboard.press('d');
    await page.keyboard.press('d');
}

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

    await page.waitForSelector(".nbgrader-CellId");
    await page.waitForSelector(".nbgrader-CellPoints");
    await page.waitForSelector(".nbgrader-LockButton");

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

    await page.waitForSelector(".nbgrader-CellId");
    await page.waitForSelector(".nbgrader-CellPoints");

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

    await page.waitForSelector(".nbgrader-CellId");

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();

    await save_current_notebook(page);
})

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

    await page.waitForSelector(".nbgrader-CellId");
    await page.waitForSelector(".nbgrader-CellPoints");
    await page.waitForSelector(".nbgrader-LockButton");

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

    await page.waitForSelector(".nbgrader-CellId");
    await page.waitForSelector(".nbgrader-CellPoints");
    await page.waitForSelector(".nbgrader-LockButton");

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

    await page.waitForSelector(".nbgrader-CellId");
    await page.waitForSelector(".nbgrader-LockButton");

    expect((await get_cell_metadata(page))['grade_id']).toEqual(expect.stringMatching('^cell\-'));
    await set_id(page);
    expect(await get_cell_metadata(page)).toHaveProperty("grade_id", "foo");

    await save_current_notebook(page);

    await select_in_toolbar(page, '');
    expect(await get_cell_metadata(page)).toBeUndefined();
    await save_current_notebook(page);
})

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

test('task total points', async ({
    page
}) => {

    await open_notebook(page, "task");
    await activate_toolbar(page);

    // make sure the total points is zero
    expect(await get_total_points(page)).toBe(0);

    // make it autograder task and set the points to two
    await select_in_toolbar(page, 'task');
    await set_points(page, 2);
    await set_id(page);
    expect(await get_total_points(page)).toBe(2);

    // make it manually graded
    await select_in_toolbar(page, 'manual');
    expect(await get_total_points(page)).toBe(2);

    // make it a solution make sure the total points is zero
    await select_in_toolbar(page, '');
    expect(await get_total_points(page)).toBe(0);

    // make it task again
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
    await wait_for_modal(page);
    await close_modal(page);

    // set correct id
    await set_id(page);

    // create a new cell
    await create_new_cell(page);

    // make it a test cell and set the label
    await select_in_toolbar(page, 'tests', 1);
    await set_id(page, "foo", 1);

    // wait for error on saving with empty id
    await save_current_notebook(page);
    await wait_for_modal(page);
    await close_modal(page);

})

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
    await wait_for_modal(page);
    await close_modal(page);

    // set correct id
    await set_id(page);

    // create a new cell
    await create_new_cell(page);

    // make it a test cell and set the label
    await select_in_toolbar(page, 'task', 1);
    await set_id(page, "foo", 1);

    // wait for error on saving with empty id
    await save_current_notebook(page);
    await wait_for_modal(page);
    await close_modal(page);

})

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

test('schema version', async ({
    page
}) => {

    await open_notebook(page, "old-schema");

    // activate toolbar should show an error modal
    await activate_toolbar(page);
    await wait_for_modal(page);
    await close_modal(page);

})

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

    await page.waitForSelector(".nbgrader-CellId");

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
