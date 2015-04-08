"""
Misc utils to deals with installing nbgrader on a system
"""

from __future__ import print_function, absolute_import

import sys
import io
import os.path
import json

from IPython.html.nbextensions import NBExtensionApp, flags as base_flags, aliases as base_aliases
from IPython.utils.traitlets import Unicode, Bool
from IPython.utils.py3compat import cast_unicode_py2


flags = {}
flags.update(base_flags)
flags.update({
    "install" : (
        {"NbGraderExtensionApp" : {"install" : True}},
        "Install the nbgrader nbextension"
    ),
    "activate" : (
        {"NbGraderExtensionApp" : {"activate" : True}},
        "Activate the nbgrader nbextension in the given profile (cannot be used with --deactivate)"
    ),
    "deactivate" : (
        {"NbGraderExtensionApp" : {"deactivate" : True}},
        "Deactivate the nbgrader nbextension in the given profile (cannot be used with --activate)"
    ),
})

aliases = {}
aliases.update(base_aliases)
del aliases['destination']
aliases.update({
})

class NbGraderExtensionApp(NBExtensionApp):

    flags = flags
    aliases = aliases

    description = """Install nbgrader notebook extensions

    Usage

        python -m nbgrader [--install] [--activate] [--deactivate]

    At least one of --install, --activate, or --deactivate must be given.

    If the requested files are already up to date, no action is taken
    unless --overwrite is specified.
    """

    examples = """
    To install without activating:

        python -m nbgrader --install

    To install and activate in the default profile:

        python -m nbgrader --install --activate

    To deactivate in the default profile:

        python -m nbgrader --deactivate

    """

    install = Bool(
        False,
        config=True,
        help="Install the nbgrader nbextension")

    activate = Bool(
        False,
        config=True,
        help="Activate the nbgrader nbextension in the given profile (incompatible with the `deactivate` option")

    deactivate = Bool(
        False,
        config=True,
        help="Deactivate the nbgrader extension in the given profile (incompatible with the `activate` option)")

    destination = Unicode('')

    def start(self):
        if self.activate and self.deactivate:
            self.log.error("--activate and --deactivate cannot be used at the same time")
            sys.exit(1)

        if not self.activate and not self.deactivate and not self.install:
            self.print_help()
            sys.exit(1)

        self.extra_args = [os.path.join(os.path.dirname(__file__), 'nbextensions', 'nbgrader')]
        if self.install:
            self.install_extensions()
        if self.activate:
            self.activate_extensions()
        if self.deactivate:
            self.deactivate_extensions()

    def activate_extensions(self):
        """
        Manually modify the frontend json-config to load nbgrader extension.
        """
        if self.verbose >= 1:
            print("activating nbextension for '%s' profile" % self.profile)

        json_dir = os.path.join(self.profile_dir.location, 'nbconfig')
        json_file = os.path.expanduser(os.path.join(json_dir, 'notebook.json'))

        try:
            with io.open(json_file, 'r') as f:
                config = json.loads(f.read())
        except IOError:
            # file doesn't exist yet. IPython might have never been launched.
            config = {}

        if not config.get('load_extensions', None):
            config['load_extensions'] = {}
        config['load_extensions']['nbgrader/create_assignment'] = True

        if not os.path.exists(json_dir):
            os.mkdir(json_dir)

        with io.open(json_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))


    def deactivate_extensions(self):
        """
        Manually modify the frontend json-config to load nbgrader extension.
        """
        json_dir = os.path.join(self.profile_dir.location, 'nbconfig')
        json_file = os.path.expanduser(os.path.join(json_dir, 'notebook.json'))

        try:
            with io.open(json_file, 'r') as f:
                config = json.loads(f.read())
        except IOError:
            # file doesn't exist yet. IPython might have never been launched.
            return

        if 'load_extensions' not in config:
            return
        if 'nbgrader/create_assignment' not in config['load_extensions']:
            return

        if self.verbose >= 1:
            print("deactivating nbextension for '%s' profile" % self.profile)

        # deactivation require the delete the key.
        del config['load_extensions']['nbgrader/create_assignment']

        # prune if last extension.
        if not config['load_extensions']:
            del config['load_extensions']

        with io.open(json_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))


def main():
    NbGraderExtensionApp.launch_instance()

