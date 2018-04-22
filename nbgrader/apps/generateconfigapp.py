# coding: utf-8

import os

from traitlets import Unicode
from traitlets.config.application import catch_config_error
from .baseapp import NbGrader


class GenerateConfigApp(NbGrader):

    name = u'nbgrader-generate-config'
    description = u'Generates a default nbgrader_config.py file'
    examples = ""

    filename = Unicode(
        "nbgrader_config.py",
        help="The name of the configuration file to generate."
    ).tag(config=True)

    @catch_config_error
    def initialize(self, argv=None):
        super(GenerateConfigApp, self).initialize(argv)

    def start(self):
        super(GenerateConfigApp, self).start()
        s = self.generate_config_file()

        if os.path.exists(self.filename):
            self.fail("Config file '{}' already exists".format(self.filename))

        with open(self.filename, 'w') as fh:
            fh.write(s)
        self.log.info("New config file saved to '{}'".format(self.filename))
