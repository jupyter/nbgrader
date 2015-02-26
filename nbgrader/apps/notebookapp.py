import os
from tornado import ioloop
from IPython.html.notebookapp import NotebookApp

class FormGradeNotebookApp(NotebookApp):
    """A Subclass of the regular NotebookApp that can be spawned by the form grader."""
    open_browser = False

    def _ipython_dir_default(self):
        d = os.path.join(os.environ["HOME"], ".nbgrader")
        self._ipython_dir_changed('ipython_dir', d, d)
        return d
    
    def _confirm_exit(self):
        # disable the exit confirmation for background notebook processes
        ioloop.IOLoop.instance().stop()
    

def main():
    return FormGradeNotebookApp.launch_instance()


if __name__ == "__main__":
    main()
