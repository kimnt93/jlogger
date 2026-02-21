import jlogger as jlog

logger = jlog.getLogger("worker")


def divide(a: float, b: float):
    try:
        return a / b
    except Exception as e:
        logger.error() \
            .with_error(e) \
            .with_value("a", a) \
            .with_value("b", b) \
            .msg("division failed")


if __name__ == "__main__":
    divide(10, 0)