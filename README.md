# jlogger

A fast, minimal structured JSON logger for Python.

`jlogger` keeps a small Python interface and builds JSON in Rust through a
PyO3 extension, so it does not depend on `orjson` and can target modern CPython
builds, including free-threaded Python 3.14t.

## Installation

```bash
git clone https://github.com/kimnt93/jlogger.git
cd jlogger
make develop
```

For a normal source install:

```bash
pip install .
```

Building from source requires a Rust toolchain. The Makefile uses
`uv run --with maturin` for local development and builds the extension in place,
so you do not need to install `maturin` into the active environment manually.

For publishing, build a normal interpreter-specific wheel for Python 3.14t and
an `abi3` wheel for regular CPython:

```bash
make wheel-314t  # requires python3.14t on PATH
make wheel-abi3  # regular CPython 3.9+ abi3 wheel
```

## Quick Example

```python
import datetime
import jlogger as jlog

jlog.setTimeFormat(jlog.TimeFormat.RFC3339)
logger = jlog.getLogger("trade")

if __name__ == "__main__":

    # build scoped logger once
    btc_logger = logger.with_value("symbol", "BTCUSDT")
    eth_logger = logger.with_value("symbol", "ETHUSDT")

    btc_logger.info().with_value("price", 65000).msg("tick")
    eth_logger.info().with_value("price", 3200).msg("tick")
```

Example output:

```json
{"time":"2026-02-21T16:03:32.703149","logger":"trade","level":"info","message":"tick","symbol":"BTCUSDT","price":65000}
{"time":"2026-02-21T16:03:32.703149","logger":"trade","level":"info","message":"tick","symbol":"ETHUSDT","price":3200}
```

The old camel-case API remains supported. Snake-case aliases are also available:

```python
import jlogger as jlog

jlog.set_time_format(jlog.TimeFormat.RFC3339)
logger = jlog.get_logger("trade").with_values(symbol="BTCUSDT")
logger.info().with_values(price=65000).msg("tick")
```

## Development

```bash
make develop  # build the Rust extension in place
make test     # run Python unit tests
make check    # run cargo check and tests
make build    # build wheel and sdist into dist/
make wheel-314t
make wheel-abi3
```

## More Examples

See the [`examples/`](examples/) directory for additional usage patterns.
