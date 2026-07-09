"""Time formats.

The `time` field can be emitted in four formats. UNIX (epoch seconds float)
is the default and fastest; use ISO8601/RFC3339 for human-readable output.
"""

import jlogger as jlog

logger = jlog.getLogger("clock")

if __name__ == "__main__":
    for fmt in (
        jlog.TimeFormat.UNIX,      # 1770000000.123  (default, fastest)
        jlog.TimeFormat.UNIX_MS,   # 1770000000123   (int milliseconds)
        jlog.TimeFormat.ISO8601,   # 2026-07-09T11:33:11.312
        jlog.TimeFormat.RFC3339,   # same as ISO8601, explicit alias
    ):
        jlog.setTimeFormat(fmt)
        logger.info().with_value("format", fmt.value).msg("tick")
