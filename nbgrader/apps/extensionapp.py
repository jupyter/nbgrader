import io
import os.path
import json
import sys

from IPython.html.nbextensions import NBExtensionApp, flags as extension_flags, aliases as extension_aliases
from IPython.utils.traitlets import Unicode
from IPython.utils.py3compat import cast_unicode_py2
from IPython.config.application import catch_config_error
from IPython.config.application import Application

from nbgrader.apps.baseapp import BaseApp, format_excepthook, base_aliases, base_flags


install_flags = {}
install_flags.update(extension_flags)
install_flags.update({
})
install_aliases = {}
install_aliases.update(extension_aliases)
del install_aliases['destination']
del install_aliases['ipython-dir']
install_aliases.update({
})
class ExtensionInstallApp(NBExtensionApp):

    name = u'nbgrader-extension-install'
    description = u'Install the nbgrader extension'

    flags = install_flags
    aliases = install_aliases

    examples = """
        nbgrader extension install
        nbgrader extension install --user
        nbgrader extension install --prefix=/path/to/prefix
        nbgrader extension install --nbextensions=/path/to/nbextensions
    """

    destination = Unicode('')

    def _classes_default(self):
        return []

    def excepthook(self, etype, evalue, tb):
        format_excepthook(etype, evalue, tb)

    def start(self):
        self.extra_args = [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'nbextensions', 'nbgrader'))]
        self.install_extensions()


activate_flags = {}
activate_flags.update(base_flags)
activate_flags.update({
})
activate_aliases = {}
activate_aliases.update(base_aliases)
activate_aliases.update({
    "ipython-dir": "BasicConfig.ipython_dir",
    "profile": "BasicConfig.profile"
})
class ExtensionActivateApp(BaseApp):

    name = u'nbgrader-extension-activate'
    description = u'Activate the nbgrader extension'

    flags = activate_flags
    aliases = activate_aliases

    examples = """
        nbgrader extension activate
    """

    def build_extra_config(self):
        config = super(ExtensionActivateApp, self).build_extra_config()
        if 'profile' not in config.BasicConfig:
            config.BasicConfig.profile = 'default'
        return config

    def start(self):
        super(ExtensionActivateApp, self).start()

        self.log.info("Activating nbextension for '%s' profile" % self.profile)

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


deactivate_flags = {}
deactivate_flags.update(base_flags)
deactivate_flags.update({
})
deactivate_aliases = {}
deactivate_aliases.update(base_aliases)
deactivate_aliases.update({
    "ipython-dir": "BasicConfig.ipython_dir",
    "profile": "BasicConfig.profile"
})
class ExtensionDeactivateApp(BaseApp):

    name = u'nbgrader-extension-deactivate'
    description = u'Deactivate the nbgrader extension'

    flags = deactivate_flags
    aliases = deactivate_aliases

    examples = """
        nbgrader extension deactivate
    """

    def build_extra_config(self):
        config = super(ExtensionDeactivateApp, self).build_extra_config()
        if 'profile' not in config.BasicConfig:
            config.BasicConfig.profile = 'default'
        return config

    def start(self):
        super(ExtensionDeactivateApp, self).start()

        self.log.info("Dectivating nbextension for '%s' profile" % self.profile)

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

        # deactivation require the delete the key.
        del config['load_extensions']['nbgrader/create_assignment']

        # prune if last extension.
        if not config['load_extensions']:
            del config['load_extensions']

        with io.open(json_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))


class ExtensionApp(Application):

    name = u'nbgrader extension'
    description = u'Utilities for managing the nbgrader extension'
    examples = ""

    subcommands = dict(
        install=(
            ExtensionInstallApp,
            "Install the extension."
        ),
        activate=(
            ExtensionActivateApp,
            "Activate the extension."
        ),
        deactivate=(
            ExtensionDeactivateApp,
            "Deactivate the extension."
        )
    )

    def _classes_default(self):
        classes = super(ExtensionApp, self)._classes_default()

        # include all the apps that have configurable options
        for appname, (app, help) in self.subcommands.items():
            if len(app.class_traits(config=True)) > 0:
                classes.append(app)

    @catch_config_error
    def initialize(self, argv=None):
        super(ExtensionApp, self).initialize(argv)

    def start(self):
        # check: is there a subapp given?
        if self.subapp is None:
            self.print_help()
            sys.exit(1)

        # This starts subapps
        super(ExtensionApp, self).start()
