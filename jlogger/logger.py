import logging
from typing import Any, Dict, Optional, Union


class LogEvent:
    __slots__ = ("_logger", "_level", "_kv")

    def __init__(
        self,
        lg: logging.Logger,
        level: int,
        base_kv: Optional[Dict[str, Any]] = None,
    ):
        self._logger = lg
        self._level = level
        self._kv: Dict[str, Any] = dict(base_kv) if base_kv else {}

    def with_value(self, key: str, value: Any) -> "LogEvent":
        self._kv[key] = value
        return self

    def with_error(self, error: Union[Exception, None]) -> "LogEvent":
        if error is None:
            return self
        self._kv["error"] = str(error)
        self._kv["error_type"] = error.__class__.__name__
        return self

    def msg(self, message: str) -> None:
        if self._logger.isEnabledFor(self._level):
            self._logger.log(
                self._level,
                message,
                extra={"kv": self._kv},
            )


# =============================
# Custom JSON Logger
# =============================
class CustomJSONLogger:
    __slots__ = ("_logger", "_base_kv")

    def __init__(
        self,
        lg: logging.Logger,
        base_kv: Optional[Dict[str, Any]] = None,
    ):
        self._logger = lg
        self._base_kv = base_kv or {}

    def with_value(self, key: str, value: Any) -> "CustomJSONLogger":
        new_kv = dict(self._base_kv)
        new_kv[key] = value
        return CustomJSONLogger(self._logger, new_kv)

    def with_error(self, error: Union[Exception, None]) -> "CustomJSONLogger":
        if error is None:
            return CustomJSONLogger(self._logger, self._base_kv)

        new_kv = dict(self._base_kv)
        new_kv["error"] = str(error)
        new_kv["error_type"] = error.__class__.__name__
        return CustomJSONLogger(self._logger, new_kv)

    # levels
    def debug(self) -> LogEvent:
        return LogEvent(self._logger, logging.DEBUG, self._base_kv)

    def info(self) -> LogEvent:
        return LogEvent(self._logger, logging.INFO, self._base_kv)

    def warning(self) -> LogEvent:
        return LogEvent(self._logger, logging.WARNING, self._base_kv)

    def error(self) -> LogEvent:
        return LogEvent(self._logger, logging.ERROR, self._base_kv)

    def critical(self) -> LogEvent:
        return LogEvent(self._logger, logging.CRITICAL, self._base_kv)