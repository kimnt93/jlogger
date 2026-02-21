import logging
import os
import threading
from typing import Union

from .formatter import JsonFormatter

_lock = threading.Lock()
_configured = False


def setup_logging(level: Union[str, None] = None) -> None:
    """
    Initialize root logging once (thread-safe).
    """
    global _configured

    if _configured:
        return

    with _lock:
        if _configured:
            return

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())

        root = logging.getLogger()

        lvl = level or os.environ.get("LOG_LEVEL", "INFO")
        root.setLevel(lvl.upper())

        root.handlers.clear()
        root.addHandler(handler)

        _configured = True