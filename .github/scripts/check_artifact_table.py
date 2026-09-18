#!/usr/bin/env python3
"""Keep ARTIFACT.md's evidence-manifest table, and its headline counts, true.

The table between the BEGIN/END EVIDENCE MANIFEST markers in ARTIFACT.md is
labelled "generated, do not hand-edit". It was not generated: no script wrote it
and none checked it, so when data/raw/ grew from 36 files to 38 the table kept
describing a directory that no longer existed, and so did five other counts
scattered through the document.

This script closes that. It regenerates the table from data/raw/ and verifies the
counts that can be derived mechanically. What it proves: the table's rows, sizes
and digests match the evidence directory, and the counts in the marked FACTS
block match the tree. What it does NOT prove: that the prose around them is true.
A count is not an argument.

The Producer column cannot be derived for every file — twelve raw records carry
no `probe` key — so attributions already present in the table are preserved and
re-emitted with their existing annotation. A new file with no `probe` key is
emitted as "— *unattributed*" and must be given a producer by hand.

Usage:
    check_artifact_table.py            # verify (exit 1 on any drift)
    check_artifact_table.py --write    # regenerate the table and the FACTS block
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
ARTIFACT = REPO / "ARTIFACT.md"
RAW = REPO / "data" / "raw"
BEGIN = "<!-- BEGIN EVIDENCE MANIFEST — generated, do not hand-edit -->"
END = "<!-- END EVIDENCE MANIFEST -->"
FACTS_BEGIN = "<!-- BEGIN ARTIFACT FACTS — generated, do not hand-edit -->"
FACTS_END = "<!-- END ARTIFACT FACTS -->"


def find_stamp(obj):
    """run_at_utc may sit at the top level or one level down; find it anywhere."""
    if isinstance(obj, dict):
        if isinstance(obj.get("run_at_utc"), str):
            return obj["run_at_utc"]
        for v in obj.values():
            got = find_stamp(v)
            if got:
                return got
    elif isinstance(obj, list):
        for v in obj:
            got = find_stamp(v)
            if got:
                return got
    return None


def existing_producers() -> dict[str, str]:
    """Preserve the Producer cell already recorded for each file."""
    text = ARTIFACT.read_text(encoding="utf-8")
    if BEGIN not in text:
        return {}
    block = text.split(BEGIN, 1)[1].split(END, 1)[0]
    out = {}
    for line in block.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 6 and cells[1].startswith("`") and cells[1].endswith(".json`"):
            out[cells[1].strip("`")] = cells[5]
    return out


def build_table() -> tuple[str, int, int]:
    keep = existing_producers()
    rows = ["", "| File | Bytes | SHA-256 | `run_at_utc` | Producer |",
            "|---|---:|---|---|---|"]
    total = 0
    files = sorted(RAW.glob("*.json"))
    for f in files:
        blob = f.read_bytes()
        total += len(blob)
        digest = hashlib.sha256(blob).hexdigest()
        try:
            stamp = find_stamp(json.loads(blob.decode("utf-8")))
        except Exception:
            stamp = None
        probe = None
        try:
            probe = json.loads(blob.decode("utf-8")).get("probe")
        except Exception:
            pass
        producer = keep.get(f.name) or (f"`{probe}`" if probe else "— *unattributed*")
        stamp_cell = f"`{stamp}`" if stamp else "— *not stamped*"
        rows.append(f"| `{f.name}` | {len(blob)} | `{digest}` | {stamp_cell} | {producer} |")
    rows.append("")
    return "\n".join(rows), len(files), total


def facts() -> dict[str, str]:
    def git(*a):
        return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.strip()
    files = sorted(RAW.glob("*.json"))
    total = sum(f.stat().st_size for f in files)
    stamped = sum(1 for f in files if find_stamp(json.loads(f.read_text(encoding="utf-8"))))
    probes = sorted((REPO / "probes").glob("*.py"))
    manifest = REPO / "data" / "MANIFEST.sha256"
    entries = [l for l in manifest.read_text(encoding="utf-8").splitlines()
               if l.strip() and not l.startswith("#")]
    scripts = sorted((REPO / ".github" / "scripts").glob("check_*.py"))
    return {
        "raw_files": str(len(files)),
        "raw_bytes": f"{total:,}".replace(",", " "),
        "raw_stamped": str(stamped),
        "raw_unstamped": str(len(files) - stamped),
        "probes": str(len(probes)),
        "probe_orig": str(len(list((REPO / "probes").glob("*.orig")))),
        "manifest_entries": str(len(entries)),
        "check_scripts": str(len(scripts)),
        "tags": git("tag", "-l") or "(none)",
        "tracked_files": str(len(git("ls-files").splitlines())),
    }
    # Deliberately absent, and each for its own reason.
    #   Commit count, HEAD, commit window: a generated block must not contain a fact that
    #   generating it changes. The commit that writes this block moves HEAD, so a block
    #   naming HEAD is stale the instant it is committed and the check can never pass.
    #   Untracked paths: worse, because it passed locally and failed in CI. The author's
    #   working tree is not a property of the artefact. A block naming it embeds whatever
    #   scratch file happens to sit beside the repository on one machine, and a clean
    #   checkout — which is what CI and every reader has — computes something different.
    #   That is how this check first went red: it published .github/GRADE-REPORT.md, an
    #   untracked local file, into a committed document.
    # All of these live in §1.4 as prose about a named past state, which is what they are.


def facts_block() -> str:
    f = facts()
    return ("\n| Fact | Value |\n|---|---|\n"
            + f"| `data/raw/` JSON files | **{f['raw_files']}** |\n"
            + f"| their total size in bytes | **{f['raw_bytes']}** |\n"
            + f"| of those, carrying a `run_at_utc` | {f['raw_stamped']} |\n"
            + f"| carrying none | {f['raw_unstamped']} |\n"
            + f"| `data/MANIFEST.sha256` entries | {f['manifest_entries']} |\n"
            + f"| `probes/*.py` | **{f['probes']}** (plus {f['probe_orig']} `.orig` reference copies) |\n"
            + f"| `.github/scripts/check_*.py` | {f['check_scripts']} |\n"
            + f"| `git tag -l` | {f['tags']} |\n"
            + f"| tracked files | {f['tracked_files']} |\n")


def splice(text: str, begin: str, end: str, body: str) -> str:
    head, _, rest = text.partition(begin)
    _, _, tail = rest.partition(end)
    return head + begin + body + end + tail


def main() -> int:
    text = ARTIFACT.read_text(encoding="utf-8")
    table, n, total = build_table()
    fb = facts_block()

    if "--write" in sys.argv:
        out = splice(text, BEGIN, END, table)
        if FACTS_BEGIN in out:
            out = splice(out, FACTS_BEGIN, FACTS_END, fb)
        ARTIFACT.write_text(out, encoding="utf-8")
        print(f"wrote ARTIFACT.md: {n} manifest rows, {total} bytes of evidence")
        return 0

    problems = []
    if BEGIN not in text or END not in text:
        problems.append("the EVIDENCE MANIFEST markers are missing from ARTIFACT.md")
    else:
        have = text.split(BEGIN, 1)[1].split(END, 1)[0]
        if have != table:
            hn = len([l for l in have.splitlines() if l.startswith("| `")])
            problems.append(f"the manifest table is stale: it holds {hn} rows, data/raw/ holds {n} "
                            f"files, or a size/digest/stamp has changed")
    if FACTS_BEGIN in text:
        have = text.split(FACTS_BEGIN, 1)[1].split(FACTS_END, 1)[0]
        if have != fb:
            problems.append("the ARTIFACT FACTS block no longer matches the tree")
    else:
        problems.append("the ARTIFACT FACTS markers are missing from ARTIFACT.md")

    if problems:
        for p in problems:
            print("FAIL: " + p, file=sys.stderr)
        print("\nRegenerate with: .github/scripts/check_artifact_table.py --write", file=sys.stderr)
        return 1
    print(f"OK: ARTIFACT.md's manifest ({n} files, {total} bytes) and facts block match the tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
