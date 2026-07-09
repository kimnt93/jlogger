import logging
from typing import Optional, Union
from .config import setup_logging
from .logger import Logger
from .timefmt import TimeFormat
from ._time import set_time_format as _set_time_format


def setLevel(level: Union[str, int]) -> None:
    setup_logging(level)
    logging.getLogger().setLevel(_normalize_level(level))


def getLogger(name: Optional[str] = None) -> Logger:
    setup_logging()
    return Logger(logging.getLogger(name or "app"))


def setTimeFormat(fmt: Union[str, TimeFormat]) -> None:
    if isinstance(fmt, str):
        fmt = TimeFormat(fmt.lower())
    _set_time_format(fmt)


def get_logger(name: Optional[str] = None) -> Logger:
    return getLogger(name)


def set_level(level: Union[str, int]) -> None:
    setLevel(level)


def set_time_format(fmt: Union[str, TimeFormat]) -> None:
    setTimeFormat(fmt)


def _normalize_level(level: Union[str, int]) -> Union[str, int]:
    if isinstance(level, str):
        return level.upper()
    return level
