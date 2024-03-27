import sys
import os
from os.path import join
import shutil
import subprocess

env = os.environ.copy()
root_dir = env.get("NBGRADER_TEST_DIR", '')

if not env["NBGRADER_TEST_DIR"]:
  raise Exception("Test directory not provided")
if not os.path.isdir(env["NBGRADER_TEST_DIR"]):
  raise Exception(f"Test directory {env['NBGRADER_TEST_DIR']} doesn't exists")

subprocess.check_call([sys.executable, "-m", "jupyter", "server", "extension", "enable", "--user", "--py", "nbgrader"], env=env)
subprocess.check_call([sys.executable, "-m", "jupyter", "labextension", "develop", "--overwrite", "."])

shutil.copyfile("./nbgrader/tests/ui-tests/files/nbgrader_config.py",
                join(root_dir, "nbgrader_config.py"))

if "NBGRADER_TEST_IS_NOTEBOOK" in env.keys():
  shutil.copyfile("./nbgrader/tests/ui-tests/utils/jupyter_server_config_notebook.py",
                join(root_dir, "jupyter_server_config_notebook.py"))
  command = ["jupyter", "notebook", "--config", "./jupyter_server_config_notebook.py"]
else:
  shutil.copyfile("./nbgrader/tests/ui-tests/utils/jupyter_server_config.py",
                join(root_dir, "jupyter_server_config.py"))
  command = ["jupyter", "lab", "--config", "./jupyter_server_config.py"]

os.chdir(root_dir)

subprocess.run(command)
