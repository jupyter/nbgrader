from tempfile import mkdtemp
import os
import shutil
import subprocess

root_dir = mkdtemp(prefix="galata-test-")

shutil.copyfile("./nbgrader/tests/labextension_ui-tests/jupyter_server_test_config.py",
                os.path.join(root_dir, "jupyter_server_test_config.py"))

shutil.copyfile("./nbgrader/tests/labextension_ui-tests/files/nbgrader_config.py",
                os.path.join(root_dir, "nbgrader_config.py.default"))

os.chdir(root_dir)
command = ["jupyter", "lab", "--config", "./jupyter_server_test_config.py"]
subprocess.run(command)
