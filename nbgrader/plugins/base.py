from traitlets.config import LoggingConfigurable
from typing import Any


class BasePlugin(LoggingConfigurable):

    def __init__(self, **kwargs: Any) -> None:
        super(BasePlugin, self).__init__(**kwargs)
