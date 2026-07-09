# jlogger

A fast, minimal structured JSON logger for Python, with a Go-style
(`zerolog`/`zap`) fluent API.

`jlogger` keeps a tiny Python interface and builds JSON in Rust through a PyO3
extension, so it does not depend on `orjson` and works on modern CPython
builds, including free-threaded Python 3.14t.

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

> Use the `git+https://` prefix — a bare `https://.../jlogger.git` URL is not
> recognized by pip/uv as a VCS source.

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

`jlogger` is benchmarked against three common ways to emit JSON logs in Python:

| Contender              | What it is                                             |
| ---------------------- | ------------------------------------------------------ |
| `jlogger`              | this library (Rust-backed encoder)                     |
| `stdlib + custom JSON` | `logging.Logger` with a hand-written JSON formatter    |
| `python-json-logger`   | popular `logging.Formatter` that renders JSON          |
| `structlog`            | popular structured logger with `JSONRenderer`          |

Every contender writes to an in-memory counting stream (bytes and lines are
tallied, output is discarded), so the numbers measure formatting + dispatch
throughput, not disk speed. Higher `logs/sec` and `MB/sec` are better; lower
`µs/op` is better. Byte counts differ slightly because each library formats the
record differently.

Results below are from CPython 3.12 on x86_64 (`iterations=50,000`, best of 5).
Numbers are relative — rerun on your machine with `make bench`
(or `make bench-314t` for free-threaded Python).

**Info, message only**

| logger               |  µs/op | logs/sec | MB/sec | bytes/log |
| -------------------- | -----: | -------: | -----: | --------: |
| structlog            |  4.487 |  222,868 |   19.6 |        92 |
| **jlogger (native)** |  4.734 |  211,227 |   20.7 |       103 |
| stdlib + custom JSON |  5.496 |  181,963 |   17.7 |       102 |
| python-json-logger   |  7.224 |  138,426 |   15.6 |       118 |

**Info, message + 5 fields**

| logger               |  µs/op | logs/sec | MB/sec | bytes/log |
| -------------------- | -----: | -------: | -----: | --------: |
| structlog            |  5.445 |  183,659 |   37.8 |       216 |
| **jlogger (native)** |  5.728 |  174,580 |   36.1 |       217 |
| stdlib + custom JSON |  6.620 |  151,050 |   31.1 |       216 |
| python-json-logger   |  8.853 |  112,955 |   26.1 |       242 |

**Info, large nested payload**

| logger               |   µs/op | logs/sec | MB/sec | bytes/log |
| -------------------- | ------: | -------: | -----: | --------: |
| structlog            |   7.839 |  127,566 |   72.0 |       592 |
| stdlib + custom JSON |   9.078 |  110,151 |   57.5 |       548 |
| **jlogger (native)** |   9.599 |  104,178 |   54.5 |       549 |
| python-json-logger   |  11.517 |   86,829 |   51.2 |       618 |

**Disabled** (call below the active level — should be near-free): `jlogger`
suppresses ~2.3M calls/sec (0.44 µs/op) before doing any formatting.

Takeaways:

- `jlogger` is on par with `structlog` — the fastest pure-Python structured
  logger here — and clearly faster than the stdlib and `python-json-logger`
  approaches for typical payloads.
- `structlog` edges ahead mainly because it bypasses the stdlib `logging`
  pipeline, while `jlogger`, `stdlib`, and `python-json-logger` all pay for
  `LogRecord` creation and the handler lock.
- Unlike `orjson`-based setups, `jlogger`'s native encoder builds and runs on
  free-threaded CPython 3.14t; on platforms with no matching prebuilt binary it
  falls back to a pure-Python encoder automatically.

The full benchmark (including the "message only" and "disabled" cases and
`--iterations`/`--repeat` flags) lives in
[`benchmarks/bench.py`](benchmarks/bench.py).
