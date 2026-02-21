import time
import datetime
from typing import Callable
from .timefmt import TimeFormat

_time_func: Callable[[], object] = time.time

def set_time_format(fmt: TimeFormat):
    global _time_func

    if fmt == TimeFormat.UNIX:
        _time_func = time.time

    elif fmt == TimeFormat.UNIX_MS:
        _time_func = lambda: int(time.time() * 1000)

    elif fmt in (TimeFormat.ISO8601, TimeFormat.RFC3339):
        _time_func = lambda: (
            datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    else:
        raise ValueError(f"Unsupported time format: {fmt}")


def now():
    return _time_func()