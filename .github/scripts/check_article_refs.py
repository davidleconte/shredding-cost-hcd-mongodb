#!/usr/bin/env python3
"""
check_refs.py — internal consistency checker for the diptych.

Exists because three defects of the same class slipped through by hand: a section
reference left pointing at a heading that no longer existed, a figure reference
frozen at its pre-split number, and a measurement cited in one part whose entry
lives in the other. Structural checks (tag balance, well-formed SVG, note anchors)
caught none of them, because none of them is structural — they are references that
resolve to the wrong thing, or to nothing.

What it checks, per file and across the pair:

  1. every "section N" / "section N.M" in prose resolves to a heading in that file,
     or is explicitly qualified as belonging to the other part
  2. every "Figure N" in prose resolves to a figure present in that file
  3. figure numbering is dense and ordered: SVG headings, figcaptions and their
     sequence agree
  4. every note anchor has a list item and every list item is cited
  5. every "measurement Mx" cited resolves to an appendix entry here, or is
     qualified as living in the other part
  6. measurement identifiers do not collide across the pair with different content
  7. shared tables (the six-axis summary) are identical in both files
  8. tag balance and SVG well-formedness, kept because they are cheap

Exit code 0 when clean, 1 otherwise. Usage:
    python3 check_refs.py part1.html part2.html
"""

from __future__ import annotations

import html
import re
import sys
import xml.dom.minidom


def strip(s: str) -> str:
    s = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s)))


def headings(s: str) -> tuple[set[str], set[str]]:
    h2 = {m.group(1) for m in re.finditer(r"<h2>(\d+)\.", s)}
    h3 = {m.group(1) for m in re.finditer(r"<h3>(\d+\.\d+)", s)}
    return h2, h3


def figures(s: str) -> tuple[list[str], list[str]]:
    return (re.findall(r"FIGURE (\d+) —", s),
            re.findall(r"<figcaption>Figure (\d+)\.", s))


def check_file(path: str) -> list[str]:
    s = open(path, encoding="utf-8").read()
    t = strip(s)
    name = path.split("/")[-1]
    errs: list[str] = []

    # --- 1. section references -------------------------------------------
    h2, h3 = headings(s)
    for m in re.finditer(r"(Part [IV]+, )?section (\d+)(\.\d+)?", t):
        other, num, sub = m.group(1), m.group(2), m.group(3) or ""
        if other:
            continue                       # explicitly the other part's numbering
        target = num + sub
        ok = (target in h3) if sub else (num in h2)
        if not ok:
            errs.append(f"{name}: 'section {target}' resolves to no heading "
                        f"(h2 {sorted(h2, key=int)}, h3 {sorted(h3)})")

    # --- 2. figure references in prose ------------------------------------
    svg_nums, cap_nums = figures(s)
    present = set(cap_nums)
    for m in re.finditer(r"\bFigure (\d+)\b", t):
        # skip the caption's own opening word
        before = t[max(0, m.start() - 60):m.start()]
        if before.rstrip().endswith((".", "…")) and "Figure" not in before[-20:]:
            pass
        if m.group(1) not in present:
            errs.append(f"{name}: prose cites 'Figure {m.group(1)}' "
                        f"but the file has figures {sorted(present, key=int)}")

    # --- 3. figure numbering dense and ordered ----------------------------
    if svg_nums != cap_nums:
        errs.append(f"{name}: SVG headings {svg_nums} disagree with "
                    f"figcaptions {cap_nums}")
    if cap_nums != sorted(cap_nums, key=int):
        errs.append(f"{name}: figure captions out of order: {cap_nums}")
    if cap_nums and [int(x) for x in cap_nums] != list(range(1, len(cap_nums) + 1)):
        errs.append(f"{name}: figure numbering not dense from 1: {cap_nums}")
    if len(set(cap_nums)) != len(cap_nums):
        errs.append(f"{name}: duplicate figure number in {cap_nums}")

    # --- 4. note anchors ---------------------------------------------------
    refs = {int(x) for x in re.findall(r'href="#n(\d+)"', s)}
    ids = {int(x) for x in re.findall(r'id="n(\d+)"', s)}
    if refs - ids:
        errs.append(f"{name}: note anchors with no list item: {sorted(refs - ids)}")
    if ids - refs:
        errs.append(f"{name}: notes never cited: {sorted(ids - refs)}")

    # --- 5. measurement citations ------------------------------------------
    entries = {m.group(1) for m in re.finditer(r"<dt>(M\d+)", s)}
    for m in re.finditer(r"measurements? (M\d+)(?: (?:to|and|&ndash;|–) (M\d+))?", t):
        cited = [g for g in m.groups() if g]
        ctx = t[max(0, m.start() - 120):m.end() + 120]
        if "Part I" in ctx or "Part II" in ctx:
            continue                       # explicitly delegated to the other part
        for c in cited:
            if c not in entries:
                errs.append(f"{name}: cites '{c}' with no appendix entry here "
                            f"and no cross-part qualifier — context: …{ctx[-70:]}")

    # --- 7b. the legend's figure count must match the file -------------------
    n_meas = len(re.findall(r'<figure class="wide measured">', s))
    n_all = len(re.findall(r'<figure class="wide', s))
    for mm in re.finditer(r"(\w+) of the (\w+) figures? below reports?", t, re.I):
        W = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10}
        said_m, said_all = W.get(mm.group(1).lower()), W.get(mm.group(2).lower())
        if said_m is not None and said_m != n_meas:
            errs.append(f"{name}: legend says {mm.group(1)} measured figures, file has {n_meas}")
        if said_all is not None and said_all != n_all:
            errs.append(f"{name}: legend says {mm.group(2)} figures, file has {n_all}")

    # --- 8. structure -------------------------------------------------------
    for tag in ("div", "figure", "dl", "table", "ol", "main"):
        o, c = s.count(f"<{tag}"), s.count(f"</{tag}>")
        if o != c:
            errs.append(f"{name}: <{tag}> unbalanced: {o} open, {c} close")
    for i, m in enumerate(re.finditer(r"<svg[^>]*>.*?</svg>", s, flags=re.S), 1):
        try:
            xml.dom.minidom.parseString(m.group(0))
        except Exception as exc:
            errs.append(f"{name}: SVG {i} malformed: {str(exc)[:80]}")
    return errs


