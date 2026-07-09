"""Zerolog-style fluent logger that writes JSON directly to a stream.

Hot path, per emitted line:
  * one level comparison (``level >= threshold``)
  * one ``LogEvent`` allocation (copy-on-write context, so no dict copy unless
    fields are actually added)
  * one native ``format_record`` call (builds the whole JSON line in Rust)
  * one locked ``write``

Disabled calls (below the active level) return a shared no-op singleton and do
zero work — no allocation, no formatting.
"""

from typing import Any, Dict, Mapping, Optional, Union

from . import config
from ._encoder import format_record
from ._time import now

# Bind hot-path callables/constants as locals for fast lookups.
_format_record = format_record
_now = now
_write = config.write
_LEVEL_NAMES = config.LEVEL_NAMES
DEBUG = config.DEBUG
INFO = config.INFO
WARNING = config.WARNING
ERROR = config.ERROR
CRITICAL = config.CRITICAL


class _NopEvent:
    """Shared disabled event: every method is a no-op returning self."""

    __slots__ = ()

    def with_value(self, key: str, value: Any) -> "_NopEvent":
        return self

    def with_values(self, **values: Any) -> "_NopEvent":
        return self

    def with_dict(self, values: Mapping[str, Any]) -> "_NopEvent":
        return self

    def with_error(self, error: Union[Exception, None]) -> "_NopEvent":
        return self

    def msg(self, message: str) -> None:
        return None


# One immutable instance is enough for all disabled calls.
_NOP = _NopEvent()


class LogEvent:
    """A single in-progress log line. Not thread-safe (use within one call)."""

    __slots__ = ("_name", "_level_name", "_kv", "_owned")

    def __init__(self, name: str, level_name: str, base_kv: Dict[str, Any]):
        self._name = name
        self._level_name = level_name
        # Share the logger's context dict until we actually mutate it.
        self._kv = base_kv
        self._owned = False

    def _own(self) -> None:
        if not self._owned:
            self._kv = dict(self._kv)
            self._owned = True

    def with_value(self, key: str, value: Any) -> "LogEvent":
        self._own()
        self._kv[key] = value
        return self

    def with_values(self, **values: Any) -> "LogEvent":
        self._own()
        self._kv.update(values)
        return self

    def with_dict(self, values: Mapping[str, Any]) -> "LogEvent":
        self._own()
        self._kv.update(values)
        return self

    def with_error(self, error: Union[Exception, None]) -> "LogEvent":
        if error is None:
            return self
        self._own()
        self._kv["error"] = str(error)
        self._kv["error_type"] = error.__class__.__name__
        return self

    def msg(self, message: str) -> None:
        _write(_format_record(_now(), self._name, self._level_name, message, self._kv))


class CustomJSONLogger:
    """A named logger with optional bound context and an optional level."""

    __slots__ = ("_name", "_base_kv", "_level")

    def __init__(
        self,
        name: str = "app",
        base_kv: Optional[Dict[str, Any]] = None,
        level: Optional[int] = None,
    ):
        self._name = name
        self._base_kv: Dict[str, Any] = base_kv if base_kv is not None else {}
        # Per-logger threshold; None means "use the global level".
        self._level = level

    # -- context (returns a new logger; base context is immutable) --------- #

    def with_value(self, key: str, value: Any) -> "CustomJSONLogger":
        new_kv = dict(self._base_kv)
        new_kv[key] = value
        return CustomJSONLogger(self._name, new_kv, self._level)

    def with_values(self, **values: Any) -> "CustomJSONLogger":
        new_kv = dict(self._base_kv)
        new_kv.update(values)
        return CustomJSONLogger(self._name, new_kv, self._level)

    def with_dict(self, values: Mapping[str, Any]) -> "CustomJSONLogger":
        new_kv = dict(self._base_kv)
        new_kv.update(values)
        return CustomJSONLogger(self._name, new_kv, self._level)

    def with_error(self, error: Union[Exception, None]) -> "CustomJSONLogger":
        if error is None:
            return self
        new_kv = dict(self._base_kv)
        new_kv["error"] = str(error)
        new_kv["error_type"] = error.__class__.__name__
        return CustomJSONLogger(self._name, new_kv, self._level)

    def level(self, level: Union[str, int]) -> "CustomJSONLogger":
        """Return a copy of this logger with its own level threshold."""
        return CustomJSONLogger(
            self._name, self._base_kv, config.normalize_level(level)
        )

    # -- levels ------------------------------------------------------------ #

    def debug(self):
        threshold = self._level
        if threshold is None:
            threshold = config.level
        if DEBUG >= threshold:
            return LogEvent(self._name, "debug", self._base_kv)
        return _NOP

    def info(self):
        threshold = self._level
        if threshold is None:
            threshold = config.level
        if INFO >= threshold:
            return LogEvent(self._name, "info", self._base_kv)
        return _NOP

    def warning(self):
        threshold = self._level
        if threshold is None:
            threshold = config.level
        if WARNING >= threshold:
            return LogEvent(self._name, "warning", self._base_kv)
        return _NOP

    def warn(self):
        return self.warning()

    def error(self):
        threshold = self._level
        if threshold is None:
            threshold = config.level
        if ERROR >= threshold:
            return LogEvent(self._name, "error", self._base_kv)
        return _NOP

    def critical(self):
        threshold = self._level
        if threshold is None:
            threshold = config.level
        if CRITICAL >= threshold:
            return LogEvent(self._name, "critical", self._base_kv)
        return _NOP


Logger = CustomJSONLogger
