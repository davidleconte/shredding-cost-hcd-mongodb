#!/usr/bin/env python3
"""Figure traceability: every published figure must be a number this repository
actually measured or derived.

WHAT IT CHECKS.  Collect every decimal token with three or more decimal places
from a FIXED list of English Markdown documents (below), and require each one to
be reachable in one of the two evidence layers:

    layer 1   data/raw/*.json                 measured evidence, immutable
    layer 2   data/derived/inference.json     numbers derived from layer 1 by
                                              .github/scripts/ (ratio intervals,
                                              exact p-values), itself re-derived
                                              from layer 1 by check_inference.py

A token is matched in one of two ways, and the two are reported separately
because they are not equally strong:

    exact     some evidence number equals the published value outright.
              Trailing-zero presentation ("0.530" in prose, 0.53 in JSON) is
              absorbed here by comparing values, not strings.
    rounded   no evidence number equals it, but some evidence number equals it
              once rounded to the precision the document prints. This is the
              honest reading of "r2 0.996" for a stored 0.9959 — and it is
              WEAKER, because rounding widens the target the published figure is
              allowed to hit. Every rounded match is listed by name in the
              output, with the evidence value and file it rounds from.

Anything matched by neither is an ORPHAN and fails the check.

WHAT IT DOES NOT CHECK, and must not be quoted as checking:

  * It matches against the UNION of the evidence files, not against the file the
    sentence cites. It therefore catches an invented figure; it does not catch a
    real figure attached to the wrong measurement, the wrong arm or the wrong
    engine. A misattribution passes this check.
  * It says nothing about numbers with fewer than three decimals (ratios such as
    44x, counts, percentages) — those are outside the token rule.
  * Its scope is the seven documents named in DOCUMENTS. Every other Markdown
    file in the repository, this artefact assessment included, is NOT covered.
    ARTIFACT.md is excluded on purpose: it quotes a Zenodo DOI prefix
    (10.5281/...), which is a name, not a figure.
  * A number being traceable says nothing about whether the measurement behind
    it was sound. That argument is in LIMITATIONS.md and docs/THREATS-TO-VALIDITY.md.

Nothing here contacts a database, and nothing here re-measures anything.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]

# The scope of the claim in ARTIFACT.md 2.2 / V12. Changing this list changes
# what the published sentence means; it is not a convenience knob.
DOCUMENTS = [
    "README.md",
    "METHODOLOGY.md",
    "RESULTS.md",
    "LIMITATIONS.md",
    "REPRODUCING.md",
    "DISCLAIMER.md",
    "data/README.md",
]

RAW_DIR = REPO / "data" / "raw"
DERIVED = REPO / "data" / "derived" / "inference.json"

# Thousands separators actually used in the prose: narrow no-break space, thin
# space, no-break space, plain space. "133 984.229" is one number, not two.
SEP = "[    ]"

# A published figure: three or more decimals, not preceded by a word character
# or a dot (so "p50 133 984.229" starts at 133, and "v1.0.33" is not a figure),
# and not followed by a further digit.
FIGURE = re.compile(r"(?<![\w.])\d{1,3}(?:" + SEP + r"\d{3})*\.\d{3,}(?!\d)")

# Any numeric literal inside an evidence file.
EVIDENCE_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

MAX_DECIMALS = 12


def evidence_values(paths: list[pathlib.Path]) -> dict[float, str]:
    """value -> name of the first file it occurs in."""
    found: dict[float, str] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in EVIDENCE_NUMBER.finditer(text):
            try:
                value = float(match.group())
            except ValueError:
                continue
            found.setdefault(value, path.name)
    return found


def index_by_precision(values: dict[float, str]) -> dict[tuple[int, str], float]:
    """(decimals, rendered-at-that-precision) -> one evidence value that renders so."""
    index: dict[tuple[int, str], float] = {}
    for value in values:
        for decimals in range(3, MAX_DECIMALS + 1):
            index.setdefault((decimals, f"{value:.{decimals}f}"), value)
    return index


def main() -> int:
    raw_paths = sorted(RAW_DIR.glob("*.json"))
    if not raw_paths:
        print(f"FAIL  no evidence files under {RAW_DIR.relative_to(REPO)}/")
        return 1

    raw_values = evidence_values(raw_paths)
    raw_index = index_by_precision(raw_values)

    if DERIVED.exists():
        derived_values = evidence_values([DERIVED])
        derived_note = f"{DERIVED.relative_to(REPO)}"
    else:
        derived_values = {}
        derived_note = f"{DERIVED.relative_to(REPO)} ABSENT — layer 2 unavailable"
    derived_index = index_by_precision(derived_values)

    print("figure traceability — published figures against committed evidence")
    print(f"  layer 1  {RAW_DIR.relative_to(REPO)}/*.json  ({len(raw_paths)} files, "
          f"{len(raw_values)} distinct numeric literals)")
    print(f"  layer 2  {derived_note}"
          + (f"  ({len(derived_values)} distinct numeric literals)" if derived_values else ""))
    print()

    missing = [d for d in DOCUMENTS if not (REPO / d).exists()]
    if missing:
        for doc in missing:
            print(f"FAIL  declared document not found: {doc}")
        return 1

    kinds = ["raw-exact", "raw-rounded", "derived-exact", "derived-rounded", "orphan"]
    per_doc: dict[str, dict[str, int]] = {}
    total = {k: 0 for k in kinds}
    distinct: dict[str, str] = {}          # printed value -> kind
    rounded_from: dict[str, tuple[float, str]] = {}   # printed -> (evidence value, file)
    orphans: dict[str, list[str]] = {}
    occurrences = 0

    for doc in DOCUMENTS:
        text = (REPO / doc).read_text(encoding="utf-8")
        counts = {k: 0 for k in kinds}
        for match in FIGURE.finditer(text):
            printed = re.sub(SEP, "", match.group())
            value = float(printed)
            decimals = len(printed.split(".")[1])
            key = (decimals, f"{value:.{decimals}f}")

            if value in raw_values:
                kind, source = "raw-exact", (value, raw_values[value])
            elif key in raw_index:
                hit = raw_index[key]
                kind, source = "raw-rounded", (hit, raw_values[hit])
            elif value in derived_values:
                kind, source = "derived-exact", (value, derived_values[value])
            elif key in derived_index:
                hit = derived_index[key]
                kind, source = "derived-rounded", (hit, derived_values[hit])
            else:
                kind, source = "orphan", None

            counts[kind] += 1
            total[kind] += 1
            occurrences += 1
            distinct.setdefault(printed, kind)
            if kind.endswith("rounded"):
                rounded_from.setdefault(printed, source)
            if kind == "orphan":
                line = text[: match.start()].count("\n") + 1
                orphans.setdefault(printed, []).append(f"{doc}:{line}")
        per_doc[doc] = counts

    width = max(len(d) for d in DOCUMENTS)
    print(f"  {'document':<{width}}   occ  raw-ex  raw-rnd  der-ex  der-rnd  ORPHAN")
    for doc in DOCUMENTS:
        c = per_doc[doc]
        print(f"  {doc:<{width}}  {sum(c.values()):4d}  {c['raw-exact']:6d}  "
              f"{c['raw-rounded']:7d}  {c['derived-exact']:6d}  {c['derived-rounded']:7d}  "
              f"{c['orphan']:6d}")
    print(f"  {'TOTAL':<{width}}  {occurrences:4d}  {total['raw-exact']:6d}  "
          f"{total['raw-rounded']:7d}  {total['derived-exact']:6d}  "
          f"{total['derived-rounded']:7d}  {total['orphan']:6d}")
    print()
    print(f"  {occurrences} occurrences, {len(distinct)} distinct values, "
          f"{len(orphans)} orphan values")

    if rounded_from:
        print()
        print(f"  matched only after rounding to the precision the document prints "
              f"({len(rounded_from)} distinct):")
        for printed in sorted(rounded_from, key=lambda p: float(p)):
            value, filename = rounded_from[printed]
            kind = distinct[printed]
            layer = "derived" if kind.startswith("derived") else "raw"
            print(f"    {printed:<12} <- {value!r:<12} {layer:<8} {filename}")
        print("  Rounding widens the target a published figure may hit. Each line above")
        print("  is a presentation choice a reader can re-check by hand; none is a match")
        print("  this script invented.")

    if orphans:
        print()
        print(f"  ORPHANS — {len(orphans)} published values occur in neither evidence layer:")
        for printed in sorted(orphans, key=lambda p: float(p)):
            print(f"    {printed:<14} {', '.join(orphans[printed][:6])}")
        print()
        print("  An orphan is not proof of fabrication: it may be a typo, a stale figure,")
        print("  or a number derived in prose and never written down. It IS a figure a")
        print("  reader cannot trace, which this repository does not permit. Either write")
        print("  the derivation into data/derived/ or correct the document.")
        return 1

    print()
    print("  0 orphans. Every published figure in the seven documents is reachable in")
    print("  data/raw/ or data/derived/inference.json. This says nothing about whether")
    print("  a figure is attached to the right measurement — see the module docstring.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