def _norm(s: str) -> str:
    """Compare tables by their rendered text: entity spelling and the
    cross-part suffix are presentation, not content."""
    s = html.unescape(s).replace("(Part II)", "").replace("(Part I)", "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()


def check_pair(p1: str, p2: str) -> list[str]:
    a, b = open(p1, encoding="utf-8").read(), open(p2, encoding="utf-8").read()
    errs: list[str] = []

    # --- 6. measurement identifiers must not collide with different content
    def ent(s: str) -> dict[str, str]:
        out = {}
        for m in re.finditer(r"<dt>(M\d+) — ([^<]{0,70})", s):
            out[m.group(1)] = m.group(2).strip()
        return out
    ea, eb = ent(a), ent(b)
    for k in set(ea) & set(eb):
        if ea[k][:40] != eb[k][:40]:
            errs.append(f"pair: {k} titled differently: "
                        f"'{ea[k][:40]}' vs '{eb[k][:40]}'")

    # --- 6b. the prose tally must match the table -------------------------
    WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
    for path, s in ((p1, a), (p2, b)):
        name = path.split("/")[-1]
        m = re.search(r"<thead><tr><th>Axis measured</th>.*?</tbody>", s, flags=re.S)
        if not m:
            continue
        rows = re.findall(r"<tr>\s*<td>.*?</td>\s*<td>(.*?)</td>", m.group(0), flags=re.S)
        counts: dict[str, int] = {}
        for r in rows:
            k = re.sub(r"<[^>]+>", "", r).strip().lower()
            counts[k] = counts.get(k, 0) + 1
        t = strip(s)
        for mm in re.finditer(r"(\w+) of the six go to (MongoDB|the decomposing engine)", t, re.I):
            said = WORDS.get(mm.group(1).lower())
            key = "mongodb" if mm.group(2).lower() == "mongodb" else "decomposing engine"
            actual = counts.get(key, 0)
            if said is not None and said != actual:
                errs.append(f"{name}: prose says '{mm.group(1)} of the six go to "
                            f"{mm.group(2)}' but the table shows {actual}")
        for mm in re.finditer(r"the (\w+) axes that go the other way", t, re.I):
            said = WORDS.get(mm.group(1).lower())
            if said is not None and said != counts.get("mongodb", 0):
                errs.append(f"{name}: prose says 'the {mm.group(1)} axes that go the "
                            f"other way' but the table shows {counts.get('mongodb', 0)}")

    # --- 7. the shared six-axis table must be identical --------------------
    def axis_table(s: str) -> str | None:
        m = re.search(r"<table>\s*<thead><tr><th>Axis measured</th>.*?</table>",
                      s, flags=re.S)
        return re.sub(r"\s+", " ", m.group(0)) if m else None
    ta, tb = axis_table(a), axis_table(b)
    if ta is None or tb is None:
        errs.append("pair: the six-axis table is missing from one of the files")
    elif _norm(ta) != _norm(tb):
        errs.append("pair: the six-axis tables differ between the two files")
    return errs


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    errs = check_file(sys.argv[1]) + check_file(sys.argv[2])
    errs += check_pair(sys.argv[1], sys.argv[2])
    if not errs:
        print("clean — every reference resolves, numbering dense, tables agree")
        return 0
    print(f"{len(errs)} problem(s):")
    for e in errs:
        print("  ·", e)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
