import { test, galata, IJupyterLabPageFixture } from '@jupyterlab/galata';
import { expect, Locator, Page } from '@playwright/test';
import {
  execute_command,
  create_env,
  wait_for_error_modal,
  close_error_modal,
  wait_for_success_modal,
  close_success_modal} from './test_utils';

import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

test.use({ tmpPath: 'nbgrader-assignment-list-test' });

var exchange_dir:string;
var cache_dir: string;

const is_windows = os.platform().startsWith('win')

/*
 * Create environment
 */
test.beforeEach(async ({ baseURL, tmpPath }) => {

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

  const contents = galata.newContentsHelper(baseURL);
  await contents.deleteDirectory(tmpPath);

  if (contents.fileExists("nbgrader_config.py")) contents.deleteFile("nbgrader_config.py");
  contents.uploadFile(path.resolve(__dirname, "../files/nbgrader_config.py"), "nbgrader_config.py");
});


/*
 * Create a nbgrader file system and modify config
 */
const add_courses = async (page:IJupyterLabPageFixture, baseURL:string, tmpPath:string) => {

  const contents = galata.newContentsHelper(baseURL);

  // copy files from the user guide
  const source = path.resolve(__dirname, "..", "..", "..", "docs", "source", "user_guide", "source");
  await contents.uploadDirectory(source, `${tmpPath}/source`);
  await contents.renameDirectory(`${tmpPath}/source/ps1`, `${tmpPath}/source/Problem Set 1`);
  await contents.renameFile(`${tmpPath}/source/Problem Set 1/problem1.ipynb`, `${tmpPath}/source/Problem Set 1/Problem 1.ipynb`)
  await contents.renameFile(`${tmpPath}/source/Problem Set 1/problem2.ipynb`, `${tmpPath}/source/Problem Set 1/Problem 2.ipynb`)
  await contents.createDirectory(`${tmpPath}/source/ps.01`);
  await contents.uploadFile(
    path.resolve(__dirname, '..', 'files', 'empty.ipynb'),
    `${tmpPath}/source/ps.01/problem 1.ipynb`
  )

  const jupyter_config_content = await page.locator('#jupyter-config-data').textContent();
  const rootDir = JSON.parse(jupyter_config_content)['serverRoot'];

  // Necessary to generate and release assignments
  fs.copyFileSync(path.resolve(rootDir, "nbgrader_config.py"), path.resolve(rootDir, tmpPath, "nbgrader_config.py"));
}

/*
 * Open the assignment list tab
 */
const open_assignment_list = async (page:IJupyterLabPageFixture) => {

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(1);

  await page.keyboard.press('Control+Shift+c');
  await page.locator('#modal-command-palette li[data-command="nbgrader:assignment-list"]').click();

  await expect(page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab")).toHaveCount(2);

  var tabs = page.locator("#jp-main-dock-panel .lm-TabBar-tab.p-TabBar-tab");
  var newTab_label = tabs.last().locator(".lm-TabBar-tabLabel.p-TabBar-tabLabel");
  await expect(newTab_label).toHaveText("Assignments");

}

/*
 * Ensure that list of assignment has been loaded for a specific name ("released", "fetched", "submitted")
 */
const wait_for_list = async(page:IJupyterLabPageFixture, name:string, nb_rows:number): Promise<Locator> => {
  await expect(page.locator(`#${name}_assignments_list_loading`)).not.toBeVisible();
  await expect(page.locator(`#${name}_assignments_list_placeholder`)).not.toBeVisible();
  await expect(page.locator(`#${name}_assignments_list_error`)).not.toBeVisible();

  const rows = page.locator(`#${name}_assignments_list > .list_item`)
  await expect(rows).toHaveCount(nb_rows);
  return rows;
}

/*
 * Select a course in dropdown list
 */
const select_course = async(page:IJupyterLabPageFixture, course:string) => {
  await page.locator('#course_list_dropdown').click();
  await page.locator(`#course_list > li :text("${course}")`).click();
  await expect(page.locator('#course_list_default')).toHaveText(course);
}

/*
 * Expand a fetched assignment
 */
const expand_fetched = async(page:IJupyterLabPageFixture, assignment:string, item_id:string): Promise<Locator> => {
  await page.locator(`#fetched_assignments_list a:text("${assignment}")`).click();
  await page.waitForSelector(`${item_id}.collapse.in`);

  const rows = page.locator(`${item_id} .list_item`);
  for (var i=1; i < await rows.count(); i++){
    expect(rows.nth(i)).toBeVisible();
  }
  return rows;
}

/*
 * Collapse an expended fetched assignment
 */
const collapse_fetched = async(page:IJupyterLabPageFixture, assignment:string, item_id:string) => {
  await page.locator(`#fetched_assignments_list a:text("${assignment}")`).click();
  await expect(page.locator(`${item_id}.collapse`)).not.toHaveClass('in');
}

/*
 * Test showing assignment list
 */
test('Show assignment list', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // Wait for DOM of each status
    await page.waitForSelector('#released_assignments_list');
    await page.waitForSelector('#fetched_assignments_list');
    await page.waitForSelector('#submitted_assignments_list');

    // release an assignment
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");

    // refresh assignments
    await page.locator('#refresh_assignments_list').click();

    // expect finding the released assignment
    const rows = await wait_for_list(page, 'released', 1);
    expect(rows.first().locator('.item_name')).toHaveText("Problem Set 1");
    expect(rows.first().locator('.item_course')).toHaveText("abc101");

  });

