from enum import Enum


class TimeFormat(str, Enum):
    UNIX = "unix"          # DEFAULT, fastest
    UNIX_MS = "unix_ms"    # milliseconds int
    ISO8601 = "iso8601"    # 2026-02-21T15:04:05Z
    RFC3339 = "rfc3339"    # same as iso but explicit