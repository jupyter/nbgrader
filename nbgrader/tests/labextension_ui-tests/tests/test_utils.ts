import { IJupyterLabPageFixture } from "@jupyterlab/galata"
import { expect } from '@playwright/test';
import { exec } from "child_process";
import { promisify } from 'util';

import * as path from 'path';
import * as fs from 'fs';

const async_exec = promisify(exec)


export const execute_command = async (command: string) => {
  const { stdout, stderr } = await async_exec(command);
  if (stderr) {
    if (stderr.includes("ERROR")){
      console.log(`stderr: ${stderr}`);
      throw new Error(`ERROR in command : ${command}\n${stderr}`);
    }
  }
  return stdout;
}

/*
 * Create a copy of default config file, append exchange directories to config file, and populate database
 */
export const create_env = async (
  page:IJupyterLabPageFixture,
  tmpPath:string,
  exchange_dir:string,
  cache_dir:string
  ): Promise<string> => {

  var content = await page.locator('#jupyter-config-data').textContent();
  const rootDir = JSON.parse(content)['serverRoot'];

  /* Add config_file to jupyter root directory, and change to that directory.
  TODO : test on windows, the config file may change (see nbextension test)
  */
  try {

    var text_to_append = `
c.Exchange.root = "${exchange_dir}"
c.Exchange.cache = "${cache_dir}"
c.Exchange.assignment_dir = "${path.resolve(rootDir, tmpPath)}"
c.CourseDirectory.root = "${path.resolve(rootDir, tmpPath)}"
c.CourseDirectory.db_url = "sqlite:///${path.resolve(rootDir, tmpPath, 'gradebook.db')}"

`;

    fs.appendFileSync(path.resolve(rootDir, "nbgrader_config.py"), text_to_append);
    process.chdir(rootDir);
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

  return rootDir;
}

/*
 * Wait for error modal
 */
export const wait_for_error_modal = async (page:IJupyterLabPageFixture) => {
  await expect(page.locator(".nbgrader-ErrorDialog")).toHaveCount(1);
}

/*
* Close error modal
*/
export const close_error_modal = async (page:IJupyterLabPageFixture) => {
  await page.locator(".nbgrader-ErrorDialog button.jp-Dialog-button").click();
}

/*
 * Wait for success modal
 */
export const wait_for_success_modal = async (page:IJupyterLabPageFixture) => {
  await expect(page.locator(".nbgrader-SuccessDialog")).toHaveCount(1);
}

/*
* Close success modal
*/
export const close_success_modal = async (page:IJupyterLabPageFixture) => {
  await page.locator(".nbgrader-SuccessDialog button.jp-Dialog-button").click();
}
