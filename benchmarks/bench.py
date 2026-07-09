"""Benchmark jlogger against other Python JSON loggers.

Compares four ways of emitting structured JSON logs:

  * jlogger              (this library, Rust-backed encoder)
  * stdlib + custom JSON (logging.Logger with a hand-written JSON formatter)
  * python-json-logger   (popular logging.Formatter that renders JSON)
  * structlog            (popular structured logger, JSONRenderer)

Every contender writes to an in-memory counting stream (bytes/lines are
tallied, output is discarded), so we measure formatting + dispatch throughput
without disk or terminal noise. Missing optional libraries are skipped.

Run (installs the comparison libs into an ephemeral env):

    PYTHONPATH=. uv run --with structlog --with python-json-logger \
        python benchmarks/bench.py

Options:
    --iterations N   log lines per timed run (default 50000)
    --repeat R       timed runs per case, averaged (default 5)
    --markdown       print GitHub-flavored Markdown tables (default)
    --plain          print aligned plain-text tables
    --json           emit machine-readable JSON (used by run_versions.py)

Each table shows only two metrics: logs/sec and speed-up relative to the
'stdlib + custom JSON' baseline (defined as 1.00x). To compare across Python
versions, use benchmarks/run_versions.py.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Shared fixtures
# --------------------------------------------------------------------------- #

MESSAGE = "request completed"
FIELDS = {
    "service": "api",
    "request_id": "b3f1c2e4-1a2b-4c3d-9e8f-0a1b2c3d4e5f",
    "user_id": 4242,
    "latency_ms": 12.5,
    "status": 200,
}

# A larger, nested payload: this is where JSON *encoding* cost dominates and
# the Rust core has room to win over pure-Python json.dumps.
NESTED = {
    "service": "api",
    "request": {
        "id": "b3f1c2e4-1a2b-4c3d-9e8f-0a1b2c3d4e5f",
        "method": "POST",
        "path": "/v1/orders",
        "headers": {"content-type": "application/json", "x-trace": "abc123"},
        "query": {"page": 1, "size": 50, "sort": "-created"},
    },
    "user": {"id": 4242, "tier": "gold", "roles": ["admin", "trader"]},
    "items": [
        {"sku": "BTC", "qty": 2, "price": 65000.5},
        {"sku": "ETH", "qty": 10, "price": 3200.0},
        {"sku": "SOL", "qty": 100, "price": 145.25},
    ],
    "latency_ms": 12.5,
    "status": 200,
    "ok": True,
}


class CountingStream(io.TextIOBase):
    """A text stream that counts bytes/lines written and discards the data."""

    def __init__(self) -> None:
        self.n_bytes = 0
        self.n_lines = 0

    def write(self, s) -> int:  # type: ignore[override]
        if isinstance(s, bytes):
            self.n_bytes += len(s)
            self.n_lines += s.count(b"\n")
        else:
            self.n_bytes += len(s.encode("utf-8"))
            self.n_lines += s.count("\n")
        return len(s)

    def flush(self) -> None:  # noqa: D401 - stream API
        pass

    def reset(self) -> None:
        self.n_bytes = 0
        self.n_lines = 0


@dataclass
class Contender:
    name: str
    stream: CountingStream
    simple: Callable[[], None]
    fields: Callable[[], None]
    nested: Callable[[], None]
    disabled: Callable[[], None]


@dataclass
class Result:
    logger: str
    scenario: str
    per_op_us: float
    ops_per_sec: float
    lines_per_sec: float
    mb_per_sec: float
    bytes_per_log: float


# --------------------------------------------------------------------------- #
# Contender builders
# --------------------------------------------------------------------------- #


def build_jlogger() -> Optional[Contender]:
    try:
        import jlogger as jlog
    except Exception:
        return None

    stream = CountingStream()
    jlog.set_output(stream)

    info_logger = jlog.getLogger("bench.jlogger", level="info")
    off_logger = jlog.getLogger("bench.jlogger", level="warning")

    label = "jlogger"
    try:
        from jlogger._encoder import has_native_encoder

        label = "jlogger (native)" if has_native_encoder() else "jlogger (pure-py)"
    except Exception:
        pass

    return Contender(
        name=label,
        stream=stream,
        simple=lambda: info_logger.info().msg(MESSAGE),
        fields=lambda: info_logger.info().with_values(**FIELDS).msg(MESSAGE),
        nested=lambda: info_logger.info().with_dict(NESTED).msg(MESSAGE),
        disabled=lambda: off_logger.info().with_values(**FIELDS).msg(MESSAGE),
    )


class _StdlibJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "time": record.created,
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, "fields", None)
        if fields:
            obj.update(fields)
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def build_stdlib() -> Optional[Contender]:
    stream = CountingStream()

    def make(name: str, level: int):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(_StdlibJsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(level)
        return logger

    info_logger = make("bench.stdlib.info", logging.INFO)
    off_logger = make("bench.stdlib.off", logging.WARNING)

    return Contender(
        name="stdlib + custom JSON",
        stream=stream,
        simple=lambda: info_logger.info(MESSAGE),
        fields=lambda: info_logger.info(MESSAGE, extra={"fields": FIELDS}),
        nested=lambda: info_logger.info(MESSAGE, extra={"fields": NESTED}),
        disabled=lambda: off_logger.info(MESSAGE, extra={"fields": FIELDS}),
    )


def build_python_json_logger() -> Optional[Contender]:
    try:
        try:
            from pythonjsonlogger.json import JsonFormatter
        except Exception:
            from pythonjsonlogger.jsonlogger import JsonFormatter
    except Exception:
        return None

    stream = CountingStream()
    fmt = JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    def make(name: str, level: int):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(level)
        return logger

    info_logger = make("bench.pjl.info", logging.INFO)
    off_logger = make("bench.pjl.off", logging.WARNING)

    return Contender(
        name="python-json-logger",
        stream=stream,
        simple=lambda: info_logger.info(MESSAGE),
        fields=lambda: info_logger.info(MESSAGE, extra=FIELDS),
        nested=lambda: info_logger.info(MESSAGE, extra=NESTED),
        disabled=lambda: off_logger.info(MESSAGE, extra=FIELDS),
    )


def build_structlog() -> Optional[Contender]:
    try:
        import structlog
    except Exception:
        return None

    stream = CountingStream()

    def make(min_level: int):
        return structlog.wrap_logger(
            structlog.PrintLogger(file=stream),
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(min_level),
        )

    info_logger = make(logging.INFO)
    off_logger = make(logging.WARNING)

    return Contender(
        name="structlog",
        stream=stream,
        simple=lambda: info_logger.info(MESSAGE),
        fields=lambda: info_logger.info(MESSAGE, **FIELDS),
        nested=lambda: info_logger.info(MESSAGE, **NESTED),
        disabled=lambda: off_logger.info(MESSAGE, **FIELDS),
    )


# --------------------------------------------------------------------------- #
# Timing
# --------------------------------------------------------------------------- #


def measure(fn: Callable[[], None], stream: CountingStream, n: int, repeat: int):
    total_elapsed = 0.0
    last_bytes = 0
    last_lines = 0
    for _ in range(repeat):
        stream.reset()
        start = time.perf_counter()
        for _ in range(n):
            fn()
        total_elapsed += time.perf_counter() - start
        # byte/line counts are deterministic across runs; keep the last.
        last_bytes = stream.n_bytes
        last_lines = stream.n_lines
    avg_elapsed = total_elapsed / repeat
    return avg_elapsed, last_bytes, last_lines


def run_scenario(
    contenders: List[Contender], attr: str, scenario: str, n: int, repeat: int
) -> List[Result]:
    results: List[Result] = []
    for c in contenders:
        fn = getattr(c, attr)
        # warm up
        for _ in range(min(1000, n)):
            fn()
        elapsed, nbytes, nlines = measure(fn, c.stream, n, repeat)
        ops_per_sec = n / elapsed
        lines_per_sec = nlines / elapsed if nlines else 0.0
        mb_per_sec = (nbytes / elapsed) / (1024 * 1024) if nbytes else 0.0
        bytes_per_log = (nbytes / nlines) if nlines else 0.0
        results.append(
            Result(
                logger=c.name,
                scenario=scenario,
                per_op_us=elapsed / n * 1e6,
                ops_per_sec=ops_per_sec,
                lines_per_sec=lines_per_sec,
                mb_per_sec=mb_per_sec,
                bytes_per_log=bytes_per_log,
            )
        )
    return results


# --------------------------------------------------------------------------- #
# Rendering  (only two metrics: logs/sec and speed-up vs the stdlib baseline)
# --------------------------------------------------------------------------- #

BASELINE = "stdlib + custom JSON"  # this contender is defined as 1.00x
HEADERS = ["logger", "logs/sec", "speed-up"]


def _speedups(results: List[Result]) -> Dict[str, float]:
    base = next((r.ops_per_sec for r in results if r.logger == BASELINE), None)
    out: Dict[str, float] = {}
    for r in results:
        out[r.logger] = (r.ops_per_sec / base) if base else float("nan")
    return out


def _row(r: Result, speedup: float) -> List[str]:
    return [r.logger, f"{r.ops_per_sec:,.0f}", f"{speedup:.2f}x"]


def render_markdown(scenario: str, results: List[Result]) -> str:
    speed = _speedups(results)
    rows = sorted(results, key=lambda r: r.ops_per_sec, reverse=True)
    lines = [f"#### {scenario}", ""]
    lines.append("| " + " | ".join(HEADERS) + " |")
    lines.append("| " + " | ".join("---" for _ in HEADERS) + " |")
    for r in rows:
        lines.append("| " + " | ".join(_row(r, speed[r.logger])) + " |")
    lines.append("")
    return "\n".join(lines)


def render_plain(scenario: str, results: List[Result]) -> str:
    speed = _speedups(results)
    rows = sorted(results, key=lambda r: r.ops_per_sec, reverse=True)
    table = [HEADERS] + [_row(r, speed[r.logger]) for r in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(HEADERS))]
    out = [scenario, ""]
    for idx, row in enumerate(table):
        out.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
        if idx == 0:
            out.append("  ".join("-" * widths[i] for i in range(len(HEADERS))))
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

SCENARIOS = [
    ("simple", "Info, message only"),
    ("fields", "Info, message + 5 fields"),
    ("nested", "Info, large nested payload"),
    ("disabled", "Disabled (below level, suppressed)"),
]


def _py_label() -> str:
    v = sys.version_info
    label = f"{v.major}.{v.minor}"
    if hasattr(sys, "_is_gil_enabled") and not sys._is_gil_enabled():
        label += "t"
    return label


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=50_000)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--plain", action="store_true", help="plain-text tables")
    parser.add_argument("--markdown", action="store_true", help="markdown tables")
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable JSON (for the matrix runner)"
    )
    args = parser.parse_args()

    builders = [
        build_jlogger,
        build_stdlib,
        build_python_json_logger,
        build_structlog,
    ]
    contenders = [c for c in (b() for b in builders) if c is not None]

    if not contenders:
        print("No loggers available to benchmark.", file=sys.stderr)
        raise SystemExit(1)

    n, repeat = args.iterations, args.repeat

    all_results = {
        title: run_scenario(contenders, attr, title, n, repeat)
        for attr, title in SCENARIOS
    }

    if args.json:
        payload = {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "label": _py_label(),
            "gil": not (hasattr(sys, "_is_gil_enabled") and not sys._is_gil_enabled()),
            "iterations": n,
            "repeat": repeat,
            "baseline": BASELINE,
            "scenarios": {
                title: {r.logger: r.ops_per_sec for r in results}
                for title, results in all_results.items()
            },
        }
        print(json.dumps(payload))
        return

    render = render_plain if args.plain else render_markdown
    py = f"CPython {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    gil = ""
    if hasattr(sys, "_is_gil_enabled"):
        gil = "  |  GIL: " + ("on" if sys._is_gil_enabled() else "off (free-threaded)")

    print(f"jlogger benchmark  |  {py}{gil}")
    print(f"iterations={n:,}  repeat={repeat}  (mean of {repeat} runs)")
    print(f"speed-up is relative to '{BASELINE}' (= 1.00x)\n")

    for _, title in SCENARIOS:
        print(render(title, all_results[title]))


if __name__ == "__main__":
    main()