/*
 * Test multiple released assignments
 */
test('Multiple released assignments', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release two assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignments
    await page.locator('#refresh_assignments_list').click();

    // select a course
    await select_course(page, 'xyz 200');

    // expect finding the released assignment for selected course
    const rows = await wait_for_list(page, 'released', 1);
    expect(rows.first().locator('.item_name')).toHaveText("ps.01");
    expect(rows.first().locator('.item_course')).toHaveText("xyz 200");

  });

/*
 * Test fetch assignment
 */
test('Fetch assignments', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release some assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignment list
    await page.locator('#refresh_assignments_list').click();

    // select one course
    await select_course(page, 'xyz 200');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click()

    // check that there is only one fetched
    rows = await wait_for_list(page, 'fetched', 1);
    expect(rows.first().locator('.item_name').first()).toHaveText("ps.01");
    expect(rows.first().locator('.item_course').first()).toHaveText("xyz 200");

    // check that the directory has been created
    const contents = galata.newContentsHelper(baseURL);
    expect(contents.directoryExists('ps.01'));

    // expand assignment notebooks
    rows = await expand_fetched(page, "ps.01", "#nbgrader-xyz_200-ps01");
    await expect(rows).toHaveCount(2);
    await expect(rows.last().locator('.item_name')).toHaveText('problem 1');

    // collapse assignments notebooks
    await collapse_fetched(page, "ps.01", "#nbgrader-xyz_200-ps01");

  });

/*
 * Test submit assignment
 */
test('Submit assignments', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    // create directories and config files, and open assignment_list tab
    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release some assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignment list
    await page.locator('#refresh_assignments_list').click();

    // select one course
    await select_course(page, 'xyz 200');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click();

    // check that there is only one fetched and submit
    rows = await wait_for_list(page, 'fetched', 1);
    await rows.first().locator('.item_status button:text("Submit")').click();

    // check that there is only one submitted
    rows = await wait_for_list(page, 'submitted', 1);
    expect(rows.first().locator('.item_name').first()).toHaveText("ps.01");
    expect(rows.first().locator('.item_course').first()).toHaveText("xyz 200");

    // check again that there is only one submitted for that course
    rows = page.locator('#nbgrader-xyz_200-ps01-submissions > .list_item');
    // the first row should be empty
    expect(rows).toHaveCount(2);

    // submit a second time
    rows = await wait_for_list(page, 'fetched', 1);
    await rows.first().locator('.item_status button:text("Submit")').click();

    // check there are two submitted (the first row is empty)
    await expect(page.locator('#nbgrader-xyz_200-ps01-submissions > .list_item')).toHaveCount(3);
    rows = page.locator('#nbgrader-xyz_200-ps01-submissions > .list_item');

    const timestamp1 = rows.nth(1).locator(".item_name").textContent();
    const timestamp2 = rows.nth(2).locator(".item_name").textContent();
    expect(timestamp1 != timestamp2);

  });

