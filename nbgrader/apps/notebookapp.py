from tornado import ioloop
from notebook.notebookapp import NotebookApp


class FormgradeNotebookApp(NotebookApp):
    """A Subclass of the regular NotebookApp that can be spawned by the form grader."""
    open_browser = False

    def _profile_default(self):
        return 'nbgrader'

    def _confirm_exit(self):
        # disable the exit confirmation for background notebook processes
        ioloop.IOLoop.instance().stop()


def main():
    return FormgradeNotebookApp.launch_instance()


if __name__ == "__main__":
    main()
