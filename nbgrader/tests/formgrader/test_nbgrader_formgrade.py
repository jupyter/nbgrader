from .. import run_nbgrader


def test_help():
    run_nbgrader(["formgrade", "--help-all"])
