"""NumPy values.

The Rust core recognizes NumPy scalars and arrays (anything whose type lives
in the `numpy` module) and converts them via `.tolist()` before serializing,
so you can log arrays and numpy scalars without manual conversion.

Run with numpy installed:  uv run --with numpy python examples/numpy_values.py
"""

import jlogger as jlog

logger = jlog.getLogger("ml")


def main() -> None:
    try:
        import numpy as np
    except ImportError:
        logger.warning().msg("numpy not installed; skipping numpy demo")
        return

    logger.info() \
        .with_value("weights", np.array([0.1, 0.2, 0.7])) \
        .with_value("epoch", np.int64(3)) \
        .with_value("loss", np.float32(0.0123)) \
        .with_value("matrix", np.arange(6).reshape(2, 3)) \
        .msg("training step")


if __name__ == "__main__":
    main()
