from typing import Optional, Union

from . import config
from ._time import set_time_format as _set_time_format
from .logger import Logger
from .timefmt import TimeFormat


def getLogger(name: Optional[str] = None, level: Union[str, int, None] = None) -> Logger:
    lvl = config.normalize_level(level) if level is not None else None
    return Logger(name or "app", level=lvl)


def setLevel(level: Union[str, int]) -> None:
    config.set_level(level)


def setOutput(writer) -> None:
    """Send log lines to ``writer`` (anything with a ``write(str)`` method)."""
    config.set_writer(writer)


def setTimeFormat(fmt: Union[str, TimeFormat]) -> None:
    if isinstance(fmt, str):
        fmt = TimeFormat(fmt.lower())
    _set_time_format(fmt)


# snake_case aliases
def get_logger(name: Optional[str] = None, level: Union[str, int, None] = None) -> Logger:
    return getLogger(name, level)


def set_level(level: Union[str, int]) -> None:
    setLevel(level)


def set_output(writer) -> None:
    setOutput(writer)


def set_time_format(fmt: Union[str, TimeFormat]) -> None:
    setTimeFormat(fmt)
