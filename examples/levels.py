"""Log levels and level filtering.

Like zerolog/zap, each level starts a fluent event with `.level()` and is
emitted with `.msg()`. Set the threshold with `setLevel`; anything below it is
dropped before formatting, so it stays cheap.
"""

import jlogger as jlog

# Only WARNING and above will be emitted.
jlog.setLevel("warning")

logger = jlog.getLogger("service")

if __name__ == "__main__":
    logger.debug().msg("this is dropped")       # below threshold
    logger.info().msg("this is dropped too")    # below threshold
    logger.warning().with_value("retries", 3).msg("slow downstream call")
    logger.error().with_value("code", 500).msg("request failed")
    logger.critical().msg("shutting down")
