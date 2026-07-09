"""Run the jlogger benchmark across multiple Python versions and print a matrix.

For each Python version it launches ``bench.py --json`` in an ephemeral ``uv``
environment (installing the comparison libraries automatically), then prints,
per scenario, a table of **logs/sec** and **speed-up** with one column per
Python version. Speed-up is relative to the ``stdlib + custom JSON`` baseline
(= 1.00x) measured on that same version.

Usage:
    python benchmarks/run_versions.py                     # default version set
    python benchmarks/run_versions.py 3.11 3.12 3.14 3.14t
    python benchmarks/run_versions.py --iterations 100000 --repeat 5

Requires ``uv`` on PATH. Versions that uv cannot provide are skipped with a
warning.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
BENCH = REPO_ROOT / "benchmarks" / "bench.py"
BASELINE = "stdlib + custom JSON"

DEFAULT_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14", "3.14t"]

# Fixed row order (loggers), fastest-typical first.
LOGGER_ORDER = [
    "jlogger (native)",
    "jlogger (pure-py)",
    "structlog",
    BASELINE,
    "python-json-logger",
]

SCENARIO_ORDER = [
    "Info, message only",
    "Info, message + 5 fields",
    "Info, large nested payload",
    "Disabled (below level, suppressed)",
]


def run_one(version: str, iterations: int, repeat: int) -> Optional[dict]:
    cmd = [
        "uv", "run", "--python", version,
        "--with", "structlog", "--with", "python-json-logger",
        "python", str(BENCH),
        "--json", "--iterations", str(iterations), "--repeat", str(repeat),
    ]
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT))
    print(f"  running {version} ...", file=sys.stderr, flush=True)
    proc = subprocess.run(
        cmd, cwd=str(REPO_ROOT), env=env,
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()[-3:]
        print(f"  ! {version} skipped: {' / '.join(tail)}", file=sys.stderr)
        return None
    lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
    try:
        return json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError):
        print(f"  ! {version} skipped: could not parse output", file=sys.stderr)
        return None


def fmt_cell(logs_per_sec: Optional[float], baseline: Optional[float]) -> str:
    if logs_per_sec is None:
        return "-"
    speed = f"{logs_per_sec / baseline:.2f}x" if baseline else "-"
    return f"{logs_per_sec:,.0f} ({speed})"


def render_matrix(results: Dict[str, dict]) -> str:
    labels = [results[v]["label"] for v in results]  # column headers
    out: List[str] = []

    for scenario in SCENARIO_ORDER:
        # collect which loggers appear in this scenario
        present = []
        for logger in LOGGER_ORDER:
            if any(logger in results[v]["scenarios"].get(scenario, {}) for v in results):
                present.append(logger)
        if not present:
            continue

        out.append(f"#### {scenario}")
        out.append("_logs/sec (speed-up vs stdlib)_")
        out.append("")
        header = ["logger"] + labels
        out.append("| " + " | ".join(header) + " |")
        out.append("| " + " | ".join("---" for _ in header) + " |")

        for logger in present:
            cells = [logger]
            for v in results:
                sc = results[v]["scenarios"].get(scenario, {})
                base = sc.get(BASELINE)
                cells.append(fmt_cell(sc.get(logger), base))
            out.append("| " + " | ".join(cells) + " |")
        out.append("")

    return "\n".join(out)


def render_variation(results: Dict[str, dict]) -> str:
    """Report how much jlogger's speed-up varies across versions."""
    scenario = "Info, message + 5 fields"
    speedups = []
    for v in results:
        sc = results[v]["scenarios"].get(scenario, {})
        base = sc.get(BASELINE)
        jl = sc.get("jlogger (native)") or sc.get("jlogger (pure-py)")
        if base and jl:
            speedups.append(jl / base)
    if len(speedups) < 2:
        return ""
    lo, hi = min(speedups), max(speedups)
    spread = (hi - lo) / lo * 100
    verdict = (
        "differences between versions are small — a single table is fine."
        if spread < 15
        else "versions differ enough to be worth showing separately."
    )
    return (
        f"jlogger speed-up on '{scenario}' ranges {lo:.2f}x–{hi:.2f}x "
        f"across versions ({spread:.0f}% spread); {verdict}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("versions", nargs="*", default=None,
                        help="Python versions to test (default: %s)" % " ".join(DEFAULT_VERSIONS))
    parser.add_argument("--iterations", type=int, default=50_000)
    parser.add_argument("--repeat", type=int, default=5)
    args = parser.parse_args()

    versions = args.versions or DEFAULT_VERSIONS

    print(f"Benchmarking across {len(versions)} Python versions "
          f"(iterations={args.iterations:,}, repeat={args.repeat})", file=sys.stderr)

    results: Dict[str, dict] = {}
    for v in versions:
        payload = run_one(v, args.iterations, args.repeat)
        if payload is not None:
            results[v] = payload

    if not results:
        print("No versions ran successfully.", file=sys.stderr)
        raise SystemExit(1)

    versions_run = ", ".join(f"{results[v]['label']} ({results[v]['python']})" for v in results)
    print(f"\njlogger benchmark matrix  |  {versions_run}")
    print(f"iterations={args.iterations:,}  repeat={args.repeat}  "
          f"baseline='{BASELINE}' (= 1.00x)\n")
    print(render_matrix(results))
    note = render_variation(results)
    if note:
        print(note)


if __name__ == "__main__":
    main()
