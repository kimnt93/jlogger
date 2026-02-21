import logging
from typing import Optional, Union
from .config import setup_logging
from .logger import CustomJSONLogger
from .timefmt import TimeFormat
from ._time import set_time_format


def setLevel(level: str) -> None:
    logging.getLogger().setLevel(level.upper())

def getLogger(name: Optional[str] = None) -> CustomJSONLogger:
    setup_logging()
    return CustomJSONLogger(logging.getLogger(name or "app"))

def setTimeFormat(fmt: Union[str, TimeFormat]):
    if isinstance(fmt, str):
        fmt = TimeFormat(fmt.lower())
    set_time_format(fmt)