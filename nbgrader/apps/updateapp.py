import os

from nbformat import current_nbformat, read as orig_read, write as orig_write
from traitlets import Bool

from .baseapp import NbGrader, nbgrader_aliases, nbgrader_flags
from ..nbformat import Validator, write
from ..utils import find_all_notebooks

aliases = {}
aliases.update(nbgrader_aliases)
aliases.update({
})

flags = {}
flags.update(nbgrader_flags)
flags.update({
})


class UpdateApp(NbGrader):

    name = u'nbgrader-update'
    description = u'Update nbgrader notebook metadata'

    aliases = aliases
    flags = flags

    validate = Bool(True, help="whether to validate metadata after updating it").tag(config=True)

    examples = """
        nbgrader stores metadata in its 
        """

    def start(self):
        super(UpdateApp, self).start()

        if len(self.extra_args) < 1:
            self.fail("No notebooks given")

        notebooks = set()
        for name in self.extra_args:
            if not os.path.exists(name):
                self.fail("No such file or directory: {}".format(name))
            elif os.path.isdir(name):
                notebooks.update([os.path.join(name, x) for x in find_all_notebooks(name)])
            elif not name.endswith(".ipynb"):
                self.log.warn("{} is not a notebook, ignoring".format(name))
            else:
                notebooks.add(name)

        notebooks = sorted(list(notebooks))
        for notebook in notebooks:
            self.log.info("Updating metadata for notebook: {}".format(notebook))
            nb = orig_read(notebook, current_nbformat)
            nb = Validator().upgrade_notebook_metadata(nb)
            if self.validate:
                write(nb, notebook)
            else:
                orig_write(nb, notebook)

