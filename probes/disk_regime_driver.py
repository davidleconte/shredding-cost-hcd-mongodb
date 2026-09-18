#!/usr/bin/env python3
"""
disk_regime_driver.py
=====================

Forces a disk-bound regime, PROVES it, and only then hands over to the cost
probes. Closes action item 1 of ADR-001.

WHY THIS EXISTS
---------------
Every latency published so far is a memtable latency. Across both earlier
campaigns no SSTable was flushed and no compaction was crossed, on either
topology. The engine described is one that never touched its disk, and the
central coefficient is a memtable-regime figure. Until that is fixed, no client
commitment can rest on any of it.

WHAT THIS DOES NOT DO
---------------------
It does not measure anything itself. It puts the cluster into a state, produces
evidence that the state was reached, and stops. Measurement is then the existing
harness — verify_storage_claims.py and probe_field_vs_byte.py — run against that
state. Keeping the two apart is deliberate: a driver that also measured would be
free to declare its own preconditions met.

THE PROOF OBLIGATION
--------------------
A run is disk-bound only if all four hold, and this script refuses to report
success unless it can evidence each:

  1. data on disk exceeds the memtable budget by a stated factor
  2. SSTables exist — Data.db count greater than zero, recorded before and after
  3. at least one compaction completed — counter read before and after
  4. caches were invalidated, and whatever could not be invalidated is named

Requires nodetool access on the node, and CQL for the counters.

USAGE
-----
    python3 disk_regime_driver.py --keyspace ks --collection coll \\
        --data-dir /var/lib/cassandra/data --target-multiple 3 \\
        --out disk_state.json

    # then, against the state it left:
    python3 probe_field_vs_byte.py --keyspace ks --out findings_fieldbyte_disk.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any


def sh(cmd: list[str], timeout: int = 180) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", f"not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s: {' '.join(cmd)}"


def nodetool(args_: list[str], nt: str) -> tuple[int, str, str]:
    return sh([nt] + args_)


def count_sstables(data_dir: str, keyspace: str) -> int:
    # Mechanical fix (campaign 3): the node is a container and the host volume is
    # root-only, so the SSTable evidence is read from inside the container via
    # docker exec rather than an in-process host walk. The proof obligation and
    # its threshold (Data.db count > 0) are unchanged; the count still comes from
    # the real node's data directory.
    rc, out, _ = sh(["docker", "exec", "p16-hcd-node1", "sh", "-c",
                     f"find {data_dir}/{keyspace} -name '*Data.db' 2>/dev/null | wc -l"])
    try:
        return int(out.strip() or "0")
    except ValueError:
        return 0


def dir_bytes(data_dir: str, keyspace: str) -> int:
    # Mechanical fix (campaign 3): read on-disk size from inside the container
    # (root-only host volume). Uses `du -sb` on the keyspace data directory.
    rc, out, _ = sh(["docker", "exec", "p16-hcd-node1", "sh", "-c",
                     f"du -sb {data_dir}/{keyspace} 2>/dev/null | cut -f1"])
    try:
        return int(out.strip() or "0")
    except ValueError:
        return 0


def compactions_completed(nt: str) -> int | None:
    rc, out, _ = nodetool(["compactionstats"], nt)
    if rc != 0:
        return None
    m = re.search(r"completed\D+(\d+)", out, flags=re.I)
    return int(m.group(1)) if m else None


def fill(coll, target_bytes: int, doc_bytes: int, report_every: int = 2000) -> int:
    """Insert until the target is plausibly exceeded. Uses an open loop with a
    modest fixed rate so the fill itself does not become a throughput test.

    Mechanical fix (campaign 3): the ballast is INCOMPRESSIBLE random text, a
    fresh value per document. A constant-byte payload ("x"*n) compressed ~120:1
    under the table's LZ4Compressor, so 6 GiB of logical data occupied 50 MiB on
    disk and the driver's on-disk-size proof correctly refused the run. Random
    base64 makes on-disk size track logical size; nothing else changes."""
    import base64
    written = 0
    n = 0
    raw = (doc_bytes * 3) // 4 + 1
    while written < target_bytes:
        payload = base64.b64encode(os.urandom(raw)).decode("ascii")[:doc_bytes]
        coll.insert_one({"_id": f"fill-{uuid.uuid4()}", "ballast": payload, "n": n})
        written += doc_bytes
        n += 1
        if n % report_every == 0:
            print(f"      {n} docs, ~{written/1024/1024:.0f} MiB submitted",
                  file=sys.stderr)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keyspace", required=True)
    ap.add_argument("--collection", default="disk_fill")
    ap.add_argument("--data-dir", required=True,
                    help="Cassandra data directory, for SSTable evidence")
    ap.add_argument("--nodetool", default="nodetool")
    ap.add_argument("--memtable-budget-mb", type=float, required=True,
                    help="memtable_heap_space + memtable_offheap_space, read from "
                         "the running config. Supplied by hand on purpose: the "
                         "script will not guess the number its proof depends on.")
    ap.add_argument("--target-multiple", type=float, default=3.0)
    ap.add_argument("--doc-bytes", type=int, default=4096)
    ap.add_argument("--out", default="disk_state.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    target = int(args.memtable_budget_mb * args.target_multiple * 1024 * 1024)
    print(f"\nTarget on-disk data: {target/1024/1024:.0f} MiB "
          f"({args.target_multiple}× a {args.memtable_budget_mb:.0f} MiB memtable "
          f"budget)\n", file=sys.stderr)

    ev: dict[str, Any] = {"before": {}, "after": {}, "steps": []}
    ev["before"]["sstables"] = count_sstables(args.data_dir, args.keyspace)
    ev["before"]["data_dir_bytes"] = dir_bytes(args.data_dir, args.keyspace)
    ev["before"]["compactions_completed"] = compactions_completed(args.nodetool)
    print(f"  before: {ev['before']['sstables']} SSTables, "
          f"{ev['before']['data_dir_bytes']/1024/1024:.1f} MiB, "
          f"compactions {ev['before']['compactions_completed']}", file=sys.stderr)

    if args.dry_run:
        print("\ndry run: no data written, no flush, no compaction.\n", file=sys.stderr)
        json.dump({"dry_run": True, "target_bytes": target, "evidence": ev},
                  open(args.out, "w"), indent=2)
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
        coll = db.create_collection(args.collection,
                                    definition={"indexing": {"deny": ["ballast"]}})
    except Exception:  # noqa: BLE001
        coll = db.get_collection(args.collection)

    print("  [1] filling …", file=sys.stderr)
    t0 = time.perf_counter()
    docs = fill(coll, target, args.doc_bytes)
    ev["steps"].append({"step": "fill", "documents": docs,
                        "seconds": round(time.perf_counter() - t0, 1)})

    print("  [2] flush …", file=sys.stderr)
    rc, out, err = nodetool(["flush", args.keyspace], args.nodetool)
    ev["steps"].append({"step": "flush", "rc": rc, "stderr": err[:400]})
    after_flush = count_sstables(args.data_dir, args.keyspace)
    ev["steps"].append({"step": "sstables_after_flush", "count": after_flush})
    print(f"      {after_flush} SSTables", file=sys.stderr)

    print("  [3] compact …", file=sys.stderr)
    rc, out, err = nodetool(["compact", args.keyspace], args.nodetool)
    ev["steps"].append({"step": "compact", "rc": rc, "stderr": err[:400]})

    print("  [4] invalidate caches …", file=sys.stderr)
    could_not = []
    for c in ("invalidatekeycache", "invalidaterowcache", "invalidatecountercache"):
        rc, _o, e = nodetool([c], args.nodetool)
        if rc != 0:
            could_not.append({"command": c, "stderr": e[:200]})
    ev["steps"].append({"step": "invalidate_caches", "failures": could_not})
    ev["caches_not_invalidated"] = could_not or None
    ev["page_cache_note"] = ("The operating system page cache was NOT dropped; doing "
                             "so needs root on the host. Reads may therefore still be "
                             "served from RAM below the database. State this in any "
                             "report that calls the regime disk-bound.")

    ev["after"]["sstables"] = count_sstables(args.data_dir, args.keyspace)
    ev["after"]["data_dir_bytes"] = dir_bytes(args.data_dir, args.keyspace)
    ev["after"]["compactions_completed"] = compactions_completed(args.nodetool)

    # ---- the four proof obligations --------------------------------------
    b, a = ev["before"], ev["after"]
    checks = {
        "data_exceeds_memtable_budget": a["data_dir_bytes"] >= target,
        "sstables_exist": a["sstables"] > 0,
        "compaction_crossed": (
            b["compactions_completed"] is not None
            and a["compactions_completed"] is not None
            and a["compactions_completed"] > b["compactions_completed"]),
        "caches_invalidated": not could_not,
    }
    ev["checks"] = checks
    ev["disk_bound"] = all(checks.values())

    record = {
        "driver": "disk_regime_driver.py", "version": "1.0",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "keyspace": args.keyspace, "collection": args.collection,
        "target_bytes": target,
        "memtable_budget_mb": args.memtable_budget_mb,
        "evidence": ev,
        "next_step": ("Run probe_field_vs_byte.py and verify_storage_claims.py against "
                      "this keyspace now, without restarting the node. If the node is "
                      "restarted the memtable is empty again and the regime is lost."),
        "honesty_note": ("disk_bound=false means the regime was not reached. Do not "
                         "report the run as disk-bound on the strength of intent."),
    }
    json.dump(record, open(args.out, "w"), indent=2)

    print("\n" + "=" * 72, file=sys.stderr)
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}", file=sys.stderr)
    print(f"  => disk_bound = {ev['disk_bound']}", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    if not ev["disk_bound"]:
        print("\nRegime NOT reached. Raise --target-multiple, check the data "
              "directory path, or read the compaction counter by hand.\n",
              file=sys.stderr)
        return 1
    print(f"\nState reached. Evidence in {args.out}. Measure now.\n", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
