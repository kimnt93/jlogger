"""Global logger configuration: level threshold and output writer.

jlogger does NOT use the stdlib ``logging`` pipeline. Instead it keeps a single
level threshold and an output stream here, and writes formatted JSON lines
directly (zerolog-style). This avoids ``LogRecord`` creation, caller stack
walks, and the handler lock hierarchy that make stdlib logging slow.
"""

import os
import sys
import threading
from typing import Union

# Level values mirror the stdlib ``logging`` module so integer levels behave
# the same way for anyone used to them.
NOTSET = 0
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

LEVEL_NAMES = {
    DEBUG: "debug",
    INFO: "info",
    WARNING: "warning",
    ERROR: "error",
    CRITICAL: "critical",
}

_NAME_TO_LEVEL = {
    "NOTSET": NOTSET,
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "WARN": WARNING,
    "ERROR": ERROR,
    "CRITICAL": CRITICAL,
    "FATAL": CRITICAL,
}


def normalize_level(level: Union[str, int]) -> int:
    """Coerce a level name or int into a threshold int."""
    if isinstance(level, str):
        try:
            return _NAME_TO_LEVEL[level.upper()]
        except KeyError:
            raise ValueError(f"unknown log level: {level!r}") from None
    return int(level)


# --------------------------------------------------------------------------- #
# Mutable global state (read on every log call; keep it trivially cheap)
# --------------------------------------------------------------------------- #

# Active threshold: an event is emitted when its level >= ``level``.
level: int = normalize_level(os.environ.get("LOG_LEVEL", "INFO"))

_writer = sys.stderr
_lock = threading.Lock()
_NEWLINE = "\n"


def set_level(new_level: Union[str, int]) -> None:
    global level
    level = normalize_level(new_level)


def set_writer(writer) -> None:
    """Set the output stream. Must have a ``write(str)`` method."""
    global _writer
    _writer = writer


def get_writer():
    return _writer


def write(line: str) -> None:
    """Write a single pre-formatted JSON line plus newline, atomically."""
    writer = _writer
    with _lock:
        writer.write(line)
        writer.write(_NEWLINE)
