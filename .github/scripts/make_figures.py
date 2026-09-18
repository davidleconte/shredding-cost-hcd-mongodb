#!/usr/bin/env python3
"""Generate docs/figures/regime-collapse.svg from the raw evidence in data/raw/.

Standard library only. The SVG markup is written directly; matplotlib is not
required and must not become a dependency of this repository (see
env/requirements.txt -- the probes install no plotting stack).

WHERE THE THREE NUMBERS COME FROM
---------------------------------
Every value on the figure is read out of data/raw/*.json at run time. Nothing is
transcribed from prose, and the growth factor drawn on each bar is recomputed
from the two p50 endpoints and cross-checked against the factor the harness
itself recorded; a mismatch aborts the run.

The caption is held to the same rule. Its growth factors and its repetition
count are interpolated from the same values the bars are drawn from, and every
topology and heap figure in it is emitted only after quote() has confirmed that
the fragment is still literally present in the conditions block it was taken
from (conditions() names the exact keys); a fragment that has gone missing
aborts the run rather than being drawn. The wording around those fragments --
"one node", "six-node ring" -- is editorial and is not machine-checked.

  x7.50  memtable, RF = 1, campaign 1
         file: data/raw/findings.json
         keys: findings[2].variant_B_indexed_chunks.evidence.by_document_size
                 ["1kb"]["p50_ms"]    = 12.104
                 ["128kb"]["p50_ms"]  = 90.783
               findings[2].variant_B_indexed_chunks.evidence.p50_growth_factor
                                      = 7.5
               findings[2].variant_B_indexed_chunks.evidence.reps_per_size = 30
         (findings[2] is probe "3. read-modify-write detection", claim_id A3.
          It is located by claim_id, not by index, so the file may be reordered.)

  x5.94  disk-resident dataset, RF = 3, campaign 3 -- the DATASET was on disk,
         the probed read was not: the RMW probe re-reads the row it just wrote,
         which stays memtable-resident (challenge C2, confirmed by M15). The
         label on this bar must never be shortened to "disk-bound".
         file: data/raw/findings_disk_rf3.json
         keys: variantB_indexed_chunks.update_p50["1kb"]    = 20.389
               variantB_indexed_chunks.update_p50["128kb"]  = 121.189
               variantB_indexed_chunks.update_growth        = 5.94
         NOTE: this file records no repetition count for variant B. The figure
         says so rather than borrowing n = 30 from the other two campaigns.

  x1.52  SSTable read path, flush before each update, M15
         file: data/raw/rmw_postflush.json
         keys: by_size["1kb"]["p50_ms"]   = 107.765
               by_size["128kb"]["p50_ms"] = 163.402
               by_size["1kb"]["n"]        = 30
               p50_growth_factor          = 1.52

Usage:  python3 .github/scripts/make_figures.py [--check]
        --check  regenerate into memory and fail if the file on disk differs
                 (for CI; does not write).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from xml.dom import minidom
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"
OUT = REPO / "docs" / "figures" / "regime-collapse.svg"


# --------------------------------------------------------------------------
# evidence
# --------------------------------------------------------------------------

def load(name: str) -> dict:
    with (RAW / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def growth(lo: float, hi: float) -> float:
    return round(hi / lo, 2)


def check(label: str, recomputed: float, recorded: float) -> float:
    """Abort rather than draw a number the harness does not agree with."""
    if abs(recomputed - recorded) > 0.005:
        raise SystemExit(
            f"{label}: recomputed growth {recomputed} != recorded {recorded}. "
            "The raw evidence changed; fix the figure or the claim, not this check."
        )
    return recomputed


def quote(label: str, source: str, fragment: str, shown: str) -> str:
    """Emit caption prose only while the evidence behind it is still there.

    The caption says "one node" where findings.json says "1 node (container
    rh-hcd"; the wording is editorial, the fact is not. Same contract as
    check(): abort rather than draw prose the raw JSON no longer supports.
    """
    if fragment not in source:
        raise SystemExit(
            f"{label}: the caption quotes {fragment!r}, which is no longer in "
            "this string. The run conditions changed; fix the caption or the "
            "claim, not this check."
        )
    return shown


def conditions() -> dict:
    """The topology and heap figures the caption states, each tied to its source.

    findings.json           .conditions.TO_BE_COMPLETED_BY_HAND.topology
                            .conditions.TO_BE_COMPLETED_BY_HAND.node_hardware
    findings_disk_rf3.json  .TO_BE_COMPLETED_BY_HAND.topology
    """
    c1 = load("findings.json")["conditions"]["TO_BE_COMPLETED_BY_HAND"]
    c3 = load("findings_disk_rf3.json")["TO_BE_COMPLETED_BY_HAND"]
    k1 = "findings.json .conditions.TO_BE_COMPLETED_BY_HAND"
    k3 = "findings_disk_rf3.json .TO_BE_COMPLETED_BY_HAND"
    return {
        "c1_nodes": quote(f"{k1}.topology", c1["topology"],
                          "1 node (container rh-hcd", "one node"),
        "c1_rf": quote(f"{k1}.topology", c1["topology"],
                       "NetworkTopologyStrategy {dc1: 1}", "RF = 1"),
        "c1_mem": quote(f"{k1}.node_hardware", c1["node_hardware"],
                        "mem_limit 3 GiB", "3 GiB"),
        "c1_heap": quote(f"{k1}.node_hardware", c1["node_hardware"],
                         "JVM heap 2 GiB (Xmx)", "2 GiB"),
        "c3_nodes": quote(f"{k3}.topology", c3["topology"],
                          "6 nodes/2 DC", "six-node ring"),
        "c3_rf": quote(f"{k3}.topology", c3["topology"],
                       "NetworkTopologyStrategy {dc1:3}", "RF = 3"),
        "c3_hw": quote(f"{k3}.topology", c3["topology"],
                       "nodes 8 GiB/4 vCPU, heap 4G", "8 GiB with a 4 GiB heap"),
    }


def collect() -> list[dict]:
    # --- campaign 1, memtable, RF = 1 -------------------------------------
    f1 = load("findings.json")
    a3 = next(f for f in f1["findings"] if f.get("claim_id") == "A3")
    ev1 = a3["variant_B_indexed_chunks"]["evidence"]
    lo1 = ev1["by_document_size"]["1kb"]["p50_ms"]
    hi1 = ev1["by_document_size"]["128kb"]["p50_ms"]
    g1 = check("findings.json", growth(lo1, hi1), ev1["p50_growth_factor"])
    n1 = ev1["by_document_size"]["1kb"]["n"]

    # --- campaign 3, disk-resident dataset, RF = 3 ------------------------
    f3 = load("findings_disk_rf3.json")
    vb3 = f3["variantB_indexed_chunks"]
    lo3 = vb3["update_p50"]["1kb"]
    hi3 = vb3["update_p50"]["128kb"]
    g3 = check("findings_disk_rf3.json", growth(lo3, hi3), vb3["update_growth"])

    # --- M15, SSTable read path -------------------------------------------
    f15 = load("rmw_postflush.json")
    lo15 = f15["by_size"]["1kb"]["p50_ms"]
    hi15 = f15["by_size"]["128kb"]["p50_ms"]
    g15 = check("rmw_postflush.json", growth(lo15, hi15), f15["p50_growth_factor"])
    n15 = f15["by_size"]["1kb"]["n"]

    return [
        {
            "regime": "Memtable-resident, RF = 1 — campaign 1",
            "note": None,
            "value": g1,
            "lo": lo1, "hi": hi1,
            "file": "data/raw/findings.json",
            "n": f"n = {n1}", "reps": n1,
        },
        {
            "regime": "Disk-resident dataset, RF = 3 — campaign 3",
            # C2, confirmed by M15: campaign 3 put the *dataset* on disk, never
            # the probed *read*. THREATS-TO-VALIDITY.md S3 grades C2 as VOIDING
            # M10's "disk-bound" label; the bar must not restore it.
            "note": "The probed read stayed in the memtable — challenge C2, confirmed by M15",
            "value": g3,
            "lo": lo3, "hi": hi3,
            "file": "data/raw/findings_disk_rf3.json",
            "n": "n not recorded", "reps": None,
        },
        {
            "regime": "SSTable read path, flush before each update — M15",
            "note": None,
            "value": g15,
            "lo": lo15, "hi": hi15,
            "file": "data/raw/rmw_postflush.json",
            "n": f"n = {n15}", "reps": n15,
        },
    ]


# --------------------------------------------------------------------------
# geometry  (one 620 x 530 viewBox; every coordinate is derived, none guessed)
# --------------------------------------------------------------------------

W = 620
CAPTION_TOP = 450           # y of the first caption line
CAPTION_STEP = 14           # leading between caption lines; the canvas
                            # height is derived from these two and the
                            # number of caption lines, never hard-coded
PLOT_X = 44                 # left edge of the bars and of all body text
PLOT_W = 480                # width of the x = 0 .. AXIS_MAX span
AXIS_MAX = 8.0              # growth factor at the right-hand end of the axis
SCALE = PLOT_W / AXIS_MAX   # px per 1.0 of growth factor
PLOT_TOP = 96
ROW_STEP = 102
BAR_H = 30
AXIS_Y = 390

INK = "#16191d"
MUTED = "#5b636d"
FAINT = "#9aa1a9"
BAR = "#1f4e79"             # one colour for all three: it is one measurement
RULE = "#d4d8dd"

SANS = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

def caption(rows: list[dict], cond: dict) -> list[str]:
    """The caption, built from the same evidence the bars are.

    Growth factors and the repetition count come from `rows`; the topology and
    heap figures come from `cond`, where quote() has already checked each one
    against the conditions block it was taken from.
    """
    g1, g3, g15 = (f"\u00d7{r['value']:.2f}" for r in rows)
    reps1, reps15 = rows[0]["reps"], rows[2]["reps"]
    if reps1 != reps15:
        raise SystemExit(
            f"campaign 1 records n = {reps1} and M15 n = {reps15}; the caption's "
            "single repetition count no longer covers both. Rewrite the caption, "
            "not this check."
        )
    return [
        "Bars are p50 growth factors (median update latency at 128 KB \u00f7 median at 1 KB), not",
        "absolute costs, and they are not directly comparable. "
        f"Campaign 1 ran on {cond['c1_nodes']}, {cond['c1_rf']},",
        f"{cond['c1_mem']} with a {cond['c1_heap']} heap; campaign 3 on a "
        f"{cond['c3_nodes']}, {cond['c3_rf']}, {cond['c3_hw']}.",
        f"The {g1} \u2192 {g3} step therefore mixes regime, topology and hardware; "
        f"only {g3} \u2192 {g15}",
        "isolates one variable \u2014 same ring, same probe, flush forced before each update. A single",
        "\u201ccost per indexed KiB\u201d for this engine is meaningless unless its regime is quoted with it.",
        # Challenge C2, CONFIRMED by M15: campaign 3 put the *dataset* on disk
        # and never the probed *read*, so THREATS-TO-VALIDITY.md S3 grades C2 as
        # VOIDING M10's "disk-bound" label. The figure travels alone, so it
        # carries the void itself rather than relying on the register. L7 bounds
        # even row 3: the OS page cache was never droppable (no root), so
        # "SSTable-resident" never means "cold" -- RESULTS.md, "A genuinely
        # disk-bound read: never achieved anywhere in the dossier".
        f"Campaign 3 put the dataset on disk, never the probed read: the {g3} run re-reads the row",
        "it just wrote, so rows 1 and 2 are both memtable reads (challenge C2, confirmed by M15).",
        f"Only the {g15} run forces the cycle\u2019s SELECT onto the SSTable path \u2014 and even there the",
        "OS page cache was never dropped, so no genuinely disk-bound read-modify-write read",
        "exists in this dossier.",
        # M15's declared reserve. Flushing before each update leaves ~35
        # small SSTables for one SELECT to merge -- fragmentation a normal
        # compaction would not produce -- so the ~90-100 ms fixed floor is
        # inflated and the true disk-bound figure lies between this run and
        # the memtable runs. Sources: REPRODUCING.md, docs/challenges.fr.md
        # (C2 resolution), RESULTS.md (M15 regime/caveat column).
        "M15 forces that flush before every update: up to ~35 small SSTables for one SELECT to",
        "merge, fragmentation a normal compaction would not leave. That inflates its ~90\u2013100 ms",
        f"fixed floor, so {g15} is a worst case \u2014 the true disk-bound figure sits between it and",
        f"the two memtable runs above, {g3} and {g1}.",
        f"n = {reps1} timed repetitions per size in campaign 1 and in M15; "
        "campaign 3 records no count.",
    ]


def text(x, y, s, *, size, fill=INK, weight="normal", family=SANS,
         anchor="start", extra="") -> str:
    return (
        f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size:g}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>'
        f"{escape(s)}</text>"
    )


def build(rows: list[dict], cond: dict) -> str:
    cap = caption(rows, cond)
    h = CAPTION_TOP + CAPTION_STEP * len(cap)
    o: list[str] = []
    o.append('<?xml version="1.0" encoding="UTF-8"?>')
    o.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" '
        f'width="{W}" height="{h}" role="img" aria-labelledby="figTitle figDesc">'
    )
    o.append(
        '<title id="figTitle">One measurement, three regimes: the growth '
        "coefficient collapses from ×7.50 towards ×1.52, a fragmented worst case</title>"
    )
    o.append(
        '<desc id="figDesc">'
        + escape(
            "Horizontal bar chart of the p50 growth factor of a single-field "
            "update, 1 KB to 128 KB document, measured three times on IBM "
            "DataStax HCD 2.0.6: "
            + "; ".join(f"{r['regime']}, x{r['value']:.2f}" for r in rows)
            + ". The three runs are not directly comparable; regime, topology "
            "and hardware differ between campaign 1 and campaign 3. Campaign 3 "
            "put the dataset on disk and never the probed read, which re-reads "
            "the row it just wrote: the first two runs are therefore both "
            "memtable reads (challenge C2, confirmed by M15). Only the third "
            "run forces the cycle's SELECT onto the SSTable read path, and even "
            "there the operating system page cache was never dropped, so no "
            "genuinely disk-bound read-modify-write read exists in this "
            "dossier. That third run flushes before every update, leaving up to "
            "about 35 small SSTables for one SELECT to merge, a fragmentation a "
            "normal compaction would not produce, so its fixed floor of roughly "
            "90 to 100 milliseconds is inflated and its growth factor is a "
            "worst case: the true disk-bound figure sits between that run and "
            "the two memtable runs."
        )
        + "</desc>"
    )
    # explicit white ground: GitHub renders SVG unchanged in dark mode, so a
    # transparent background would put dark text on a dark page.
    o.append(f'<rect x="0" y="0" width="{W}" height="{h}" fill="#ffffff"/>')

    o.append(text(PLOT_X, 34, "One measurement, three regimes", size=21, weight="700"))
    o.append(text(PLOT_X, 56,
                  "IBM DataStax HCD 2.0.6, Data API v1.0.33. Growth in the latency of one scalar $set",
                  size=12, fill=MUTED))
    o.append(text(PLOT_X, 72,
                  "as a document grows 1 KB \u2192 128 KB, the added content indexed and never mutated.",
                  size=12, fill=MUTED))

    # x = 1 reference: a growth factor of 1 is "no growth at all".
    x1 = PLOT_X + SCALE
    o.append(
        f'<line x1="{x1:g}" y1="{PLOT_TOP}" x2="{x1:g}" y2="{AXIS_Y}" '
        f'stroke="{FAINT}" stroke-width="1" stroke-dasharray="3 3"/>'
    )
    o.append(text(x1 + 5, PLOT_TOP - 5, "×1 = no growth", size=10.5, fill=FAINT))

    for i, r in enumerate(rows):
        top = PLOT_TOP + i * ROW_STEP
        bar_y = top + 24
        bar_w = r["value"] * SCALE
        assert bar_w > 0, "negative or zero bar width"
        assert PLOT_X + bar_w <= PLOT_X + PLOT_W, "bar overflows the plot area"

        o.append(text(PLOT_X, top + 16, r["regime"], size=15, weight="600"))
        o.append(
            f'<rect x="{PLOT_X}" y="{bar_y:g}" width="{bar_w:.2f}" height="{BAR_H}" '
            f'fill="{BAR}"/>'
        )
        o.append(text(PLOT_X + bar_w + 9, bar_y + BAR_H - 9,
                      f"×{r['value']:.2f}", size=17, weight="700"))
        o.append(text(PLOT_X, top + 70,
                      f"{r['file']}  ·  p50 {r['lo']:g} → {r['hi']:g} ms  ·  {r['n']}",
                      size=11.5, fill=MUTED, family=MONO))

        # A regime label the register has voided is corrected on the bar, not
        # only in the caption: a figure travels alone.
        if r["note"]:
            assert top + 86 < AXIS_Y - 4, "row note would collide with the axis"
            o.append(text(PLOT_X, top + 86, r["note"], size=11.5, fill=INK))

    # axis
    o.append(
        f'<line x1="{PLOT_X}" y1="{AXIS_Y}" x2="{PLOT_X + PLOT_W}" y2="{AXIS_Y}" '
        f'stroke="{RULE}" stroke-width="1.5"/>'
    )
    for k in range(int(AXIS_MAX) + 1):
        x = PLOT_X + k * SCALE
        o.append(f'<line x1="{x:g}" y1="{AXIS_Y}" x2="{x:g}" y2="{AXIS_Y + 5}" '
                 f'stroke="{RULE}" stroke-width="1.5"/>')
        o.append(text(x, AXIS_Y + 18, f"×{k}", size=11, fill=MUTED, anchor="middle"))
    o.append(text(PLOT_X, AXIS_Y + 38,
                  "p50 growth factor, dimensionless — median update latency at 128 KB ÷ "
                  "median at 1 KB",
                  size=12, fill=INK))

    y = CAPTION_TOP
    for line in cap:
        o.append(text(PLOT_X, y, line, size=11, fill=MUTED))
        y += CAPTION_STEP

    o.append("</svg>")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail if the committed SVG differs from a fresh render")
    args = ap.parse_args()

    rows = collect()
    svg = build(rows, conditions())

    # well-formedness is asserted here, not left to the reader
    minidom.parseString(svg)

    if args.check:
        if not OUT.exists():
            print(f"missing: {OUT}", file=sys.stderr)
            return 1
        if OUT.read_text(encoding="utf-8") != svg:
            print(f"stale: {OUT} differs from a fresh render of data/raw/", file=sys.stderr)
            return 1
        print(f"up to date: {OUT.relative_to(REPO)}")
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({len(svg)} bytes)")
    for r in rows:
        print(f"  x{r['value']:.2f}  {r['regime']}  <-  {r['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
