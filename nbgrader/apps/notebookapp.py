from tornado import ioloop
from traitlets import default
from notebook.notebookapp import NotebookApp


class FormgradeNotebookApp(NotebookApp):
    """A Subclass of the regular NotebookApp that can be spawned by the form grader."""
    open_browser = False
    token = ''  # Notebook >=4.3

    @default("profile")
    def _profile_default(self):
        return 'nbgrader'

    def _confirm_exit(self):
        # disable the exit confirmation for background notebook processes
        ioloop.IOLoop.instance().stop()


def main():
    return FormgradeNotebookApp.launch_instance()


if __name__ == "__main__":
    main()
