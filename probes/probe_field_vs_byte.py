#!/usr/bin/env python3
"""
probe_field_vs_byte.py
======================

Separates the two terms of the indexing cost that campaign 1 grew together.

WHY THIS EXISTS
---------------
The published result is that a mutation's cost rises with the *indexed content*
the document carries and the mutation never touches. Campaign 1 grew indexed
field count (1 → 17) and indexed byte volume (8 KB → 136 KB) in lockstep, because
every ballast field was an 8 000-byte string. Neither share is recoverable from
that run, so the per-field rate that appeared in one revision of the article was
withdrawn. This probe recovers them.

WHY NOT THREE ARMS AT CONSTANT SIZE
-----------------------------------
The obvious design — many short fields / reference / few long fields, all at one
document size — is not executable. The Data API refuses any indexed string above
8 000 bytes, so at 128 KB of indexed content the MINIMUM field count is 17, which
is the reference arm itself. "Few long fields" does not exist at that size. The
campaign brief proposed those three arms; they collapse to two, and one of the
two is the run we already have.

The executable design is two series, each holding one term constant:

  SERIES 1 — field count FIXED, bytes per field VARY
      16 fields at 512 / 1024 / 2048 / 4096 / 8000 bytes
      → totals 8 KB … 125 KB.  Slope here is the PER-BYTE term.

  SERIES 2 — total indexed bytes FIXED, field count VARIES   ← the decisive one
      64 KB of indexed content, carried as
      9 / 16 / 32 / 64 / 128 fields (7281 / 4096 / 2048 / 1024 / 512 bytes each)
      → a 14× range in field count at constant volume.
      Slope here is the PER-FIELD term.

Read series 2 first. If latency is flat across it, the cost is carried by bytes
and the article's wording — "how many indexed fields" — is wrong and must be
rewritten. If it rises materially, field count is an independent driver and the
withdrawn rate can be restated, this time with a protocol that licenses it.

METHODOLOGICAL COMMITMENTS
--------------------------
Two passes per configuration, not one: campaign 1 was weakened by an indexed arm
executed once. Five warm-ups discarded, thirty timed repetitions, medians only —
no mean is computed anywhere in this file, by construction. A same-size read
control at every configuration. The updateOne HTTP payload is recorded at every
configuration so that a constant payload can be shown rather than assumed.

USAGE
-----
    export DATA_API_ENDPOINT="http://127.0.0.1:8181"
    export DATA_API_TOKEN="..."

    python3 probe_field_vs_byte.py --keyspace ks --dry-run      # plan only
    python3 probe_field_vs_byte.py --keyspace ks --out findings_fieldbyte.json
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

INDEXED_STRING_CAP = 8000          # SHRED_DOC_LIMIT_VIOLATION above this
PROPERTIES_CAP = 1000              # per indexable object


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

@dataclass
class Config:
    label: str
    series: str
    n_fields: int
    bytes_per_field: int

    @property
    def total_bytes(self) -> int:
        return self.n_fields * self.bytes_per_field

    def validate(self) -> list[str]:
        errs = []
        if self.bytes_per_field > INDEXED_STRING_CAP:
            errs.append(f"{self.label}: {self.bytes_per_field} B/field exceeds the "
                        f"{INDEXED_STRING_CAP} B indexed-string cap")
        if self.n_fields > PROPERTIES_CAP:
            errs.append(f"{self.label}: {self.n_fields} fields exceeds the "
                        f"{PROPERTIES_CAP}-property cap")
        return errs


def build_plan() -> list[Config]:
    plan: list[Config] = []

    # SERIES 1 — field count fixed at 16, bytes per field vary.
    for b in (512, 1024, 2048, 4096, 8000):
        plan.append(Config(f"S1-16x{b}B", "bytes-vary-fields-fixed", 16, b))

    # SERIES 2 — total indexed bytes fixed at 64 KiB, field count varies.
    # 9 is the minimum field count that keeps every field under the cap at 64 KiB.
    total = 64 * 1024
    for n in (9, 16, 32, 64, 128):
        per = total // n
        plan.append(Config(f"S2-{n}x{per}B", "fields-vary-bytes-fixed", n, per))

    return plan


# ---------------------------------------------------------------------------
# Statistics — percentiles only, never a mean
# ---------------------------------------------------------------------------

def distribution(samples_ms: list[float]) -> dict[str, Any]:
    if not samples_ms:
        return {}
    s = sorted(samples_ms)

    def pct(p: float) -> float:
        if len(s) == 1:
            return round(s[0], 3)
        k = (len(s) - 1) * p
        lo, hi = int(k), min(int(k) + 1, len(s) - 1)
        return round(s[lo] + (s[hi] - s[lo]) * (k - lo), 3)

    return {"n": len(s), "min_ms": round(s[0], 3), "p50_ms": pct(0.50),
            "p95_ms": pct(0.95), "p99_ms": pct(0.99), "max_ms": round(s[-1], 3),
            "stdev_ms": round(statistics.pstdev(s), 3) if len(s) > 1 else 0.0}


def slope_report(points: list[tuple[float, float]], x_name: str) -> dict[str, Any]:
    """Least-squares slope plus the endpoint ratio. Both are reported because a
    ratio hides curvature and a slope hides a bad fit; disagreement between them
    is itself a finding."""
    if len(points) < 2:
        return {}
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
    # coefficient of determination, to say how well a straight line describes it
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (my + slope * (x - mx))) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return {
        "x": x_name,
        "slope_ms_per_unit": round(slope, 6),
        "r2": round(r2, 4),
        "endpoint_ratio": round(ys[-1] / ys[0], 3) if ys[0] else None,
        "x_range": [xs[0], xs[-1]],
        "y_range_ms": [round(ys[0], 3), round(ys[-1], 3)],
    }


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def make_doc(doc_id: str, cfg: Config) -> dict[str, Any]:
    d: dict[str, Any] = {"_id": doc_id, "status": "PENDING"}
    for i in range(cfg.n_fields):
        d[f"b{i:03d}"] = "x" * cfg.bytes_per_field
    return d


def run_config(coll, cfg: Config, reps: int, warmup: int) -> dict[str, Any]:
    doc_id = f"fb-{cfg.label}-{uuid.uuid4()}"
    coll.insert_one(make_doc(doc_id, cfg))

    for _ in range(warmup):
        coll.update_one({"_id": doc_id}, {"$set": {"status": "WARM"}})

    upd: list[float] = []
    for i in range(reps):
        t0 = time.perf_counter()
        coll.update_one({"_id": doc_id}, {"$set": {"status": f"S{i}"}})
        upd.append((time.perf_counter() - t0) * 1000.0)

    rd: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter()
        coll.find_one({"_id": doc_id})
        rd.append((time.perf_counter() - t0) * 1000.0)

    try:
        coll.delete_one({"_id": doc_id})
    except Exception:  # noqa: BLE001
        pass

    return {"update": distribution(upd), "read_control": distribution(rd)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--collection", default="fieldbyte_probe")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--passes", type=int, default=2,
                    help="two by default; one pass is what weakened campaign 1")
    ap.add_argument("--out", default="findings_fieldbyte.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plan = build_plan()
    errs = [e for c in plan for e in c.validate()]
    print("\nPLAN", file=sys.stderr)
    print(f"{'label':<16}{'series':<26}{'fields':>7}{'B/field':>9}{'total KB':>10}",
          file=sys.stderr)
    for c in plan:
        print(f"{c.label:<16}{c.series:<26}{c.n_fields:>7}{c.bytes_per_field:>9}"
              f"{c.total_bytes/1024:>10.1f}", file=sys.stderr)
    if errs:
        print("\nPLAN INVALID:", file=sys.stderr)
        for e in errs:
            print("  ·", e, file=sys.stderr)
        return 2
    print(f"\n{len(plan)} configurations × {args.passes} passes × "
          f"{args.reps} reps (+{args.warmup} warm-ups discarded)\n", file=sys.stderr)

    if args.dry_run:
        print("dry run: nothing written, nothing measured.", file=sys.stderr)
        return 0

    endpoint = os.environ.get("DATA_API_ENDPOINT")
    if not endpoint:
        print("DATA_API_ENDPOINT is not set.", file=sys.stderr)
        return 2
    try:
        from astrapy import DataAPIClient
        from astrapy.constants import Environment
    except ImportError:
        print("pip install astrapy", file=sys.stderr)
        return 2

    db = DataAPIClient(os.environ.get("DATA_API_TOKEN", ""),
                       environment=Environment.HCD).get_database(
                           endpoint, keyspace=args.keyspace)
    try:
        coll = db.create_collection(args.collection)
    except Exception:  # noqa: BLE001
        coll = db.get_collection(args.collection)

    results: dict[str, Any] = {}
    for p in range(1, args.passes + 1):
        for c in plan:
            key = f"{c.label}|pass{p}"
            print(f"  [{key}] …", file=sys.stderr)
            results[key] = {"config": asdict(c), "total_bytes": c.total_bytes,
                            **run_config(coll, c, args.reps, args.warmup)}
            print(f"      update p50 {results[key]['update']['p50_ms']} ms · "
                  f"read p50 {results[key]['read_control']['p50_ms']} ms",
                  file=sys.stderr)

    # ---- slopes, per series, per pass ------------------------------------
    analysis: dict[str, Any] = {}
    for p in range(1, args.passes + 1):
        s1 = [(c.bytes_per_field, results[f"{c.label}|pass{p}"]["update"]["p50_ms"])
              for c in plan if c.series.startswith("bytes-vary")]
        s2 = [(c.n_fields, results[f"{c.label}|pass{p}"]["update"]["p50_ms"])
              for c in plan if c.series.startswith("fields-vary")]
        analysis[f"pass{p}"] = {
            "series1_per_byte_at_fixed_field_count": slope_report(s1, "bytes per field"),
            "series2_per_field_at_fixed_volume": slope_report(s2, "field count"),
        }

    # ---- free internal control -------------------------------------------
    # 16 fields x 4096 B appears in both series, so the same configuration is
    # measured twice per pass under two labels. Agreement between them bounds
    # run-to-run noise; disagreement invalidates every slope above.
    control: dict[str, Any] = {}
    for p_ in range(1, args.passes + 1):
        a = results.get(f"S1-16x4096B|pass{p_}", {}).get("update", {}).get("p50_ms")
        b = results.get(f"S2-16x4096B|pass{p_}", {}).get("update", {}).get("p50_ms")
        if a and b:
            spread = abs(a - b) / min(a, b)
            control[f"pass{p_}"] = {
                "S1_p50_ms": a, "S2_p50_ms": b,
                "relative_spread": round(spread, 4),
                "verdict": "consistent" if spread <= 0.10 else
                           "NOISE EXCEEDS 10% — slopes below are not trustworthy",
            }

    verdicts = []
    for p in range(1, args.passes + 1):
        s2 = analysis[f"pass{p}"]["series2_per_field_at_fixed_volume"]
        r = s2.get("endpoint_ratio")
        if r is None:
            verdicts.append("INCONCLUSIVE")
        elif r <= 1.15:
            verdicts.append("BYTES DOMINATE")
        elif r >= 1.5:
            verdicts.append("FIELD COUNT IS AN INDEPENDENT DRIVER")
        else:
            verdicts.append("INCONCLUSIVE")

    record = {
        "probe": "probe_field_vs_byte.py",
        "version": "1.0",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "design_note": ("Three arms at one constant document size are NOT executable: "
                        "the 8 000-byte indexed-string cap makes 17 the minimum field "
                        "count at 128 KB, which is the reference arm itself. Two series "
                        "are used instead, each holding one term constant."),
        "decisive_series": "series 2 — field count varies at constant indexed volume",
        "verdict_rule": ("series-2 endpoint ratio <= 1.15 → bytes dominate; "
                         ">= 1.5 → field count is an independent driver; "
                         "between → inconclusive"),
        "verdict_per_pass": verdicts,
        "internal_control_same_config_in_both_series": control,
        "analysis": analysis,
        "results": results,
        "conditions": {
            "endpoint": endpoint, "keyspace": args.keyspace,
            "collection": args.collection, "reps": args.reps,
            "warmup_discarded": args.warmup, "passes": args.passes,
            "client_platform": platform.platform(), "python": sys.version.split()[0],
            "TO_BE_COMPLETED_BY_HAND": {
                "product_and_version": "read from the node, not the docs",
                "topology": "nodes, datacentres, racks, replication factor",
                "node_hardware": "vCPU, RAM, storage class of the data volume",
                "working_set_vs_ram": "in-cache or disk-bound; state which, with evidence",
                "sstables_and_compactions": "counts before and after; a disk-bound claim needs proof",
                "durability_settings": "commitlog sync mode and any non-default consistency",
                "http_payload_per_config": "record request/response bytes; constancy must be shown, not assumed",
            },
        },
        "publication_note": ("Characterises one build on one machine under one workload. "
                             "Publish the verdict and the method; publish the numbers only "
                             "alongside every field of 'conditions' above, completed. "
                             "Licenses no comparison with any other vendor's product."),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)

    print("\n" + "=" * 72, file=sys.stderr)
    for p, v in enumerate(verdicts, 1):
        s2 = analysis[f"pass{p}"]["series2_per_field_at_fixed_volume"]
        print(f"  pass {p}: {v}   (series-2 endpoint ratio "
              f"{s2.get('endpoint_ratio')}, r² {s2.get('r2')})", file=sys.stderr)
    if len(set(verdicts)) > 1:
        print("  PASSES DISAGREE — report both, conclude neither.", file=sys.stderr)
    for k, v in control.items():
        print(f"  control {k}: {v['verdict']} (spread {v['relative_spread']:.1%})",
              file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f"\nRecord written to {args.out}\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
