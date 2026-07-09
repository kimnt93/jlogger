import logging
import os
import threading
from typing import Union

from .formatter import JsonFormatter

_lock = threading.Lock()
_configured = False


def setup_logging(level: Union[str, int, None] = None) -> None:
    """
    Initialize root logging once (thread-safe).
    """
    global _configured

    if _configured:
        if level is not None:
            logging.getLogger().setLevel(_normalize_level(level))
        return

    with _lock:
        if _configured:
            return

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())

        root = logging.getLogger()

        lvl = level or os.environ.get("LOG_LEVEL", "INFO")
        root.setLevel(_normalize_level(lvl))

        root.handlers.clear()
        root.addHandler(handler)

        _configured = True


def _normalize_level(level: Union[str, int]) -> Union[str, int]:
    if isinstance(level, str):
        return level.upper()
    return level
