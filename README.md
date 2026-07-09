# jlogger

A fast, minimal structured JSON logger for Python, with a Go-style
(`zerolog`/`zap`) fluent API.

`jlogger` keeps a tiny Python interface and builds JSON in Rust through a PyO3
extension, so it does not depend on `orjson` and works on modern CPython
builds, including free-threaded Python 3.14t.

It writes formatted JSON straight to an output stream (default `stderr`,
override with `setOutput`) instead of going through the stdlib `logging`
pipeline — no `LogRecord`, no caller stack walk, no handler locks — which is
what makes it fast.

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
| **jlogger (native)** |  1.416 |  706,155 |   65.8 |        98 |
| structlog            |  4.549 |  219,853 |   19.3 |        92 |
| stdlib + custom JSON |  5.530 |  180,825 |   17.5 |       102 |
| python-json-logger   |  7.327 |  136,480 |   15.4 |       118 |

**Info, message + 5 fields**

| logger               |  µs/op | logs/sec | MB/sec | bytes/log |
| -------------------- | -----: | -------: | -----: | --------: |
| **jlogger (native)** |  2.322 |  430,610 |   87.0 |       212 |
| structlog            |  5.449 |  183,526 |   37.8 |       216 |
| stdlib + custom JSON |  6.680 |  149,692 |   30.8 |       216 |
| python-json-logger   |  8.958 |  111,629 |   25.8 |       242 |

**Info, large nested payload**

| logger               |   µs/op | logs/sec | MB/sec | bytes/log |
| -------------------- | ------: | -------: | -----: | --------: |
| **jlogger (native)** |   6.066 |  164,861 |   85.5 |       544 |
| structlog            |   7.898 |  126,614 |   71.5 |       592 |
| stdlib + custom JSON |   9.239 |  108,239 |   56.5 |       548 |
| python-json-logger   |  11.610 |   86,131 |   50.8 |       618 |

**Disabled** (call below the active level — should be near-free): `jlogger`
suppresses ~3.8M calls/sec (0.27 µs/op) via a shared no-op event, ahead of
`structlog` (~1.3M/sec).

Takeaways:

- `jlogger` is the fastest here — roughly **2–3× `structlog`** (the fastest
  pure-Python structured logger) and **3–5×** the stdlib and
  `python-json-logger` approaches for typical payloads.
- The win comes from bypassing the stdlib `logging` pipeline: no `LogRecord`,
  no `findCaller()` stack walk, no handler-lock hierarchy. Formatting happens in
  Rust and the line is written straight to the stream. Scoped loggers share
  their context dict copy-on-write, so `.info().msg(...)` allocates almost
  nothing.
- Unlike `orjson`-based setups, `jlogger`'s native encoder builds and runs on
  free-threaded CPython 3.14t (where it is even faster — see `make bench-314t`);
  on platforms with no matching prebuilt binary it falls back to a pure-Python
  encoder automatically.

The full benchmark (including the "message only" and "disabled" cases and
`--iterations`/`--repeat` flags) lives in
[`benchmarks/bench.py`](benchmarks/bench.py).
