import logging
from typing import Any, Dict
import orjson

from jlogger._time import now


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "time": now(),
            "logger": record.name,
            "level": record.levelname.lower(),
            "message": record.getMessage(),
        }

        kv = getattr(record, "kv", None)
        if kv:
            log_obj.update(kv)

        return orjson.dumps(
            log_obj,
            option=orjson.OPT_SERIALIZE_NUMPY,
            default=str,
        ).decode()