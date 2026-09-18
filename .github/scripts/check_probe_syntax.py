#!/usr/bin/env python3
"""Every probes/*.py must compile. Nothing is executed.

A probe in this repository is evidence of what was run, not a library anyone
imports. Importing one would open sockets to a database that does not exist on a
CI runner, so this check goes no further than the compiler: the file is valid
Python for the interpreter running here.

This proves the source is syntactically intact. It proves nothing at all about
whether the probe measures what its name says, or whether the JSON under
data/raw/ came out of it. Files ending in .py.orig are deliberately NOT compiled:
they are archived earlier revisions, documented in probes/README.md, and their
modification times are themselves part of the evidence.
"""
from __future__ import annotations

import pathlib
import py_compile
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
PROBES = REPO / "probes"


def main() -> int:
    sources = sorted(PROBES.glob("*.py"))
    if not sources:
        print(f"FAIL: no Python sources under {PROBES}", file=sys.stderr)
        return 1

    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        for source in sources:
            target = pathlib.Path(tmp) / (source.stem + ".pyc")
            try:
                py_compile.compile(str(source), cfile=str(target), doraise=True)
            except py_compile.PyCompileError as exc:
                failures.append(f"{source.relative_to(REPO)}: {exc.msg.strip()}")

    for item in failures:
        print(f"SYNTAX {item}")

    if failures:
        print(f"\nFAIL: {len(failures)} of {len(sources)} probes do not compile.", file=sys.stderr)
        return 1

    orig = sorted(PROBES.glob("*.py.orig"))
    print(
        f"OK: {len(sources)} probes compile under Python {sys.version_info.major}."
        f"{sys.version_info.minor} (not executed); "
        f"{len(orig)} archived .py.orig file(s) skipped by design"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
