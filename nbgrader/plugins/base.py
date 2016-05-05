from traitlets.config import LoggingConfigurable
from traitlets import List
from traitlets import Unicode


class BasePluginLoader(LoggingConfigurable):

    plugin_file_name = Unicode(
        'nbgrader_plugin',
        help="Specify the plugin file name."
    ).tag(config=True)

    supported_methods = List([])

    def __init__(self, **kwargs):
        super(BasePluginLoader, self).__init__(**kwargs)

    def import_plugin(self):
        return None
