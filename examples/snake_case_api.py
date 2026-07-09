"""Snake-case API.

jlogger keeps the camelCase names from the Go-style original API
(`getLogger`, `setLevel`, `setTimeFormat`) and also exposes snake_case
aliases (`get_logger`, `set_level`, `set_time_format`) for Python-idiomatic
code. Pick whichever fits your codebase.
"""

import jlogger as jlog

jlog.set_time_format(jlog.TimeFormat.RFC3339)
jlog.set_level("info")

logger = jlog.get_logger("trade").with_values(symbol="BTCUSDT", venue="binance")

if __name__ == "__main__":
    logger.info().with_values(price=65000, qty=0.5).msg("tick")
    logger.warning().with_value("spread_bps", 12).msg("wide spread")
