import sys
import os
from os.path import join
import shutil
import subprocess

from tempfile import mkdtemp

root_dir = mkdtemp(prefix="galata-test-")
env = os.environ.copy()

shutil.copyfile("./nbgrader/tests/labextension_ui-tests/jupyter_server_test_config.py",
                join(root_dir, "jupyter_server_test_config.py"))

shutil.copyfile("./nbgrader/tests/labextension_ui-tests/files/nbgrader_config.py",
                join(root_dir, "nbgrader_config.py.default"))

subprocess.check_call([sys.executable, "-m", "jupyter", "server", "extension", "enable", "--user", "--py", "nbgrader"], env=env)
subprocess.check_call([sys.executable, "-m", "jupyter", "labextension", "develop", "."])

os.chdir(root_dir)

command = ["jupyter", "lab", "--config", "./jupyter_server_test_config.py"]
subprocess.run(command)
