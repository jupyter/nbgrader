import { exec } from "child_process";
import { promisify } from 'util';

const async_exec = promisify(exec)

export const execute_command = async (command: string) => {
  const { stderr } = await async_exec(command);
  if (stderr) {
    if (stderr.includes("ERROR")){
      console.log(`stderr: ${stderr}`);
      throw new Error(`ERROR in command : ${command}\n${stderr}`);
    }
  }
}
