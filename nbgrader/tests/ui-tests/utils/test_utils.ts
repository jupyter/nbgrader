import { IJupyterLabPageFixture } from "@jupyterlab/galata"
import { expect } from '@playwright/test';
import { exec } from "child_process";
import { promisify } from 'util';

import * as path from 'path';
import * as fs from 'fs';

const asyncExec = promisify(exec)


export const executeCommand = async (command: string) => {
  const { stdout, stderr } = await asyncExec(command);
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
export const createEnv = async (
  rootDir: string,
  tmpPath: string,
  exchange_dir: string,
  cache_dir: string,
  is_windows: boolean
  ): Promise<void> => {

  /* Add config_file to jupyter root directory, and change to that directory.
  TODO : test on windows, the config file may change (see nbextension test)
  */
  try {

    var text_to_append = `
c.CourseDirectory.root = r"${path.resolve(rootDir, tmpPath)}"
c.CourseDirectory.db_url = r"sqlite:///${path.resolve(rootDir, tmpPath, 'gradebook.db')}"

`;

    if (!is_windows){
      text_to_append = text_to_append.concat(`
c.Exchange.root = r"${exchange_dir}"
c.Exchange.cache = r"${cache_dir}"
c.Exchange.assignment_dir = r"${path.resolve(rootDir, tmpPath)}"

`);
    }

    fs.appendFileSync(path.resolve(rootDir, "nbgrader_config.py"), text_to_append);
    process.chdir(rootDir);
  }
  catch (e){
    throw new Error(`ERROR : ${e}`);
  }

  /* Fill database */
  await executeCommand("nbgrader db assignment add 'Problem Set 1'");
  await executeCommand("nbgrader db assignment add ps.01");
  await executeCommand("nbgrader db student add Bitdiddle --first-name Ben --last-name B");
  await executeCommand("nbgrader db student add Hacker --first-name Alyssa --last-name H");
  await executeCommand("nbgrader db student add Reasoner --first-name Louis --last-name R");
}

/*
 * Wait for error modal
 */
export const waitForErrorModal = async (page: IJupyterLabPageFixture) => {
  await expect(page.locator(".nbgrader-ErrorDialog")).toHaveCount(1);
}

/*
* Close error modal
*/
export const closeErrorModal = async (page: IJupyterLabPageFixture) => {
  await page.locator(".nbgrader-ErrorDialog button.jp-Dialog-button").click();
}

/*
 * Wait for success modal
 */
export const waitForSuccessModal = async (page: IJupyterLabPageFixture) => {
  await expect(page.locator(".nbgrader-SuccessDialog")).toHaveCount(1);
}

/*
* Close success modal
*/
export const closeSuccessModal = async (page: IJupyterLabPageFixture) => {
  await page.locator(".nbgrader-SuccessDialog button.jp-Dialog-button").click();
}
