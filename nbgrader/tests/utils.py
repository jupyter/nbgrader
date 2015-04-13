import os
import glob
import shutil
import subprocess as sp

from IPython.utils.tempdir import TemporaryWorkingDirectory

def temp_cwd(copy_filenames=None):
    temp_dir = TemporaryWorkingDirectory()

    if copy_filenames is not None:
        files_path = os.path.dirname(__file__)
        for pattern in copy_filenames:
            for match in glob.glob(os.path.join(files_path, pattern)):
                dest = os.path.join(temp_dir.name, os.path.basename(match))
                shutil.copyfile(match, dest)

    return temp_dir


def start_subprocess(command, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT, cwd=None):
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env = os.environ.copy()
    env['COVERAGE_PROCESS_START'] = os.path.join(root, ".coveragerc")
    proc = sp.Popen(command, shell=shell, stdout=stdout, stderr=stderr, env=env, cwd=cwd)
    return proc


def copy_coverage_files():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if os.getcwd() != root:
        coverage_files = glob.glob(".coverage.*")
        if len(coverage_files) == 0:
            raise RuntimeError("No coverage files produced")
        for filename in coverage_files:
            shutil.copyfile(filename, os.path.join(root, filename))


def run_command(command, retcode=0):
    proc = start_subprocess(command)
    true_retcode = proc.wait()
    output = proc.communicate()[0].decode()
    print(output)
    if true_retcode != retcode:
        raise AssertionError(
            "process returned an unexpected return code: {}".format(true_retcode))
    copy_coverage_files()
    return output
