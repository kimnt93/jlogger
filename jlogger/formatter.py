import logging

from jlogger._encoder import format_record
from jlogger._time import now


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        kv = getattr(record, "kv", None)
        if kv is None:
            kv = {}

        return format_record(
            now(),
            record.name,
            record.levelname.lower(),
            record.getMessage(),
            kv,
        )
