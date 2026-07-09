# jlogger

A fast, minimal structured JSON logger for Python, with a Go-style
(`zerolog`/`zap`) fluent API.

`jlogger` keeps a tiny Python interface and builds JSON in Rust through a PyO3
extension, so it does not depend on `orjson` and works on modern CPython
builds, including free-threaded Python 3.14t.

## Installation

`jlogger` ships **prebuilt native extensions** in the repo, so installing does
**not** require a Rust toolchain. Pick whichever fits your workflow:

```bash
# from a git URL (pip)
pip install git+https://github.com/kimnt93/jlogger.git

# from a git URL (uv)
uv pip install git+https://github.com/kimnt93/jlogger.git

# from a local clone
git clone https://github.com/kimnt93/jlogger.git
cd jlogger
pip install .
```

> Use the `git+https://` prefix for git installs — a bare
> `https://.../jlogger.git` URL is not recognized by pip/uv as a VCS source.

### How it works across Python versions

The repo commits two native builds under `jlogger/`:

| File                                         | Used by                                   |
| -------------------------------------------- | ----------------------------------------- |
| `_native.abi3.so`                            | Regular CPython 3.9+ (single abi3 binary) |
| `_native.cpython-314t-x86_64-linux-gnu.so`   | Free-threaded CPython 3.14t               |

If no committed binary matches your interpreter or platform (e.g. macOS,
Windows, or a different CPU), `jlogger` transparently falls back to a
pure-Python JSON encoder — it still works, just without the Rust speedup. The
prebuilt binaries above are Linux/x86_64.

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

## Development

Building the native extension requires a Rust toolchain. The Makefile uses
`uv run --with maturin` so you do not need `maturin` in your active environment.

```bash
make native       # build abi3 .so (CPython 3.9+) into jlogger/ and commit it
make native-314t  # build free-threaded 3.14t .so into jlogger/ (needs python3.14t)
make native-all   # build both

make develop      # alias for `make native`
make install      # pip install . (uses the committed .so, no Rust)
make test         # run unit tests
make test-314t    # run unit tests under python3.14t
make check        # cargo check + Python tests
make fmt          # format Rust code
make build        # build sdist + wheel into dist/
make clean        # remove build artifacts (keeps committed .so)
```

### Releasing new binaries

After changing the Rust code, rebuild and commit the binaries so git installs
keep working without Rust:

```bash
make native-all
git add jlogger/_native.abi3.so jlogger/_native.cpython-314t-*.so
git commit -m "Rebuild native extensions"
```
