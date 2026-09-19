#!/usr/bin/env python3
"""Corrections parity: when this dossier corrects itself, does the correction reach every surface?

WHY THIS EXISTS. On 18 September 2026 three retractions landed in the Markdown
layer and not in the HTML layer, and nothing caught it for a day: the annulment
of challenge D12, the refutation of challenge D9, and the replacement of D7's
decomposition. The article — the surface a reader actually reads — went on
publishing a withdrawal the repository had annulled, and contradicted itself
across 579 lines of its own file. Ten CI checks were green throughout, because
every one of them examines a surface in isolation. This one compares them.

The hand repair that followed missed two more, and how it missed them is the
argument for automating it: the verification grepped the ENGLISH phrase
"cold-start property" across all three HTML files. The French synthesis says
"avant premier flush". Searching for the word rather than the effect, in one
language, left two corrected claims stale on a published page for a day.

THE BLOCK RULE, which is the whole of the design. This repository's convention is
that a superseded reading is KEPT and refuted in place, not deleted — so a
superseded phrase is not forbidden. It is forbidden *standing alone*. An entry
declares a `trigger` (the superseded reading, in every language it is published
in) and a `qualifier` (what must accompany it). A block containing a trigger must
contain a qualifier. `article-part1` line 605 is the case this rule was built
around: it keeps "cold-start property", and the same paragraph carries 171 267
and 172 132. That passes, and should. A block carrying the trigger and no
qualifier fails, and should.

A block is one <p>, <li>, <dd>, <dt>, <td>, <th> or heading in HTML; in Markdown
one paragraph between blank lines, or one table row. Text is normalised before
matching — HTML entities expanded, tags stripped, whitespace and non-breaking
spaces collapsed, French decimal commas and thousands separators folded — so a
phrase broken by `&mdash;` or wrapped across lines still matches, "13,398" matches
"13.398", and `**tier** gap` matches "tier gap". That last one is not cosmetic: emphasis
is invisible to a reader and must be invisible to a matcher, or the check develops the
same blind spot check 7 was found to have on 18 September.

WHAT IT PROVES. For every correction declared in the ledger, across every
published surface in the tree: wherever the superseded reading appears, the
correction appears with it.

WHAT IT DOES NOT PROVE, and this half matters more:

  * That the correction is TRUE. It makes two renderings of a claim agree.
    Agreement is not truth. Whether campaign 7bis measured what it says it
    measured is argued in docs/campagne7bis.fr.md, not here.
  * That every correction is declared. The ledger is hand-authored and there is
    nothing in this tree from which the set of corrections could be derived — no
    evidence file records what challenge D9 used to claim. A correction nobody
    enters here is invisible. Two partial guards, neither a cure: an entry whose
    trigger matches nothing anywhere fails, because a correction of something
    nobody wrote is a typo or a lie; and the surface set is derived from the tree
    rather than listed, so a page added and forgotten is in scope the moment it
    is committed.
  * That a qualifier means what it says. A block can carry "171 267" in an
    unrelated sentence and pass. The suite's own precedent applies: a fingerprint
    pins a line, it does not read it.
  * Anything about corrections carrying no identifier. Of the seven divergences
    repaired by hand on 18 September, three were retractions with challenge ids
    and four were not. The ledger covers what it covers.
  * Anything that is not text: the SVG figures inside the article parts, their
    alt text, and the D/M/U epistemic markers that grade each sentence.

An entry has two shapes. Most declare a trigger and a qualifier: the superseded
reading survives and must be refuted in place. One marked `"resolved": true`
declares the opposite — the reading was removed everywhere — and its obligation
flips: the trigger must then match nothing at all. Marking an entry resolved
tightens the check on that entry rather than silencing it, which is why it is
safe to allow at all.

This check has NO --write mode, and that is a real asymmetry with the rest of the
suite. check_probe_citations re-derives every fingerprint; check_artifact_table
re-derives its table; make_figures re-renders the figure. Each can compute the
right answer and therefore say the committed copy is wrong. Nothing here can
compute what D9 used to claim.

Usage:
    check_corrections_parity.py            # verify (exit 1 on any failure)
    check_corrections_parity.py --list     # print the ledger and the derived surface set
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
LEDGER = REPO / ".github" / "corrections.json"

BLOCK_HTML = re.compile(r"<(p|li|dd|dt|td|th|h[1-6])\b[^>]*>(.*?)</\1>", re.S | re.I)
TAGS = re.compile(r"<[^>]+>")
WS = re.compile(r"[\s   ]+")
NUM_COMMA = re.compile(r"(?<=\d),(?=\d)")
EMPHASIS = re.compile(r"[*_`~]")


def normalise(text: str) -> str:
    t = html.unescape(TAGS.sub(" ", text))
    t = EMPHASIS.sub("", t)            # **tier** gap must match "tier gap" — Markdown emphasis
    t = WS.sub(" ", t)                 # is invisible to a reader and must be invisible here
    t = NUM_COMMA.sub(".", t)          # 13,398 -> 13.398 ; 171 267 keeps its space, collapsed above
    return t.strip().lower()


def surfaces() -> list[pathlib.Path]:
    """The published corpus, derived from the tree — closed by default, not listed by hand."""
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True,
                         check=True).stdout.split()
    keep = []
    for p in out:
        if p.startswith(".github/"):        # CI and working records are not published prose
            continue
        if p.endswith(".md") or (p.startswith("docs/") and p.endswith(".html")):
            keep.append(pathlib.Path(p))
    return sorted(keep)


def blocks(path: pathlib.Path) -> list[tuple[int, str]]:
    raw = (REPO / path).read_text(encoding="utf-8")
    out: list[tuple[int, str]] = []
    if path.suffix.lower() in (".html", ".htm"):
        for m in BLOCK_HTML.finditer(raw):
            out.append((raw.count("\n", 0, m.start()) + 1, normalise(m.group(2))))
        return out
    line_no = 1
    for chunk in raw.split("\n\n"):
        if chunk.lstrip().startswith("|"):
            for row in chunk.splitlines():
                out.append((line_no, normalise(row)))
                line_no += 1
            line_no += 1
            continue
        out.append((line_no, normalise(chunk)))
        line_no += chunk.count("\n") + 2
    return out


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = ledger["corrections"]
    corpus = surfaces()
    index = {p: blocks(p) for p in corpus}

    if "--list" in sys.argv:
        print(f"{len(corpus)} published surfaces derived from the tree:")
        for p in corpus:
            print(f"    {p}")
        print()
        for e in entries:
            print(f"{e['id']:12} {e['date']}  {e['what']}")
            for s, why in e.get("exempt", {}).items():
                print(f"{'':12} exempt: {s} — {why}")
        return 0

    problems: list[str] = []
    exemptions: list[str] = []
    fired = 0
    resolved_ok = 0

    for e in entries:
        triggers = [normalise(t) for t in e["trigger"]]
        quals = [normalise(q) for q in e["qualifier"]]
        exempt = {k: v for k, v in e.get("exempt", {}).items()}
        hits_anywhere = 0

        for path, bl in index.items():
            sp = path.as_posix()
            for line, text in bl:
                matched = [t for t in triggers if t in text]
                if not matched:
                    continue
                hits_anywhere += 1
                if sp in exempt:
                    exemptions.append(f"    {e['id']:12} {sp}:{line} — {exempt[sp]}")
                    continue
                if any(q in text for q in quals):
                    fired += 1
                    continue
                problems.append(
                    f"STALE  {e['id']}  {sp}:{line}\n"
                    f"       the superseded reading {matched[0]!r} stands in a block carrying none\n"
                    f"       of its corrections {e['qualifier']}.\n"
                    f"       {e['what']}")

        if e.get("resolved"):
            # The superseded reading was removed everywhere rather than refuted in place. The entry
            # stays as the record — this repository does not delete what it corrected — and the
            # obligation FLIPS: the trigger must now appear nowhere at all. Marking an entry
            # resolved therefore tightens the check on that entry; it cannot be used to silence one.
            if hits_anywhere:
                problems.append(
                    f"RESURFACED  {e['id']}: declared resolved — the superseded reading was removed "
                    f"everywhere — but {hits_anywhere} block(s) carry it again. Either the text "
                    f"regressed or the entry should lose its `resolved` flag and declare qualifiers.")
            else:
                resolved_ok += 1
        elif hits_anywhere == 0:
            problems.append(
                f"DEAD-ENTRY  {e['id']}: none of its triggers {e['trigger']} matches any block in "
                f"the published corpus, and it is not marked `resolved`. A correction of something "
                f"nobody wrote is a typo or a lie — fix the trigger, or set \"resolved\": true if the "
                f"superseded reading was removed everywhere rather than refuted in place.")

    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        stale = len([p for p in problems if p.startswith("STALE")])
        print(f"\nFAIL: {len(problems)} problem(s) across {len(corpus)} published surfaces"
              + (f", of which {stale} superseded reading(s) stand uncorrected" if stale else "")
              + ". The surface is behind the correction, or the ledger is wrong. Do not resolve it "
                "by weakening the ledger.", file=sys.stderr)
        return 1

    print(f"OK: {len(entries)} declared corrections across {len(corpus)} published surfaces — "
          f"{fired} superseded reading(s) found and correctly refuted in place, "
          f"{resolved_ok} removed everywhere and verified absent")
    if exemptions:
        print("    exemptions applied (each is one person's judgment, checked by nobody):")
        for x in exemptions:
            print(x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