/*
 * Test submitting assignment without notebook
 */
test('submit assignment missing notebook', async ({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    // create directories and config files, and open assignment_list tab
    const rootDir = await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release some assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignment list
    await page.locator('#refresh_assignments_list').click();

    // select one course
    await select_course(page, 'xyz 200');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click();

    // check that there is only one fetched and submit
    rows = await wait_for_list(page, 'fetched', 1);
    await rows.first().locator('.item_status button:text("Submit")').click();

    // check that there is only one submitted
    rows = await wait_for_list(page, 'submitted', 1);
    expect(rows.first().locator('.item_name').first()).toHaveText("ps.01");
    expect(rows.first().locator('.item_course').first()).toHaveText("xyz 200");
    rows = page.locator('#nbgrader-xyz_200-ps01-submissions > .list_item');
    expect(rows).toHaveCount(2);

    // rename the assignment notebook file
    const contents = galata.newContentsHelper(baseURL);
    expect(await contents.fileExists(`${tmpPath}/ps.01/problem 1.ipynb`));
    await contents.renameFile(
      `${tmpPath}/ps.01/problem 1.ipynb`,
      `${tmpPath}/ps.01/my problem 1.ipynb`
    );

    // submit again and check it has submitted
    rows = await wait_for_list(page, 'fetched', 1);
    await rows.first().locator('.item_status button:text("Submit")').click();
    rows = await wait_for_list(page, 'submitted', 1);
    expect(rows.first().locator('.item_name').first()).toHaveText("ps.01");
    expect(rows.first().locator('.item_course').first()).toHaveText("xyz 200");
    rows = page.locator('#nbgrader-xyz_200-ps01-submissions > .list_item');
    expect(rows).toHaveCount(3);

    const timestamp1 = rows.nth(1).locator(".item_name").textContent();
    const timestamp2 = rows.nth(2).locator(".item_name").textContent();
    expect(timestamp1 != timestamp2);

    // Set strict flag
    fs.appendFileSync(path.resolve(rootDir, tmpPath, "nbgrader_config.py"), 'c.ExchangeSubmit.strict = True');

    // submit again and check that nothing changes
    rows = await wait_for_list(page, 'fetched', 1);
    await rows.first().locator('.item_status button:text("Submit")').click();

    // wait for error modal and close it
    await wait_for_error_modal(page);
    await close_error_modal(page);

    // check that nothing has change in submitted list
    rows = await wait_for_list(page, 'submitted', 1);
    expect(rows.first().locator('.item_name').first()).toHaveText("ps.01");
    expect(rows.first().locator('.item_course').first()).toHaveText("xyz 200");
    rows = page.locator('#nbgrader-xyz_200-ps01-submissions > .list_item');
    expect(rows).toHaveCount(3);

});

/*
 * Test fetch a second assignment
 */
test('Fetch a second assignment', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release some assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignment list
    await page.locator('#refresh_assignments_list').click();

    // select one course
    await select_course(page, 'xyz 200');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click()

    // select the other course
    await select_course(page, 'abc101');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click()

    // check that there is only one fetched
    rows = await wait_for_list(page, 'fetched', 1);
    expect(rows.first().locator('.item_name').first()).toHaveText("Problem Set 1");
    expect(rows.first().locator('.item_course').first()).toHaveText("abc101");

    // check that the directory has been created
    const contents = galata.newContentsHelper(baseURL);
    expect(contents.directoryExists('Problem Set 1'));

    // expand assignment notebooks
    rows = await expand_fetched(page, "Problem Set 1", "#nbgrader-abc101-Problem_Set_1");
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(1).locator('.item_name')).toHaveText('Problem 1');
    await expect(rows.last().locator('.item_name')).toHaveText('Problem 2');

    // collapse assignments notebooks
    await collapse_fetched(page, "Problem Set 1", "#nbgrader-abc101-Problem_Set_1");

  });

/*
 * Test submit another assignment
 */
