from traitlets.config import LoggingConfigurable


plugin_aliases = {
    'log-level': 'Application.log_level',
}
plugin_flags = {
    'debug': (
        {'Application' : {'log_level' : 'DEBUG'}},
        "set log level to DEBUG (maximize logging output)"
    ),
}


class BasePlugin(LoggingConfigurable):

    aliases = plugin_aliases
    flags = plugin_flags

    def __init__(self, **kwargs):
        super(BasePlugin, self).__init__(**kwargs)
