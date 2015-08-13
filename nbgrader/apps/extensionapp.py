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
install_aliases = {}
install_aliases.update(extension_aliases)
del install_aliases['destination']
del install_aliases['ipython-dir']
class ExtensionInstallApp(NBExtensionApp, BaseApp):

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
        nbextensions_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'nbextensions'))
        extra_args = self.extra_args.copy()

        # install the create_assignment extension
        if len(extra_args) == 0 or "create_assignment" in extra_args:
            self.log.info("Installing create_assignment extension")
            self.extra_args = [os.path.join(nbextensions_dir, 'create_assignment')]
            self.destination = 'create_assignment'
            self.install_extensions()


activate_flags = {}
activate_flags.update(base_flags)
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

    def _update_config(self, config_file, key_list, value):
        if os.path.exists(config_file):
            with io.open(config_file, 'r') as f:
                config = json.loads(f.read())
        else:
            config = {}

        # ensure the hierarchy of dictionaries exists
        last_config = config
        for key in key_list[:-1]:
            if key not in last_config:
                last_config[key] = {}
            last_config = last_config[key]

        # add the actual key/value pair
        if isinstance(value, (list, tuple, set)):
            old_set = set(last_config.get(key_list[-1], set([])))
            old_set.update(set(value))
            last_config[key_list[-1]] = list(old_set)
        else:
            last_config[key_list[-1]] = value

        # make sure the directory exists
        if not os.path.exists(os.path.dirname(config_file)):
            os.mkdir(os.path.dirname(config_file))

        # save it out
        with io.open(config_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))

    def start(self):
        super(ExtensionActivateApp, self).start()

        if len(self.extra_args) == 0 or "create_assignment" in self.extra_args:
            self.log.info("Activating create_assignment nbextension for '%s' profile" % self.profile)
            self._update_config(
                os.path.expanduser(os.path.join(self.profile_dir.location, 'nbconfig', 'notebook.json')),
                ["load_extensions", "create_assignment/main"],
                True
            )


deactivate_flags = {}
deactivate_flags.update(base_flags)
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

    def _recursive_get(self, obj, key_list):
        if obj is None or len(key_list) == 0:
            return obj
        return self._recursive_get(obj.get(key_list[0], None), key_list[1:])

    def _update_config(self, config_file, key_list, value=None):
        if os.path.exists(config_file):
            with io.open(config_file, 'r') as f:
                config = json.loads(f.read())
        else:
            config = {}

        # search for the key through the hierarchy, return if it's not present
        last_config = self._recursive_get(config, key_list)
        if last_config is None:
            return

        # remove the key
        if value is None:
            self._recursive_get(config, key_list[:-1])[key_list[-1]] = False
        else:
            last_config = self._recursive_get(config, key_list[:-1])[key_list[-1]]
            if value not in last_config:
                return
            last_config.remove(value)

        # remove empty structures
        while len(key_list) > 0:
            key = key_list.pop()
            last_config = self._recursive_get(config, key_list)
            if not last_config[key]:
                del last_config[key]

        # save the updated config
        with io.open(config_file, 'w+') as f:
            f.write(cast_unicode_py2(json.dumps(config, indent=2), 'utf-8'))

    def start(self):
        print(self.extra_args)
        super(ExtensionDeactivateApp, self).start()

        if len(self.extra_args) == 0 or "create_assignment" in self.extra_args:
            self.log.info("Deactivating create_assignment nbextension for '%s' profile" % self.profile)
            self._update_config(
                os.path.expanduser(os.path.join(self.profile_dir.location, 'nbconfig', 'notebook.json')),
                ["load_extensions", "create_assignment/main"]
            )


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
