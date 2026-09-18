#!/usr/bin/env python3
"""Verify that every `<script>.py:NNN` citation in the Markdown still points at the
line it was written to point at.

This repository cites probe source lines by number more than thirty times — they
are its verification recipes ("resolve this yourself") and its pre-registration
pointers. A line number is a pointer into a file that moves: inserting a single
line in a docstring silently invalidates every citation below it, and no other
check in this suite notices, because the citation is prose, the probe still
compiles, and the evidence hashes are untouched.

That is not hypothetical. On 18 September 2026 a five-line docstring warning was
added to probes/probe_aggregation.py and eight citations across four documents
went stale in the same commit that was repairing a claim about rigour.

What this proves: the text on each cited line is the text that was there when the
citation was last blessed. What it does NOT prove: that the citation describes
that text correctly. A fingerprint pins a line, it does not read it.

The manifest is .github/probe-citations.sha256, one record per distinct citation:

    <sha256 of the stripped line>  <path>:<line>  <first 60 chars, for the human>

Usage:
    check_probe_citations.py            # verify (exit 1 on any mismatch)
    check_probe_citations.py --write    # re-bless every citation at its current line
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = REPO / ".github" / "probe-citations.sha256"
CITATION = re.compile(r"\b([A-Za-z_][A-Za-z_0-9]*\.py):(\d{1,5})\b")


def tracked_markdown() -> list[pathlib.Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout.split()
    return [REPO / p for p in out]


def resolve(script: str) -> pathlib.Path | None:
    """A citation names a basename; find it under the tracked tree, unambiguously."""
    out = subprocess.run(["git", "ls-files", f"*/{script}", script], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout.split()
    hits = sorted(set(out))
    return REPO / hits[0] if len(hits) == 1 else None


def fingerprint(path: pathlib.Path, line_no: int) -> tuple[str, str] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not (1 <= line_no <= len(lines)):
        return None
    text = lines[line_no - 1].strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), text[:60]


def scan() -> tuple[dict[str, tuple[str, str]], list[str]]:
    found, problems = {}, []
    for doc in tracked_markdown():
        for script, num in CITATION.findall(doc.read_text(encoding="utf-8")):
            path = resolve(script)
            if path is None:
                continue                      # not a file in this repo; not our business
            key = f"{path.relative_to(REPO).as_posix()}:{num}"
            fp = fingerprint(path, int(num))
            if fp is None:
                problems.append(f"OUT-OF-RANGE  {key}  cited in {doc.relative_to(REPO)} "
                                f"but the file has fewer lines")
                continue
            found[key] = fp
    return found, problems


def read_manifest() -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    entries = {}
    for lineno, raw in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("  ", 2)
        if len(parts) < 2 or len(parts[0]) != 64:
            raise SystemExit(f"{MANIFEST}:{lineno}: malformed line: {raw!r}")
        entries[parts[1]] = parts[0]
    return entries


def main() -> int:
    found, problems = scan()
    if "--write" in sys.argv:
        body = ["# Fingerprints of every <script>.py:NNN line cited in the Markdown.",
                "# Regenerate with: .github/scripts/check_probe_citations.py --write",
                "# A change here means a cited line moved or was edited — re-read the",
                "# citation before re-blessing it.", ""]
        for key in sorted(found):
            digest, preview = found[key]
            body.append(f"{digest}  {key}  {preview}")
        MANIFEST.write_text("\n".join(body) + "\n", encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(REPO)} ({len(found)} citations)")
        return 0

    expected = read_manifest()
    if not expected:
        print("FAIL: no manifest; run with --write once and commit it", file=sys.stderr)
        return 1

    for key in sorted(set(expected) - set(found)):
        problems.append(f"NO-LONGER-CITED  {key}  in the manifest but cited by no document "
                        f"(re-bless with --write if the citation was deliberately dropped)")
    for key in sorted(set(found) - set(expected)):
        problems.append(f"UNBLESSED  {key}  newly cited, absent from the manifest")
    for key in sorted(set(found) & set(expected)):
        if found[key][0] != expected[key]:
            problems.append(f"MOVED  {key}  now reads {found[key][1]!r} — the citation was "
                            f"blessed against different text; the line shifted or was edited")

    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        print(f"\nFAIL: {len(problems)} of {len(found)} source-line citations do not resolve "
              f"to the text they were blessed against.", file=sys.stderr)
        return 1
    print(f"OK: {len(found)} source-line citations still point at the text they name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
