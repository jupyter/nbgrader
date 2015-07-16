from nbgrader.tests import run_command


def test_help():
    run_command(["nbgrader", "formgrade", "--help-all"])
