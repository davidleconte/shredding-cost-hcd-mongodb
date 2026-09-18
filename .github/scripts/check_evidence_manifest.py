#!/usr/bin/env python3
"""Verify that every file under data/raw/ still hashes to its committed sha256.

The manifest lives at data/MANIFEST.sha256 — beside the evidence it describes, where a
reader following REPRODUCING.md looks for it — and is written in the ordinary
`sha256sum` format, so a reader can check it without this script:

    sha256sum -c data/MANIFEST.sha256      # from the repository root

Its paths are relative to the repository root, so it must be run from there. Run
from inside data/ it reports every file as "No such file or directory", which
looks like corruption and is not. It moved from .github/evidence.sha256 on
18 September 2026; git log --follow carries the history across.

What this proves: no file under data/raw/ has been edited, truncated, added or
removed since the manifest was committed. What it does NOT prove: that the
numbers inside those files were produced by the runs the documents describe.
A hash is a seal on a file, not a witness to a measurement.

Usage:
    check_evidence_manifest.py            # verify (exit 1 on any mismatch)
    check_evidence_manifest.py --write    # regenerate the manifest
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO / "data" / "raw"
MANIFEST = REPO / "data" / "MANIFEST.sha256"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan() -> dict[str, str]:
    out = {}
    for path in sorted(EVIDENCE_DIR.rglob("*")):
        if path.is_file():
            out[path.relative_to(REPO).as_posix()] = sha256(path)
    return out


def read_manifest() -> dict[str, str]:
    entries = {}
    for lineno, line in enumerate(MANIFEST.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, name = line.partition("  ")
        if not name or len(digest) != 64:
            raise SystemExit(f"{MANIFEST}:{lineno}: malformed manifest line: {line!r}")
        entries[name] = digest
    return entries


def main() -> int:
    if not EVIDENCE_DIR.is_dir():
        print(f"FAIL: {EVIDENCE_DIR} does not exist", file=sys.stderr)
        return 1

    actual = scan()

    if "--write" in sys.argv:
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        body = "".join(f"{digest}  {name}\n" for name, digest in actual.items())
        MANIFEST.write_text(body, encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(REPO)} ({len(actual)} files)")
        return 0

    if not MANIFEST.is_file():
        print(f"FAIL: manifest {MANIFEST} is missing", file=sys.stderr)
        return 1

    expected = read_manifest()

    changed = sorted(n for n in expected.keys() & actual.keys() if expected[n] != actual[n])
    removed = sorted(expected.keys() - actual.keys())
    added = sorted(actual.keys() - expected.keys())

    for name in changed:
        print(f"CHANGED  {name}\n         manifest {expected[name]}\n         on disk  {actual[name]}")
    for name in removed:
        print(f"REMOVED  {name}")
    for name in added:
        print(f"UNLISTED {name}  {actual[name]}")

    total = len(actual)
    if changed or removed or added:
        print(
            f"\nFAIL: evidence under data/raw/ diverges from data/MANIFEST.sha256 "
            f"({len(changed)} changed, {len(removed)} removed, {len(added)} unlisted).\n"
            "data/raw/ is append-only by policy. If a file was legitimately ADDED, "
            "regenerate with:  python .github/scripts/check_evidence_manifest.py --write\n"
            "If a file was CHANGED or REMOVED, that is a policy violation, not a "
            "manifest problem.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {total} evidence files match data/MANIFEST.sha256")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
