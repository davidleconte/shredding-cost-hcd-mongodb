#!/usr/bin/env python3
"""Every file under data/raw/ must parse, and every latency distribution in it
must be internally ordered.

A "latency distribution object" here is any JSON object that carries a central
quantile (p50, p50_ms or median) together with at least one other order
statistic. For each one the checker asserts the only thing a summary can be
asked to prove about itself:

    min <= p10 <= p50 <= p90 <= p95 <= p99 <= p999 <= max      and      n >= 1

over whichever of those keys are actually present. A percentile out of order, or
a sample size of zero, means the record is corrupt or was assembled by hand — in
either case no claim may rest on it.

This is an internal-consistency check. It cannot tell whether the numbers are
true, only whether they are self-consistent. See the header of
.github/workflows/verify-evidence.yml for what CI can and cannot establish.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO / "data" / "raw"

# Canonical order. Each entry: (rank label, accepted key spellings).
ORDER = [
    ("min", ("min_ms", "min_us", "min")),
    ("p10", ("p10_ms", "p10")),
    ("p50", ("p50_ms", "p50", "median_ms", "median")),
    ("p90", ("p90_ms", "p90")),
    ("p95", ("p95_ms", "p95")),
    ("p99", ("p99_ms", "p99")),
    ("p999", ("p999_ms", "p999")),
    ("max", ("max_ms", "max_us", "max")),
]
CENTRAL = {"p50_ms", "p50", "median_ms", "median"}


def numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def extract(obj: dict) -> list[tuple[str, str, float]] | None:
    """Return the ordered statistics present, or None if this is not a distribution."""
    found = []
    for label, spellings in ORDER:
        for key in spellings:
            if key in obj and numeric(obj[key]):
                found.append((label, key, float(obj[key])))
                break
    if len(found) < 2:
        return None
    if not any(key in CENTRAL for _, key, _ in found):
        return None
    return found


def walk(node, path: str, out: list[tuple[str, dict]]) -> None:
    if isinstance(node, dict):
        if extract(node) is not None:
            out.append((path or "$", node))
        for key, value in node.items():
            walk(value, f"{path}.{key}", out)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            walk(value, f"{path}[{index}]", out)


def main() -> int:
    files = sorted(p for p in EVIDENCE_DIR.rglob("*.json") if p.is_file())
    if not files:
        print(f"FAIL: no JSON under {EVIDENCE_DIR}", file=sys.stderr)
        return 1

    problems: list[str] = []
    n_dists = 0

    for path in files:
        rel = path.relative_to(REPO)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            problems.append(f"{rel}: does not parse: {exc}")
            continue

        distributions: list[tuple[str, dict]] = []
        walk(document, "", distributions)
        n_dists += len(distributions)

        for where, obj in distributions:
            stats = extract(obj)
            assert stats is not None
            for (lo_label, lo_key, lo), (hi_label, hi_key, hi) in zip(stats, stats[1:]):
                if lo > hi:
                    problems.append(
                        f"{rel}:{where}: {lo_key}={lo} > {hi_key}={hi} "
                        f"({lo_label} must not exceed {hi_label})"
                    )
            if "n" in obj:
                count = obj["n"]
                if not isinstance(count, int) or isinstance(count, bool) or count < 1:
                    problems.append(f"{rel}:{where}: n={count!r} is not an integer >= 1")

    for item in problems:
        print(f"INVALID {item}")

    if problems:
        print(f"\nFAIL: {len(problems)} problems across {len(files)} evidence files.", file=sys.stderr)
        return 1

    print(
        f"OK: {len(files)} evidence files parse; "
        f"{n_dists} latency distributions satisfy min <= ... <= max and n >= 1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
