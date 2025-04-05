import warnings
from nbgrader.exchange.abc import  ExchangeError
from nbgrader.exchange import abc, default
from .exchange_factory import ExchangeFactory

def __getattr__(name):
    if name in abc.__all__:
        warnings.warn(
            f"Importing {name} from nbgrader.exchange is deprecated."
            " Import from nbgrader.exchange.abc or the specific "
            " exchange implementation instead.".format(name),
            DeprecationWarning,
            stacklevel=2
        )

    if hasattr(abc, name):
        return getattr(abc, name)
    elif hasattr(default, name):
        return getattr(default, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "abc",
    "default",
    "ExchangeFactory",
    "ExchangeError",
]