test('Submit another assignments', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    // create directories and config files, and open assignment_list tab
    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release some assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignment list
    await page.locator('#refresh_assignments_list').click();

    // select one course
    await select_course(page, 'abc101');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click();

    // check that there is only one fetched and submit
    rows = await wait_for_list(page, 'fetched', 1);
    await rows.first().locator('.item_status button:text("Submit")').click();

    // check that there is only one submitted
    rows = await wait_for_list(page, 'submitted', 1);
    expect(rows.first().locator('.item_name').first()).toHaveText("Problem Set 1");
    expect(rows.first().locator('.item_course').first()).toHaveText("abc101");

    // check again that there is only one submitted for that course
    rows = page.locator('#nbgrader-abc101-Problem_Set_1-submissions > .list_item');
    // the first row should be empty
    expect(rows).toHaveCount(2);

  });

/*
 * Test validate assignment
 */
test('Validate OK', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    // create directories and config files, and open assignment_list tab
    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release some assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignment list
    await page.locator('#refresh_assignments_list').click();

    // select one course
    await select_course(page, 'xyz 200');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click();

    // check that there is only one fetched and submit
    rows = await wait_for_list(page, 'fetched', 1);

    // expand assignment notebooks
    rows = await expand_fetched(page, "ps.01", "#nbgrader-xyz_200-ps01");
    await expect(rows).toHaveCount(2);
    await expect(rows.last().locator('.item_name')).toHaveText('problem 1');

    // Click on validate
    await rows.last().locator('.item_status button:text("Validate")').click()

    await wait_for_success_modal(page);
    await close_success_modal(page);

});

/*
 * Test validation failure
 */
test('Validate failure', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    // create directories and config files, and open assignment_list tab
    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);
    await open_assignment_list(page);

    // release some assignments
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");
    await execute_command("nbgrader generate_assignment 'ps.01' --force");
    await execute_command("nbgrader release_assignment 'ps.01' --course 'xyz 200' --force");

    // refresh assignment list
    await page.locator('#refresh_assignments_list').click();

    // select one course
    await select_course(page, 'abc101');

    // check that there is only one released, and fetch it
    var rows = await wait_for_list(page, 'released', 1);
    await rows.first().locator('.item_status button').click();

    // check that there is only one fetched and submit
    rows = await wait_for_list(page, 'fetched', 1);

    // expand assignment notebooks
    rows = await expand_fetched(page, "Problem Set 1", "#nbgrader-abc101-Problem_Set_1");
    await expect(rows).toHaveCount(3);
    await expect(rows.nth(1).locator('.item_name')).toHaveText('Problem 1');
    await expect(rows.last().locator('.item_name')).toHaveText('Problem 2');

    // Click on validate
    await rows.last().locator('.item_status button:text("Validate")').click()
    await wait_for_error_modal(page);
    await close_error_modal(page);

});

/*
 * Test missing exchange directory
 */
test('Missing exchange directory', async({
  page,
  baseURL,
  tmpPath
  }) => {

    test.skip(is_windows, 'This feature is not implemented for Windows');

    // create directories and config files
    await create_env(page, tmpPath, exchange_dir, cache_dir, is_windows);
    await add_courses(page, baseURL, tmpPath);

    // delete exchange directory
    fs.rmSync(exchange_dir, { recursive: true, force: true });

    // open assignment_list tab
    await open_assignment_list(page);

    // Expecting error on lists and dropdown
    await expect(page.locator(`#released_assignments_list_error`)).toBeVisible();
    await expect(page.locator(`#fetched_assignments_list_error`)).toBeVisible();
    await expect(page.locator(`#submitted_assignments_list_error`)).toBeVisible();

    await expect(page.locator('#course_list_default')).toHaveText("Error fetching courses!");

    // create exchange directory again
    fs.mkdtempSync(exchange_dir);

    // release assignment
    await execute_command("nbgrader generate_assignment 'Problem Set 1' --force");
    await execute_command("nbgrader release_assignment 'Problem Set 1' --course 'abc101' --force");

    // refresh assignment list and expect retrieving released assignment
    await page.locator('#refresh_assignments_list').click();
    const rows = await wait_for_list(page, 'released', 1);
    expect(rows.first().locator('.item_name')).toHaveText("Problem Set 1");
    expect(rows.first().locator('.item_course')).toHaveText("abc101");

});
