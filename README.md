# jlogger

A fast, minimal structured JSON logger for Python, with a Go-style
([`zerolog`][zerolog]/[`zap`][zap]) fluent API.

`jlogger` keeps a tiny Python interface and builds JSON in Rust through a PyO3
extension, so it does not depend on [`orjson`][orjson] and works on modern
CPython builds, including free-threaded Python 3.14t.

It writes formatted JSON straight to an output stream (default `stderr`,
override with `setOutput`) instead of going through the stdlib `logging`
pipeline — no `LogRecord`, no caller stack walk, no handler locks — which is
what makes it fast.

[zerolog]: https://github.com/rs/zerolog
[zap]: https://github.com/uber-go/zap
[orjson]: https://github.com/ijl/orjson

## Installation

`jlogger` ships **prebuilt native extensions** in the repo, so installing does
**not** require a Rust toolchain.

Install from a git URL:

```bash
# pip
pip install git+https://github.com/kimnt93/jlogger.git

# uv
uv pip install git+https://github.com/kimnt93/jlogger.git
```

Install from source:

```bash
git clone https://github.com/kimnt93/jlogger.git
cd jlogger
make install     # runs `pip install .`
```

## Quick Example

```python
import jlogger as jlog

jlog.setTimeFormat(jlog.TimeFormat.RFC3339)
logger = jlog.getLogger("trade")

if __name__ == "__main__":
    # build scoped loggers once
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

The camelCase API is the original; snake_case aliases are also available:

```python
import jlogger as jlog

jlog.set_time_format(jlog.TimeFormat.RFC3339)
logger = jlog.get_logger("trade").with_values(symbol="BTCUSDT")
logger.info().with_values(price=65000).msg("tick")
```

## More Examples

See the [`examples/`](examples/) directory:

| Example                     | Shows                                            |
| --------------------------- | ------------------------------------------------ |
| `levels.py`                 | Log levels and `setLevel` filtering              |
| `context.py`                | Per-request scoped context (request/user ids)    |
| `childs.py`                 | Scoped child loggers via `with_value`            |
| `structured_data.py`        | Nested dicts, lists, and `with_dict`             |
| `snake_case_api.py`         | snake_case aliases                               |
| `all_time_formats.py`       | All four `TimeFormat` options                    |
| `time_format.py`            | RFC3339 timestamps                               |
| `exception.py`              | Error logging with `with_error`                  |
| `threads.py`                | Concurrent logging from multiple threads         |
| `numpy_values.py`           | Logging NumPy scalars and arrays                 |

Run one with the repo on the path:

```bash
PYTHONPATH=. python examples/levels.py
```

## Benchmarks

Two metrics only: **logs/sec** (higher is better) and **speed-up** relative to
a stdlib `logging.Logger` + hand-written JSON formatter, which is the baseline
(**1.00×**). Contenders:

| Contender              | What it is                                             |
| ---------------------- | ------------------------------------------------------ |
| `jlogger`              | this library (Rust-backed encoder)                     |
| `stdlib + custom JSON` | [`logging`][logging] + hand-written JSON formatter (=1.00×) |
| `python-json-logger`   | popular [`logging.Formatter`][pjl] that renders JSON   |
| `structlog`            | popular [structured logger][structlog] with `JSONRenderer` |

[logging]: https://docs.python.org/3/library/logging.html
[pjl]: https://github.com/nhairs/python-json-logger
[structlog]: https://github.com/hynek/structlog

Every contender writes to an in-memory counting stream (output discarded), so
the numbers measure formatting + dispatch throughput, not disk speed.

Reference numbers below are CPython 3.12 on x86_64 (`iterations=50,000`, mean of
5 runs). The **speed-up** ratios are stable across CPython 3.10, 3.11, 3.12,
3.13, 3.14 and free-threaded 3.14t — `jlogger` stays ≈4.2–4.9× on message-only
and ≈2.8–3.1× with fields regardless of version — so a single table is shown
here. Reproduce the full per-version matrix with `make bench-matrix`.

**Info, message only**

| logger               | logs/sec | speed-up |
| -------------------- | -------: | -------: |
| **jlogger (native)** |  766,840 |    4.21× |
| structlog            |  220,833 |    1.21× |
| stdlib + custom JSON |  182,357 |    1.00× |
| python-json-logger   |  136,785 |    0.75× |

**Info, message + 5 fields**

| logger               | logs/sec | speed-up |
| -------------------- | -------: | -------: |
| **jlogger (native)** |  433,413 |    2.88× |
| structlog            |  180,388 |    1.20× |
| stdlib + custom JSON |  150,294 |    1.00× |
| python-json-logger   |  111,077 |    0.74× |

**Info, large nested payload**

| logger               | logs/sec | speed-up |
| -------------------- | -------: | -------: |
| **jlogger (native)** |  166,117 |    1.51× |
| structlog            |  127,499 |    1.16× |
| stdlib + custom JSON |  110,119 |    1.00× |
| python-json-logger   |   87,452 |    0.79× |

Reproduce:

```bash
make bench          # single interpreter (current uv default)
make bench-matrix   # across CPython 3.10–3.14 + 3.14t via uv
```

Both wrap [`benchmarks/bench.py`](benchmarks/bench.py) and
[`benchmarks/run_versions.py`](benchmarks/run_versions.py); pass
`--iterations`/`--repeat` to tune.
