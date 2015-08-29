from .. import run_python_module


def test_help():
    run_python_module(["nbgrader", "formgrade", "--help-all"])
