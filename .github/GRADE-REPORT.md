# Reconciled grade report

**Subject:** `shredding-cost-hcd-mongodb` — adversarial self-verification of a technical article
comparing IBM DataStax HCD 2.0.6 (Data API v1.0.33) against MongoDB 8.x on document-database
storage layout. Seven campaigns, twenty-three measurements (M1–M23; no M9 was ever assigned).

**Graded at:** commit `ff84757`, working tree of 2026-09-18, 8 commits, 0 tags, 0 releases.

**Method:** six independent rubrics were run against the repository. This document reconciles them.
Every claim below that is not attributed to a rubric was re-verified directly against the tree by
the reconciler; the commands are named where the number is load-bearing.

---

## 1. The headline

# **71 / 100 — C−**

> *Useful but materially limited. Accepted only with major revisions. A reader must do real
> work to know which parts to trust.*

**One line:** The most honest research artefact I have graded, and it is honest about a study that
cannot support the number on its own front page — a dossier whose self-audit found nearly every
defect I found, then shipped with the defects unrepaired and, in six places in its own normative
register, with a statement its audit had already declared false.

### The weights, declared and argued

| Rubric | Score | Weight | Why this weight, for *this* artefact |
|---|---:|---:|---|
| **Inferential apparatus (statistician)** | 71 | **22 %** | Heaviest, because this artefact's entire claim on a reader is that its numbers are honestly bounded. Everything else it does — the immutable evidence, the CI, the self-refutation register — exists to make one assertion credible: *these figures mean no more than they say*. The rubric that tests that assertion is the one that decides the grade. |
| **SIGMOD/VLDB PC review** | 73 | **20 %** | The broadest competent rubric: it is the only one that prices novelty, soundness, evidence and presentation against each other, which is the trade this artefact actually makes (high rigour, low novelty). |
| **Thesis examiner** | 80 | **18 %** | Grades the claim-to-evidence chain and the proportionality of hedging — the artefact's declared contribution, judged on its declared terms. Full weight, but not more, because a viva rewards *disclosure* of a defect nearly as much as its absence, and this artefact has learned to be rewarded for that. |
| **ACM artifact evaluation** | 72 | **18 %** | The artefact asked to be graded this way: `ARTIFACT.md` is 738 lines organised badge by badge. A repository that adopts a standard is entitled to be measured by it and obliged to be bound by it. |
| **Hostile procurement diligence** | 66 | **14 %** | Real weight, not full weight. The artefact explicitly disclaims procurement use (README rule 8: *"Prefer the structural results… the latency ratios are the decorative ones"*), and grading work against a purpose it declines is unfair. But the article is public, the author is an IBM employee, the subject is a live buy-or-build choice, and `44×` is four characters long. The audience it disclaims is the audience it will get. |
| **OSS maintainer** | 61 | **8 %** | Lightest, deliberately. It is the harshest grade in the set and it is the least diagnostic one. Topics, tags, a DOI, a CI badge, a disabled wiki — every defect it prices is real, cheap, and orthogonal to whether the work is right. Weighting packaging at 20 % would let two hours of `gh` commands move a research grade by five points, which would be its own form of grade inflation. |

**Weighted composite, rubrics as scored: 71.7.** This report argues five corrections to those six
numbers. Every one of them is priced here, once, with a stated magnitude and a stated weight.
Nothing in this document moves a score without a number attached to it.

| # | Correction | Argued in | On the rubric | Weight | On the composite |
|---:|---|:--:|---|---:|---:|
| 1 | Thesis examiner too generous by about four points — it credits disclosures whose one-line repairs are unapplied at HEAD | §4.1 | 80 → 76 | 18 % | **−0.72** |
| 2 | OSS maintainer too harsh by about six points — it prices a two-hour packaging deficit like a permanent evidential loss | §4.1 | 61 → 67 | 8 % | **+0.48** |
| 3 | SIGMOD novelty undersold, 48 → 56 | §4.6 | +1.5 | 20 % | **+0.30** |
| 4 | §4.4, the composition of the headline-coefficient attacks: two points off each of the two rubrics this report already calls *"too generous by a little, for the reason in §4.4"* — each priced half of it and neither priced the composition | §4.4 | statistician −2, SIGMOD −2 | 22 %, 20 % | **−0.84** |
| 5 | §4.5, "93 comparisons" presented throughout as an enumeration of a register it in fact samples (16 of 36 raw files): one point off the rubric that owns that register | §4.5 | statistician −1 | 22 % | **−0.22** |

**Net −1.00. Corrected composite: 70.70.** The adjusted set — statistician **68**, SIGMOD **72.5**,
thesis examiner **76**, ACM **72**, hostile procurement **66**, OSS **67** — composites to 70.70
exactly, which is the check on the ledger above. Rounded to the nearest integer, the headline is
**71**: a move of **+0.30**, upward, and a rounding that prices nothing, because every correction
this report argues is already inside the 70.70. On the letter map declared once in §2, the cell
70.0–72.9 is C−, so 71 is **C−**.

Three notes on where each price lands, so that none is charged twice. §2's scorecard continues to
report what each rubric returned; this ledger is the whole of the difference between that table and
the headline, and wherever this report routes a reader to a rubric it routes them to the adjusted
figure. The two §4.1 corrections very nearly cancel (−0.72 against +0.48, subtotal **71.46**, the
71.5 quoted in §2), so they do not decide the grade — rows 4 and 5 do. The hostile-procurement
rubric is not charged for §4.4 even though §4.4 names it, because §4.3 upholds its number as it
stands; charging it here would overturn §4.3 silently. And §5's dimension 11 (*Targeting of the inferential apparatus*, **52**
after the third correction note below it, at the joint-heaviest weight in that table) scores the same §4.4 evidence inside the dimensional
cut: that cut is a parallel scoring of the whole artefact, not a second charge inside this one.

### If the graders disagree, which should a reader trust?

They disagree by 19 points (61 → 80) and the spread is not noise — it is the artefact's own thesis
restated. **Trust the rubric that matches your purpose:**

- **Deciding whether to believe the article's numbers** → the **statistician**, at **68** rather
  than the 71 the rubric awarded, and the **SIGMOD review**, at **72.5** rather than 73. Both are
  right and both are too generous by a little, for the reason in §4.4 — charged against both at two
  points each in row 4 of the ledger above, with a further point against the statistician alone in
  row 5; the SIGMOD figure is net of the novelty credit of §4.6.
- **Deciding whether to buy HCD or MongoDB** → the **hostile-diligence** grade (66) *and its
  closing paragraph*, which is the single most useful sentence any grader wrote: on a
  research-integrity rubric this artefact scores around A−, on a procurement rubric it scores in the
  D band, *and that distance is not a contradiction — it is the artefact's own thesis about itself.*
- **Deciding whether to cite it** → the **ACM** grade (72). It earns no badge today. Not one of four.
- **Deciding whether to fork it as a template for your own adversarial self-review** → the
  **thesis-examiner** grade, at **76** rather than the 80 the rubric awarded: §4.1 finds that
  rubric too generous by about four points, because it credits disclosures whose prescribed
  one-line repairs are still unapplied at HEAD — the defect a forker would inherit. 76 is still
  the highest number in the set, and this remains the use for which the artefact is strongest.
- **Deciding whether to `git clone` it and expect a working thing** → the **OSS** grade, at **67**
  rather than the 61 the rubric awarded (§4.1: too harsh by about six points, because it prices a
  two-hour packaging deficit like a permanent evidential loss) — which is the correct answer to a
  question nobody should be asking of this repository.

---

## 2. The scorecard

### The letter map, declared once

Every letter in this document is issued from the map below and from nothing else. The bands are the
calibration's own (A 90–100, B 80–89, C 70–79, D 60–69, F below 60), and every band is cut at the
same two offsets: the first three points of a band take the **minus**, the middle four the bare
letter, the last three the **plus**. The map is therefore monotonic by construction, and a letter is
recoverable from a score without reading the sentence around it.

| Band | minus | middle | plus |
|---|---|---|---|
| **A** | A− 90.0–92.9 | A 93.0–96.9 | A+ 97.0–100 |
| **B** | B− 80.0–82.9 | B 83.0–86.9 | B+ 87.0–89.9 |
| **C** | C− 70.0–72.9 | C 73.0–76.9 | C+ 77.0–79.9 |
| **D** | D− 60.0–62.9 | D 63.0–66.9 | D+ 67.0–69.9 |
| **F** | — | F below 60.0 | — |

Two of the six source rubrics issued themselves a letter alongside their score: the
hostile-procurement rubric wrote **D+** against its 66, and the OSS rubric wrote **D+** against its
61. The map supersedes both — 66 is **D**, 61 is **D−** — and the letters printed below are the
map's, not the source rubrics'. Only labels changed: **this correction moved no score, so the §1
ledger is unchanged — 71.7 as scored, 70.70 corrected, 71 rounded** (and 71.5, the subtotal after
the two §4.1 corrections alone, is C− on this map as well). An earlier revision of this document mapped 71 → C−, 72 → C+ and 73 → C,
which was not monotonic; the three letters corrected here are 72 (C+ → C−), 66 (D+ → D) and
61 (D+ → D−).

| Rubric | Score | Letter | One-line verdict |
|---|---:|:--:|---|
| Thesis examiner (viva) | 80 | B− | Pass with minor corrections; the prose retreats to exactly what the data carry, but the empirical ceiling is fixed by design choices no revision can undo. |
| SIGMOD/VLDB PC review | 73 | C | Refutes its own author more rigorously than almost anything I have reviewed, attached to findings largely predictable from 1996 — and ships three factual errors its own audit had already written down. |
| ACM artifact evaluation | 72 | C− | Earns no ACM badge today, yet its own self-assessment found every defect I found before I found it; the gap between those two facts is the grade. |
| Inferential apparatus | 71 | C− | Correct everywhere I could check it and re-derivable to the digit — while auditing 93 comparisons it rarely quotes and leaving its headline coefficient without an interval anywhere in the repository. |
| Hostile procurement diligence | 66 | D | An honest mechanism study that correctly says it cannot decide a procurement, and is unrigorous at exactly the one number a careless colleague will paste into a slide. |
| OSS maintainer | 61 | D− | A dossier of unusual integrity inside a GitHub project two hours old: the parts an author writes are excellent, the parts a maintainer does are absent. |
| **Reconciled** | **71** | **C−** | **Accepted with major revisions.** |

---

## 3. Where the graders agree — the robust findings

Six findings were reached independently by three or more rubrics. I re-verified each. These are the
ones a hostile committee would not dislodge.

### 3.1 The samples are destroyed, and that is a loss, not a condition *(6 / 6 rubrics)*

Every rubric named this, and the thesis examiner, the statistician and the procurement reader all
ranked it their **worst** or near-worst finding. `probes/probe_comparative.py:94` — `distribution()`
— consumes the observation list and returns only `n / min / p50 / p95 / p99 / max / stdev`. The
process exited; nothing was serialised.

Verified: of 36 raw files, exactly **six** retain any per-observation array, and only
`vector_freshness_idle.json` and `vector_freshness_loaded.json` retain the latency `cycles[]` that
support a real test — the rest are field/vector metadata. Two of the three legs of the artefact's
central instability are thinner still: `rmw_postflush.json` (M15, the ×1.52) carries no `min_ms`,
and `findings_disk_rf3.json` (M10, the ×5.94) carries four `p50` values and nothing else.

**Consequence:** no confidence interval, no rank test, no bootstrap, no re-percentiling is
recoverable for 91 of the 93 published comparisons — by anyone, including the author, ever.

### 3.2 The percentile floor is set an order of magnitude too permissively *(4 / 6)*

Verified by walking every `data/raw/*.json`: **186** distribution blocks publish a `p99_ms`
alongside an `n`. **141 of them are at n = 30.** Sixteen are at n ≤ 5.

At n = 30, `pct()` interpolates at k = (30−1)·0.99 = 28.71, so the published p99 is
`0.29·x₍₂₉₎ + 0.71·max` — a blend of the top **two** of thirty observations. `docs/STATISTICS.md`
§6 rule 4 forbids quoting p95/p99 only **below n = 10**, which licenses all 141. Worse, §1's own
justification for the percentiles-only policy leans on a p99 of 326.149 ms drawn from a 30-point
sample, and two live verdicts ride on such a p99: `RESULTS.md:201` adjudicates a pre-registered
50 ms decision rule on "p99 under load 59.178 ms and 53.849 ms", and `RESULTS.md:227` argues the
RF = 3 freshness window widens to "p99 127.346 ms".

`ARTIFACT.md` §6 item 2 states the caveat corpus-wide. `README.md`, `RESULTS.md` and
`data/README.md` still attach it to the single n = 3 arm.

### 3.3 The prose has drifted from the evidence in ways the artefact already diagnosed *(5 / 6)*

Four contradictions, all verified, all with the repository's own audit already pointing at them:

| # | Defect | Verified how | Already flagged in |
|---|---|---|---|
| i | `DISCLAIMER.md:18` sources the date claim to `run_at_utc` in **"every file under `data/raw/`"** | `grep -l run_at_utc data/raw/*.json \| wc -l` → **24**; `ls data/raw/*.json \| wc -l` → **36**. `README.md:106` already says "24 of the 36" | `ARTIFACT.md` §8.2, `THREATS` X4, `.github/IMPROVEMENT-PLAN.md` |
| ii | `RESULTS.md` — the normative M1–M23 register — asserts **six times** (lines 59, 60, 155, 156, 157, 158) that campaign 7 carries *"no adversarial verdict … no figure in it has been challenged"* | `docs/challenges-campagne7.fr.md` carries D6–D14 against exactly those measurements and has been committed since `09459b9`, two commits before HEAD | `THREATS` X8: *"That sentence was true when written and is now false"* |
| iii | `METHODOLOGY.md:29–35` still asserts the cardinal rule *"Each probe carried its decision rule in its own source before it ran"* | `docs/RESEARCH-DESIGN.md:573,590` calls it **"false as a generalisation"** — the true figure is **six of sixteen**. `grep -c RESEARCH-DESIGN METHODOLOGY.md` → **0**: the retraction has no route to the document that makes the claim | RESEARCH-DESIGN §5.2 |
| iv | `docs/RESEARCH-DESIGN.md:756` closes *"This repository currently contains no scholarly references at all"* | `docs/RELATED-WORK.md` has 16 verified entries and is linked from the same README | — (undetected) |

**(ii) is the worst single item in the repository**, and the SIGMOD reviewer is right to rank it so.
In an artefact whose entire authority is the claim that its prose cannot drift from its evidence, a
six-fold false statement in the normative register — already found, written down, and shipped
anyway — is evidence that the apparatus does not close its own loop. It costs more than any
statistical weakness because it is the one failure the whole apparatus exists to prevent.

### 3.4 Half the system under test cannot be stood up from the artefact *(4 / 6)*

Verified: `env/` contains exactly two files — `docker-compose.mongodb-rs.yml` and
`requirements.txt`. There is no compose file and no Dockerfile for HCD or the Data API, and the
Data API container's environment is marked `[U] not recorded`. Four raw files have no producing
script in `probes/` (`control_read_A_run1.json`, `control_read_A_run2.json`,
`findings_hcd_vec_freshness.json` — source of the 44.972 ms freshness figure — and
`tier_comparison.json`). Eight of sixteen probes cannot answer `--help` offline; I ran the loop and
counted exactly **8**, the same eight `ARTIFACT.md` §2.2 predicts.

Of four images under test, exactly one is digest-pinned — and the pin sits in
`data/raw/findings_mongot_provenance.json` while `REPRODUCING.md:187` still instructs an unpinned
`docker run … mongodb/mongodb-atlas-local`. `ARTIFACT.md` §3.2 calls fixing that line *"the single
cheapest correctness fix in the artefact"* and supplies the replacement. The line is unchanged.

### 3.5 Thirteen files of this campaign's own evidence are withheld *(3 / 6, and the ACM chair's "worst")*

`probes/README.md` gap 8, read in full and verified: an archive
`verif-storage-20260917/raw_evidence.tar.gz` exists outside the repository holding **13 files, none
byte-identical to anything published**. Two of them are the scripts the register itself calls
unfindable (`probe3_variant_b.py`, `control_read.py`). One of them, `control_read_B.json`, carries
the ×1.56 variant-B read control that `RESULTS.md` M3 **publishes** — so a published number rests
on an unpublished file. And `probe4_traced.json` records `consistency_levels_observed` as
`LOCAL_QUORUM` 70 **alongside `ONE` 42 and `LOCAL_ONE` 2** over 200 traces, where ADR-001 states M4
as "70/70 statements at `LOCAL_QUORUM`".

The register's own words: *"This register records no decision to withhold these files and no reason
for it."* In a dossier whose authority rests on publishing the runs that went against its author,
the one withheld file that qualifies a published claim is the worst possible file to be missing.
Naming a gap is not closing it.

### 3.6 The verification apparatus is real and survives adversarial handling *(6 / 6 — the agreed strength)*

Every rubric, including the two that graded in the D band, credited this. I ran all six checks:

```
check_evidence_manifest  OK: 36 evidence files match .github/evidence.sha256
check_raw_json           OK: 194 latency distributions satisfy min <= p50 <= ... <= max
check_probe_syntax       OK: 16 probes compile under Python 3.12
check_links              OK: 236 relative links resolve to tracked paths, across 28 tracked files
check_inference          OK: 93 comparisons re-derived; 56 disjoint, 34 overlapping, 3 undecidable
check_figure_traceability OK: 0 orphans across the seven English documents
```

`git log --diff-filter=MD -- data/raw/` is empty across all history. The ACM chair tampered with a
float and added an unlisted file and got exit 1 both times, with a policy statement rather than a
diff. `check_links.py` resolves against `git ls-files` rather than the disk — the distinction most
artefacts get wrong, and the reason a local pass predicts the runner here. GitHub run
`35341327821` is green in 48 s.

And the workflow header spends 80 lines enumerating what a green tick does **not** assert, ending:
*"a sha256 seals a file against later editing; it is not a witness to a measurement"* and *"this
workflow can catch rot, drift, tampering and bad arithmetic. It cannot catch a wrong experiment."*
I have not seen a research repository write that sentence about itself.

---

## 4. Where they disagree — and my adjudication

### 4.1 Is 80 (thesis examiner) or 61 (OSS maintainer) closer to right?

**Neither. Both are grading real things and both are mis-scaled.**

The thesis examiner at **80 is too generous by about four points**, and the reason is structural to
viva rubrics: a viva rewards a candidate who *identifies* a flaw nearly as much as one who avoids
it, because in a viva the candidate is present and the correction is assumed to follow. This
artefact is not present. It ships. The examiner scored "proportionality of hedging" at 88 and
"claims-to-evidence chain" at 86 on the strength of disclosures whose prescribed repairs — all
named in `ARTIFACT.md` §8, all one line each — remain unapplied at HEAD. Disclosure that is not
followed by repair is a *feature of the document*, not of the artefact.

The OSS maintainer at **61 is too harsh by about six points**, because it prices a two-hour
packaging deficit at the same rate as a permanent evidential loss. `repositoryTopics: null`,
`homepageUrl: ""`, 0 tags, 0 releases, an empty wiki, no CI badge — I confirmed all of these by
`gh`, and every one is a five-minute fix specified in the repository's own IMPROVEMENT-PLAN. A
rubric on which the artefact can gain nine points without touching a single claim is a rubric about
housekeeping, and I have weighted it accordingly (8 %) rather than argued it away.

The two levers are separate and both are pulled, once each. The **six points** correct the rubric's
internal mis-scaling — what it should have scored — and are applied to its score in §1's ledger,
row 2 (**+0.48**). The **8 % weight** answers a different question — how far a housekeeping rubric
should be allowed to move a research grade at all — and is set in §1's weights table. The four
points against the thesis examiner are applied the same way, in row 1 (**−0.72**); its 18 % weight
was never discounted for the same reason, only capped at full and no more.

Two of its findings I do **not** discount, because they are not housekeeping:
- `gh api …/branches/main/protection` → **404 Branch not protected**. The evidence manifest and the
  files it seals can be rewritten in the same unreviewed commit. The workflow header concedes the
  sha256's limit; it does not concede this one.
- `docs/figures/regime-collapse.svg` is embedded in **no reader-facing document**.
  `grep -rn regime-collapse --include=*.md .` hits only `.github/IMPROVEMENT-PLAN.md`, the workflow
  and `make_figures.py`. CI job 6 enforces byte-identity of an asset no reader ever sees.

### 4.2 Is the ACM chair right that the self-assessment is 88-grade honest?

**Yes on accuracy, no on weight.** I spot-checked its §5 claims and they reproduce: the 24/36 count,
the two mechanical patches touching no threshold, the eight probes failing `--help`. `ARTIFACT.md`
§8.6 even *corrects a self-accusation that was overstated* and explains why that is not a softening.
That is rare and it is real.

But the chair scored the dimension at 88 while its own justification records that `ARTIFACT.md` is
stale by a commit (it asserts `rev-list --count HEAD` = **7** and HEAD = `166225e`; the tree is
**8** and HEAD is `ff84757`), that its §2.1 badge reasoning rests on a now-false "nothing above is
published" premise, and that row V0 of its own runnable-claim table invokes
`data/MANIFEST.sha256`, a file that does not exist. A self-assessment that is factually wrong about
the tree it assesses is not an 88. **I score that dimension 80.**

### 4.3 Is the procurement reader's 66 unfair?

**No, and its own last paragraph is the best adjudication in the set.** It states plainly that on a
research-integrity rubric this artefact would score around A−, and that the distance between that
A− and its own procurement grade is the artefact's own thesis about itself. It is right. A study that never entered
the production regime — no concurrency, no offered-rate load, no multi-host topology, three
"replicas" on one host, a shared VM at load average 14–16 — cannot decide a procurement, and
grading it 66 for that is not unfair when the repository itself says so in README rule 8.

The 14 % weight reflects one thing only: that the artefact's disclaimer does not travel with the
number. `44×` will be quoted without its row.

### 4.4 The aggravation neither the statistician nor the procurement reader priced

Both graders attacked the headline coefficient. The statistician computed Fieller intervals on
pass 1; the procurement reader refit on pass 2 and found a 2.6× swing. **Both are right, they
compose, and the composition is worse than either stated.** I refit all six slopes from
`data/raw/cmp_hcd.json` and `data/raw/cmp_mongo.json`:

| Pass | Arm | Slope (ms/KiB) | SE | r² | Ratio to HCD | Fieller 95 % |
|---|---|---:|---:|---:|---:|---|
| 1 | hcd | 0.77754 | 0.02479 | 0.9970 | — | — |
| 1 | mongo-wildcard | 0.01756 | 0.00376 | 0.8794 | **44.3×** | [26.0, 138.9] |
| 1 | mongo-default | 0.00976 | 0.00299 | 0.7809 | **79.6×** | [39.9, 2950.4], g = 0.947 |
| 2 | hcd | 0.73216 | 0.01389 | 0.9989 | — | — |
| 2 | mongo-wildcard | 0.00629 | 0.00256 | 0.6684 | **116.4×** | **UNBOUNDED**, g = 1.674 |
| 2 | mongo-default | 0.00848 | 0.00578 | 0.4179 | **86.3×** | **UNBOUNDED**, g = 4.702 |

The published slopes reproduce **exactly** — the arithmetic is sound. What the arithmetic shows is
that the flagship ratios are (a) fitted on one of two collected passes, hard-coded at
`probes/probe_comparative.py:255` as `k = f"{sz.label}|pass1"`; (b) 2.6× different on the other
pass, where audit finding I7 characterises inter-pass variance as "roughly 10–15 %"; and (c) on
that other pass, **possessed of no finite confidence interval at all**, because both MongoDB
denominator slopes have 95 % CIs containing zero.

`docs/STATISTICS.md` is 760 lines and the words *slope*, *regression*, *least-squares* and *r²*
appear in none of them. `data/derived/inference.json`'s `derived_quantities` block is restricted by
policy to "division or subtraction only. No model, no fit" — so the 93-comparison apparatus
**deliberately excludes** the four numbers the artefact is known for. `STATISTICS.md` §6 rule 2 —
*"quote the ratio interval, not only the ratio of medians"* — silently exempts them, and
`LIMITATIONS.md:197` asserts the weak-r² problem "does not touch effects of 40× and above", which
is backwards for precisely the two quantities it names.

The pass selection in (a) is **not** concealed, and an earlier revision of this section implied that
it was. `README.md:118` declares it in bold under ⛔ at the point of the number — *"the slopes are
fitted on **pass 1 only**, undeclared until now"* — with the r² pair and a pointer to `ARTIFACT.md`
§8.5; and `docs/RESEARCH-DESIGN.md:381`, `docs/THREATS-TO-VALIDITY.md:452`,
`docs/RELATED-WORK.md:254` and `ARTIFACT.md` V11 each record the hard-coded `pass1` key
independently. What is missing is (b) and (c): the pass-2 magnitudes appear nowhere in the tree, and
no interval for these four numbers appears anywhere in it. The reader is handed the fact of the
selection without its consequence. The aggravation is real but narrower than first scored, and §5's
dimension 11 is raised from 48 to 52 in consequence — the third correction note under the §5 table.

**This is the artefact's defining defect and it is not a statistics problem. It is a targeting
problem.** An apparatus rigorous everywhere except at the number every reader will quote has
aimed at the wrong target. Nothing here required new measurement: the five published medians per
arm were sufficient all along, and I computed the table above in four minutes from files already
in `data/raw/`.

### 4.5 The second unpriced aggravation: "93 comparisons" is not a census

The statistician noted M5's coordinator-side 2× is absent. I checked the whole census.
`data/derived/inference.json` draws its 93 comparisons from **16 of the 36 raw files**.
`findings_rf3.json` — which carries M5's `SELECT` p50 6.582 ms against `UPDATE … IF` 13.738 ms at
n = 124, published at `RESULTS.md:222–224` as "about 2×" — appears **zero times** in the inference
file. So do `findings_rf3_rate50*.json`, `findings_vector_rf3.json`, `comparison*.json`,
`tier_comparison.json`, `control_read_*.json` and `probe4_rf3_supplementary.json`. Substance is
unaffected — the missing comparisons would have returned OVERLAPPING — but "93 comparisons" is
presented throughout as an enumeration of the register, and it is a sample of it, nowhere declared
as one. CI verifies the 93 that exist; nothing verifies that 93 is the right number.

### 4.6 Where I think a grader is simply wrong

**The SIGMOD reviewer's novelty score of 48 is too low by about eight points.** It reasons from
`docs/RELATED-WORK.md` §8, which classifies 12 of 23 measurements as "predictable in kind" — and
then adopts that classification uncritically because the artefact made it against its own interest.
But two items survive that classification and are undersold. **M22** — `estimatedDocumentCount()`
returning 0 against a true 200 000 because it reads pre-flush SSTable metadata, with nothing in the
API signalling the condition — is a *silent* correctness defect. An application testing
`if count == 0` on a freshly loaded collection concludes it is empty. Calling that "a bug report on
one build" undersells it: silent wrongness in a cardinality primitive is a class of defect, and the
mechanism (metadata-derived estimate on an LSM store before flush) is not build-specific. **M1/M2**
— twelve physical columns and nine automatic SAI on a collection declaring nothing, and eleven
assignments per single-field `$set` in 10/10 CQL traces — documents a layer with no public
description, three of whose column names appear nowhere in vendor material. That is not discovery,
but "documentation of an undocumented layer whose existence changes an architecture" is worth more
than 48. I score novelty **56**, which moves the SIGMOD rubric by about **+1.5** and the weighted
composite by **+0.30** at 20 %. That credit is applied — row 3 of the ledger in §1 — and not
absorbed by rounding. It could not have been absorbed: the rounding §1 applies is *upward*, 70.70
to 71, and an upward rounding cannot swallow an upward correction. An earlier draft of this
sentence claimed it could, against a downward rounding of 71.7 to 71 that was itself unpriced; both
are withdrawn. Net of §4.4's two-point composition charge, this rubric carries **72.5** into the
composite.

---

## 5. Graded by dimension — all six graders collapsed

| # | Dimension | Score | Weight | The finding, in one sentence |
|---|---|---:|---:|---|
| 1 | **Evidence integrity and tamper resistance** | **90** | 9.09 % (10/110) | 36 files hashed, never modified across all history, three-way append-only check that fails correctly under adversarial handling, links resolved against `git ls-files`. Deduction: `main` is unprotected, so the manifest and what it seals can be rewritten in one unreviewed commit; the immutability window is one working day. |
| 2 | **Honesty and self-refutation** | **88** | 10.91 % (12/110) | Both axes where the author's employer wins are stamped NOT ESTABLISHED in the headline table, with intervals [0.465, 65.842] and [0.155, 36.683] spanning 1.0; the refuted file `findings_mongot_freshness.json` still reads `p50_ms: 1015.201` unedited beside the file that overturned it; 52 numbered points where measurement contradicted the article. This is the artefact's reason to exist and it is real. |
| 3 | **Positioning and scope discipline** | **84** | 6.36 % (7/110) | `RELATED-WORK.md` is used to narrow claims, never to pad them — it retracts the CITATION.cff keyword "write amplification" because no raw file carries a bytes-written figure, and §10 lists four claims it could not source. Deduction: written after all seven campaigns, so positioning shaped nothing; and the LSM-vs-B-tree asymmetry that explains the flagship's *direction* never reaches README's results table. |
| 4 | **Statistical method, where applied** | **82** | 9.09 % (10/110) | Separation of support is the right and nearly the only valid instrument on summary-only records; the exact permutation floor is correct (8.46e-18 = 1/C(60,30)); §3.2 pre-empts the sharpest criticism available — that identical p across 30-v-30 rows measures n and separation, nothing else. Deduction: §3.2's exchangeability defence is the wrong way round, since the live threat is block-level drift on a shared host, not serial correlation. |
| 5 | **Arithmetic correctness and re-derivability** | **92** | 5.45 % (6/110) | 93/93 classifications, intervals, median ratios and permutation p-values re-derive; 185 arms trace to source records; the published slopes reproduce to five decimals under my own refit. A hostile reader can check the entire inferential claim in ten minutes. |
| 6 | **Contribution surface and CI honesty** | **83** | 4.55 % (5/110) | Three purpose-built issue forms, a `config.yml` that routes an objector to the repository's own refutations *before* they file, a CONTRIBUTING that opens "the most valuable thing you can send this repository is a refutation", and 80 lines of workflow header on what a green tick cannot assert. Deduction: `wontfix` label retained; no CODE_OF_CONDUCT; one CI run in history. |
| 7 | **Research question and its answer** | **80** | 5.45 % (6/110) | Eight RQs with hypotheses, falsification criteria marked [PRE]/[POST], and explicit "was it refuted?" — two answered against the author. Deduction: conceded post-hoc reconstruction; campaigns 3–7 chose each hypothesis after seeing the previous result (M14 ran 17 minutes after `comparison.json`). |
| 8 | **Quality of the self-assessment** | **80** | 5.45 % (6/110) | Every runnable claim in `ARTIFACT.md` §5 that I checked reproduced. Deduction: it is stale by a commit, asserts 7 commits against a tree of 8, reasons from a now-false "nothing is published" premise, and cites a manifest file that does not exist. |
| 9 | **Documentation navigability** | **60** | 4.55 % (5/110) | ~7,150 lines of English Markdown across nine documents for 23 measurements, no table of contents in any of the nine, 21 of 32 section-naming cross-references unanchored, ~110 KB of the adversarial record French-only with README declaring French authoritative. The load-bearing self-criticism (§8.5's pass-1 selection, §6's p99 caveat) lives in the one document CI's traceability check excludes. |
| 10 | **Internal consistency of the record** | **52** | 9.09 % (10/110) | Four verified live contradictions (§3.3), each already diagnosed in-repo, each shipped. Including a six-fold false statement in the document designated normative. |
| 11 | **Targeting of the inferential apparatus** | **52** | 10.91 % (12/110) | 93 comparisons audited; the four numbers the artefact is known for audited by none of them, quoted with no interval anywhere in breach of its own `STATISTICS.md` §6 rule 2, and wrong-signed in `LIMITATIONS.md:197`. Plus 141 p99 values at n = 30 licensed by a rule set an order of magnitude too loose, two of them carrying live verdicts. **Raised from 48 — third correction note below.** The pass-1 selection *is* declared at the point of the number: `README.md:118` carries it in bold under ⛔ with the r² pair and a pointer to `ARTIFACT.md` §8.5. A dimension that penalises this artefact for failing to carry its caveats to where its numbers live must credit the one place it does. It rises no further because `RESULTS.md:128–129` — the M13/M14 rows of the register this report designates normative — carry no pass-1 caveat at all. |
| 12 | **Reproducibility of the environment** | **48** | 5.45 % (6/110) | Half the system under test absent from `env/`; four raw files with no producing script; thirteen evidence files withheld including one that qualifies a published claim; one image digest-pinned of four, and that pin contradicted by `REPRODUCING.md:187`. |
| 13 | **Construct validity of the title** | **50** | 4.55 % (5/110) | "Shredding *cost*" is operationalised as client wall-clock latency around one call, and the resulting coefficient takes ×7.50 / ×5.94 / ×1.52 across three regimes. Bytes were measured, but once and only at corpus level: `probes/disk_regime_driver.py` calls `dir_bytes()` and `count_sstables()` to put `data_dir_bytes: 6 491 369 675` and `sstables: 40` into three raw files as a disk-regime proof, and `findings_fieldbyte.json:645` re-quotes that figure as `on_disk_bytes`. No probe attributes bytes written to a mutation, which is the figure the title’s "cost" would need. The repository states the consequence itself — *"not merely imprecise; it is ill-formed"* — and does not repair it. |
| 14 | **Persistent identity and citability** | **40** | 3.64 % (4/110) | 0 tags, 0 releases, no DOI, no archival deposit, `repositoryTopics: null`, `homepageUrl: ""`, CITATION.cff with no version/commit/identifier and a `license:` naming only one of the two licences in the deposit. The citation block resolves to a mutable branch tip that has already moved substantively. |
| 15 | **Novelty** | **56** | 5.45 % (6/110) | Twelve of 23 measurements predictable from O'Neil 1996, Luo & Carey 2020, CEP-7 and Shanmugasundaram 1999 — by the artefact's own classification. M22 (silent zero count) and M1/M2 (the undocumented physical layer) survive it and are worth more than the artefact claims for them. |

**Each weight is printed twice — as a share of 100, and as the relative integer it was argued from,
over that column's true total.** Those integers sum to **110**, not 100, so the composite divides by
110: Σ(score × weight) = 7 769, and 7 769 / 110 = 70.6273… — **weighted dimensional
composite: 70.63**. That clears by six tenths the 70.0 floor of the one-decimal §2 letter map. This
line has now carried three values on three corrections: 7 696 / 110 = **69.96**, four hundredths
*under* that floor; 7 721 / 110 = **70.19** after dimension 13 went 45 → 50; and 7 769 / 110 =
**70.63** after dimension 11 went 48 → 52. One five-point judgement at weight 5/110 was enough to
carry this cut across a band boundary, and one four-point judgement at 12/110 was worth twice that
again — which is the measure of what its second decimal is worth (see below). The per-cent form is that same column
scaled by 1/110, so it changes no emphasis; printed to two decimals it sums to 99.99, and the
missing hundredth is display rounding, not a residual weight.

**Correction (this line previously read "70.9 — consistent with the rubric-weighted 71.7").** The
column was also labelled in per cent, and fifteen percentages summing to 110 are not percentages.
The old 70.9 reproduced from neither available reading: normalising over the actual 110 gives
**69.96**, and taking the figures literally as percentages gives **76.96** — both computed on the column as it then stood, with dimension 13 at 45 and Σ = 7 696. I could not recover 70.9
from these fifteen scores by any route I tried — not by dropping any single weight to bring the
column to 100 (67.96, 68.16, 68.76, 71.76, 72.16), and not by the unweighted mean (68.5). Exactly
**one** pair of reductions summing to 10 lands on 70.9 — cutting dimension 1 from 10 to 7 together
with dimension 11 from 12 to 5 — and **6,035** combinations in all once three or more weights may be
re-cut, 26 of them touching three. But every one of those re-cuts weights this document never
argued, so the figure belonged to no version of this table.
The error mattered in both directions: the literal reading would have placed the artefact at
**76.96**, which falls in the same kind of gap this correction turns on — above the C cell's printed
ceiling of 76.9, below C+'s floor of 77.0, and C+ the moment anyone rounds it. That is a seven-point
swing from the 69.96 that column then gave (70.63 after the two corrections below), six
from the 70.9 that was published, off a slip in the one number
this document offers as the independent check on its own headline. That is precisely the
defect §4.2 convicts `ARTIFACT.md` of — *"A self-assessment that is factually wrong about the tree it
assesses is not an 88"* — committed here about this document's own table, under a closing line
asserting that all factual claims were re-verified. I have corrected it by stating the divisor *and*
by printing each weight's share of 100 beside the integer it was argued from — not by re-cutting the
integers, which encode the relative emphasis argued in §1. The scaling is uniform (*w*/110), so it
moves no emphasis: dimensions 2 and 11 are still the two heaviest, dimension 2 still outweighs
dimension 5 two to one, every pairwise ratio in the column is unchanged, and a reader who distrusts
the rescaling can work from the integers, which are still in the cells.

**70.63 is 0.07 below §1’s corrected rubric composite of 70.70 — 1.07 below the rubrics as they
scored themselves, 71.7 — and 0.37 below the published final 71.** It is therefore *not*
corroboration of 71, and the earlier claim that it was is withdrawn — and it stays withdrawn even
though the two cuts have now converged to within a tenth of a point, because **that convergence
deserves no weight whatever.** They stood 0.74 apart two corrections ago and 0.51 apart one
correction ago; the gap closed because two dimensions were rescored on their merits, not because two
independent methods agreed. Reinstating the corroboration claim on a coincidence would be a worse
error than asserting it originally on bad arithmetic. The §2 map is declared to one decimal, and
70.63 sits inside its C− cell (70.0–72.9), six tenths above the floor and above the 70 floor of the
coarser calibration this exercise was run under, where C is 70–79 and D is 60–69. Two corrections
ago this cut read 69.96 and sat *under* that floor, in the map’s own gap between D+ (67.0–69.9) and
C−; the arithmetic case for D+ that it carried no longer follows. None of that is comfort: a cut
that crossed a band boundary on one five-point judgement at weight 5/110, and then moved twice as
far again on one four-point judgement at 12/110, is not evidence of anything at its second decimal. I state the margin rather than resolve it with an unshown round, because an unshown number
doing the work of an argument is precisely what §4.2 convicts `ARTIFACT.md` of, and precisely what
the original 70.9 did here.

**So does the D band apply?** I hold the C, and on substance rather than on the second decimal. Two
reasons, in that order of weight. First, the D band on this calibration means *the honest parts do
not carry the unsound parts*, and here they do carry them: the structural results — the twelve
physical columns, the nine automatic SAI, the eleven assignments per single-field `$set`, the silent
zero count — rest on raw evidence never modified in the repository's history, while the figures that
do not stand are stamped NOT ESTABLISHED in the artefact's own headline table and quarantined by its
own reading rule 8. A reader who follows this repository's instructions is not misled by it, and
that is the line between C and D. Second, on the instruments: §1's rubric weights are argued one by
one, in a column that exists for that purpose, and sum to 100 by construction, whereas the fifteen
weights above are asserted with no justification column at all. Where an argued aggregation and an
unargued one differ by half a point, the argued one carries the headline.

So the headline remains **71** — §1's rubric aggregation, adjusted for §4.4 and §4.5, is what
produced it, and this dimensional cut is a check on that number, not its source. But the check still
lands half a point low, and clears the floor by only nineteen hundredths, which remains a real
argument for 70 rather than 71 and is recorded here as such: read the grade as **C− at the floor of
its band**. That is not a new position for this report — on §1's
corrected set, three of its six rubrics land in the D band already (statistician 68, hostile
procurement 66, OSS maintainer 67) — and a reader who prefers the dimensional cut to the rubric
cut is entitled to it. The only other figure derived from this composite is
§7's ladder base, which moves with it and is restated there; nothing else in this document does.

**Second correction (dimension 13, 45 → 50; dimensional composite 69.96 → 70.19).** The row above
opened *"‘Shredding cost’ was never measured in bytes by any probe in seven campaigns"*, and two
prose passages carried the same universal — §6’s ceiling item 2 (*"zero-measured across seven
campaigns"*) and §8’s MAY-NOT item 6 (*"no probe in seven campaigns measured a byte"*). All three
are false about this tree. `probes/disk_regime_driver.py` defines `dir_bytes()` and
`count_sstables()` and calls them either side of the fill (lines 157–158, 198, 219–220);
`data/raw/findings_disk_rf3.json`, `data/raw/disk_state.json` and `data/raw/disk_state_c4.json`
each record `data_dir_bytes` 0 → 6 491 369 675 (6 491 383 676 in c4) beside `sstables` 0 → 40 and
`compactions_completed` 651 → 729; and `findings_fieldbyte.json:645` — the file the per-KiB
coefficient comes out of — re-quotes that byte figure inside a `disk_proof` block. The claim was
also self-contradictory within this document, since §6’s own A− recipe names `count_sstables()` and
`dir_bytes()` as tooling already sitting in that probe. The narrower claim, which those passages now
make, is true: no probe attributes bytes *written* to a mutation. Write amplification per `$set`,
compaction load in bytes and CPU-seconds are unmeasured — `data/raw/` carries no per-run CPU figure
at all, only `cpu_model` and `cpu_count` in the environment blocks.

**Why five points and not more.** The correction repairs the record, not the construct. One
whole-keyspace `du -sb`, taken once to show that 6.05 GiB clears a 2 GiB memtable budget, prices no
operation and does not operationalise "cost per shredded field"; the title still rests on a
client-latency coefficient that moves ×7.50 / ×5.94 / ×1.52 with the regime, and the artefact’s own
verdict on it — *ill-formed* — stands. A seven-point move to 52 was put to me and I decline it: this
is a construct-validity score, and the construct did not improve. Five points at weight 5/110 is
+0.23 of composite.

**A defect this correction uncovered, deliberately left unpriced.** The overstatement was inherited
from the artefact. `docs/RELATED-WORK.md:71` asserts in bold that *"No file under `data/raw/`
contains a bytes-written, SSTable-bytes, write-amplification or CPU-seconds figure"*, and §9 item 1
(`:553`) that *"No byte-level figure exists anywhere in `data/raw/`"*. Both are false as to SSTable
bytes — `data_dir_bytes` is `du -sb` over the keyspace’s SSTable directory — and the second is false
more broadly (`total_bytes`, `bytes_per_field`, `wire_bytes`, `on_disk_bytes`). That is a false
statement in the repository’s own record beyond the four §3.3 convicts, and it belongs to dimension
10, which this pass did not re-audit. It is flagged, not scored. Priced at three points it would
cost 0.27 of composite — more than this correction credits — so the move from 69.96 to 70.19, and
the band boundary it crosses, should be read as provisional on that audit.

**Third correction (dimension 11, 48 → 52; dimensional composite 70.19 → 70.63).** §7 item 1 read
*"State in `METHODOLOGY.md` §6 and at every occurrence that 44×/79×/40×/72× are **pass-1-only
fits**"*, and this dimension was scored — at the joint-heaviest weight in the table — partly on the
premise that the pass selection was undeclared where the number lives. **That premise is false at
the most prominent occurrence there is.** `README.md:118` — the Principal-results row §7 item 7
measures at 841 characters — already declares it in bold, under this report's own ⛔ register: *"the
slopes are fitted on **pass 1 only**, undeclared until now ([ARTIFACT.md §8.5](ARTIFACT.md)), and
MongoDB's denominator is near-flat (r² 0.78 / 0.88 against HCD's 0.997)"*. The pass selection, the
weak denominator, the r² values and the pointer to the self-assessment are therefore all at the
point of the headline number. `METHODOLOGY.md` §6 carries the low-r² finding for these same ratios
at lines 342–344 and the words *"**No confidence intervals.** Anywhere."* at line 334, and
`docs/RESEARCH-DESIGN.md:381`, `docs/THREATS-TO-VALIDITY.md:452` (X2), `docs/RELATED-WORK.md:254`
(§3.8) and `ARTIFACT.md` V11 each record the hard-coded `pass1` key independently.

**What survives is narrower, and is entirely undone.** No interval for these four numbers is
published anywhere in the tree — I grepped the repository and found none — the pass-2 magnitudes
(116.4× and 86.3×, a 2.6× swing) are nowhere stated, and `LIMITATIONS.md:197` is backwards about
them. That is a missing-interval defect, not an undisclosed-selection defect, and 48 at 12/110
over-priced it. §7 item 1's imperative has been rewritten accordingly; its hours are unchanged,
because the intervals and the refit are what those four hours buy and neither exists in any form,
but its Δ falls from +2.8 to +2.4 — the four points at 12/110 come out of the headroom it was
claiming.

**Why four points and not eight.** Eight was put to me and I decline it. *"At every occurrence"* was
wrong but not absurd: `RESULTS.md:128–129`, the M13 and M14 rows of the document this report
designates normative, carry no pass-1 caveat whatever, and neither do `RESULTS.md:22` and `:51`,
`LIMITATIONS.md:54`, `:220`, `:260`, `:277–278`, `:348`, `:586`, `METHODOLOGY.md:193` and `:455`,
`data/README.md:383` and `:574`, or `ADR-001:207–208`. The disclosure sits at README's headline row
and in four audit documents; it does not travel with the number through the register — which is the
same failure §3.2 convicts on the p99 caveat, and it would be incoherent to credit here what is
debited there. Nor does the disclosure touch the three clauses this dimension was actually scored
on: the four numbers are still audited by none of the 93 comparisons, still quoted with no interval
in breach of `STATISTICS.md` §6 rule 2, and `LIMITATIONS.md:197` is still wrong-signed. Four points
at weight 12/110 is +0.44 of composite, twice what the dimension-13 correction moved.

**A defect this correction uncovered, deliberately left unpriced.** `docs/RELATED-WORK.md:254`
states of this very selection that ***"Nothing in the dossier's prose declares it"*** — which
`README.md:118` falsifies. That is a fifth live contradiction of exactly the kind §3.3 catalogues,
and it is the sentence this report read and believed: the artefact's own most recent audit document
asserts the non-disclosure this note now withdraws. It belongs to dimension 10 and to §3.3, neither
of which this pass re-audited, so it is flagged and not scored. Priced at three points it would cost
0.27 of composite — more than half of what this correction credits — so the move from 70.19 to 70.63
should be read as provisional on that audit, exactly as the second correction's is.

---

## 6. The ceiling

### Without new measurement: **B / B+ (about 84–87) — and §7's ladder computes 84.0**

Everything in §7 is editing, packaging and re-analysis of data already in `data/raw/`. Executed in
full — the persistent identifier minted, the withheld archive published, the HCD compose shipped,
the four self-diagnosed record defects repaired, the slope intervals published, the p99 caveat
moved to where the numbers live — this becomes an artefact that earns **Artifacts Available** and
**Evaluated-Functional**, and plausibly **Evaluated-Reusable**. That is an honest, well-bounded
mechanism study with an exemplary integrity apparatus. **It is a B.** §7's ladder, re-derived
dimension by dimension in §7.1, totals **+13.0** and lands the artefact at **84.0** — the bottom of
this band, not the top of it. 87 is reachable only if every repaired dimension lands at the
optimistic end of what editing alone can reach.

**Correction (§7 previously totalled "+17.5 → about 88" against this band).** The two sections priced
the same programme of work — §6 opens by stating that everything in §7 is editing, packaging and
re-analysis of data already in `data/raw/` — and disagreed by 1.5 points across a ceiling this
section calls absolute. 71 + 17.5 is 88.5, printed as "about 88"; both figures breach the 87 above.
The band was not the error and is unchanged: the §7 deltas were, and §7.1 now derives each one from
§5's dimension scores and weights instead of asserting it.

**It cannot exceed B+ without new measurement, and four things cap it:**

1. **The samples are gone.** 23 of ~25 latency-bearing files retain only summaries. No interval, no
   rank test, no re-percentiling, for 91 of 93 comparisons, permanently. An exemplar of this kind
   invites statistical re-analysis; this one forecloses it.
2. **The title construct is measured only at corpus level.** "Write cost" as bytes attributable to
   an operation — write amplification per `$set`, compaction load in bytes, CPU-seconds — is
   unmeasured across seven campaigns. What exists is one whole-keyspace figure captured to prove
   the disk regime (`data_dir_bytes: 6 491 369 675` beside `sstables: 40`, in
   `findings_disk_rf3.json`, `disk_state.json` and `disk_state_c4.json`), and it prices no
   operation. The flagship per-byte coefficient is therefore ill-formed by the artefact’s own
   argument, not merely imprecise.
3. **One implementation of shredding cannot support a claim about shredding as a class.** The title
   generalises to "document databases" on n = 1. `RELATED-WORK.md` §9 item 8 concedes this.
4. **No genuinely disk-bound read exists anywhere in the dossier** — `RESULTS.md` M15 states this
   itself, because every RMW probe re-reads the row it just wrote. Every per-KiB rate published
   here is a memtable/cache coefficient.

### With new measurement on new hardware: **A− (about 90–92)**

Reachable, and the recipe is already written — `docs/STATISTICS.md` §5 and `RESEARCH-DESIGN.md`
§5.4, executed *before* the runs instead of after them: an idle, owned, digest-pinned stack; the
sample vector persisted beside every summary; three timestamps per observation; a declared
offered-rate schedule identical across arms; n fixed by a power calculation against a pre-declared
minimum effect; arms interleaved rather than blocked; and **bytes written per single-field
mutation**, using the tooling already sitting in `probes/disk_regime_driver.py`
(`count_sstables()`, `dir_bytes()`) — the one figure that is cache-independent, percentile-free,
regime-free and host-independent, and therefore the only one that would transfer to a reader's
hardware without re-running anything.

**A (93+) is not reachable at all**, because A on the calibration means a reviewer would cite this
as *how to do this*, and the exemplars in that class — a study whose protocol was tagged before the
first probe ran, on hardware the author controlled — differ from this one in kind. This artefact is
the honest post-mortem of a study that did not do those things. Graded as that, it is good. Graded
as the study, it is a C−.

---

## 7. The shortest path up — ranked by composite points per hour, item 1 excepted

*Ranked by Δ composite per hour, with one deliberate exception: **item 1 is promoted** to the
top at 0.60/hr although five rows below it earn more per hour, because it is the only entry that
touches the four numbers every reader will quote, and because the data for it have been sitting in
`data/raw/` since 09:33 on the day of the runs. Items 2–9 are in strict rate order.*

| # | Action | Hours | Δ composite | Δ/hr | Files |
|---:|---|---:|---:|---:|---|
| 1 | **Publish the slope intervals and the pass-2 refit.** Add `docs/STATISTICS.md` §3.18 with the six slopes, their SEs and r², the Fieller intervals [26.0, 138.9] and [39.9, 2950.4], and the finding that on pass 2 **both intervals are unbounded** because the MongoDB denominators are not distinguishable from zero. Publish the **pass-2 magnitudes** — 116.4× and 86.3×, a 2.6× swing — which appear nowhere in the tree. Carry the pass-1 caveat from `README.md:118`, which already has it, to `RESULTS.md:128–129`, which does not. Correct `LIMITATIONS.md:197`. | **4** | **+2.4** | **0.60** | `docs/STATISTICS.md`, `METHODOLOGY.md`, `LIMITATIONS.md`, `README.md`, `RESULTS.md` |
| 2 | **Mint the persistent identifier.** `git tag -s v1.0.0`, `gh release create v1.0.0`, enable the Zenodo hook, write concept + version DOI, `version` and `commit` into `CITATION.cff`, fix its `license:` to the Apache-2.0 + CC-BY-4.0 pair. This is the only ACM badge currently within reach; `ARTIFACT.md` §7.2 has the eight steps. | **1** | **+1.4** | **1.40** | `CITATION.cff`, `README.md`, GitHub settings |
| 3 | **Repair the four record defects, then put each in CI.** `DISCLAIMER.md:18` → "24 of 36"; delete the six campaign-7 "never challenged" sentences in `RESULTS.md`; correct `METHODOLOGY.md` §1 with a cross-reference to `RESEARCH-DESIGN.md` §5.2 ("six of sixteen"); delete `RESEARCH-DESIGN.md:756`. Then add check 8: recount `run_at_utc`, grep the retracted sentences, assert `rev-list --count` against `ARTIFACT.md` §1.4. | **3** | **+4.1** | **1.37** | four `.md` files, `.github/scripts/check_record_consistency.py`, `.github/workflows/verify-evidence.yml` |
| 4 | **Packaging.** 6–8 topics, homepage, description cut to ~110 chars so the unfurl survives, CI badge in README, embed `regime-collapse.svg` after the abstract, disable the empty wiki, delete `wontfix`, protect `main` with `verify-evidence` required. | **1.5** | **+1.2** | **0.80** | GitHub settings, `README.md` |
| 5 | **Move the p99 caveat to where the numbers live.** Replace `STATISTICS.md` §6 rule 4's n < 10 floor with the order-statistic weights `pct()` implies (at n = 30: p99 = 0.29·x₍₂₉₎ + 0.71·max), and attach it in `README.md`, `RESULTS.md` and `data/README.md` — especially to `RESULTS.md:201` and `:227`, the two live verdicts riding on a p99. | **2** | **+1.3** | **0.65** | `docs/STATISTICS.md`, `README.md`, `RESULTS.md`, `data/README.md` |
| 6 | **Publish the thirteen withheld files** into `data/raw/withheld-20260917/` with a README stating the reason each was held, and update `probes/README.md` gap 8 to closed. If any cannot be published, name each one and say why. This is the item that blocks Evaluated-Functional by itself, and `probe4_traced.json` qualifies M4. | **2** | **+1.3** | **0.65** | `data/raw/`, `probes/README.md`, `.github/evidence.sha256` |
| 7 | **Restructure the Principal-results table.** Row 118 is **841 characters** and its fourth cell — carrying the ⛔ that voids the claim — is 425 of them, behind horizontal scroll on a phone. Fold the disqualifying clause in bold into the margin cell; move the reserves to numbered `###` notes beneath. | **1.5** | **+0.4** | **0.27** | `README.md` |
| 8 | **Ship `env/docker-compose.hcd-dataapi.yml`** with every unrecorded value marked `[U]`, and pin the atlas-local digest at `REPRODUCING.md:187` (`@sha256:e118f5c1…`, already in `data/raw/findings_mongot_provenance.json`). | **2** | **+0.5** | **0.25** | `env/`, `REPRODUCING.md` |
| 9 | **Add TOCs and anchors** to the nine long documents; anchor the 21 unanchored section-naming links; extend `check_links.py` to heading anchors. | **3** | **+0.5** | **0.17** | nine `.md` files, `.github/scripts/check_links.py` |

### 7.1 How the Δ column is computed

**Correction (this column previously carried +4.0, +3.5, +2.5, +2.5, +1.5, +1.5, +1.0, +0.5 and
+0.5 — summing to +17.5, under a total line reading "+17.5 → about 88").** Three things were wrong
with it. The column sum was right — 17.5 — but 71 + 17.5 is **88.5**, not the "about 88" printed, so
the total line rounded its own arithmetic down by half a point without saying so. Both 88.5 and 88
sit **above the 87 ceiling §6 declares one section earlier for this exact set of repairs**, and §6
opens by stating that everything in §7 is editing, packaging and re-analysis of data already in
`data/raw/` — so the two sections priced the same programme of work 1.5 points apart. And the
deltas were stated without derivation, which is how the breach went unnoticed: at least one was not
merely generous but **unreachable**. Minting the DOI was awarded +2.5, and it moves dimension 14
alone, which carries 4 of 110 and stands at 40 — so even a perfect 100 there is worth
60 × 4 / 110 = **2.18**. The band in §6 is not what was wrong. This column was. It is re-derived
below and now totals **+13.0** (+13.1 on the rounded column).

Each Δ is now the movement the item produces in §5's weighted dimensional composite:
Σ(Δ dimension × weight) / 110, on §5's own scores and relative weights. Nothing in the column is a
judgement of the item's importance — item 1 is the most important row on the list and is only
second by delta, behind a three-hour editing pass — only of how much of the composite the item can
physically move. The post-repair scores assumed, every one of them arguable and each stated so it
can be argued with:

| §5 dimension | w | now | after §7 | moved by | why it stops there |
|---|---:|---:|---:|---|---|
| 1 Evidence integrity | 10 | 90 | 96 | 3, 4 | Branch protection closes §4.1's one non-housekeeping finding; the sha256's own limits, which the workflow header already concedes, do not close. |
| 2 Honesty and self-refutation | 12 | 88 | 91 | 6 | The single gap where honesty is asserted but not performed shuts; the rest of the dimension was already near its ceiling and nothing in §7 adds to it. |
| 4 Statistical method | 10 | 82 | 88 | 1, 5 | Regression documented, percentile rule re-founded on the order statistics `pct()` actually implies; summary-only records still forbid every instrument cap 1 in §6 names. |
| 6 Contribution surface and CI | 5 | 83 | 88 | 4 | `wontfix` gone, badge added, check 8 in the workflow; no CODE_OF_CONDUCT and a run history of one or two remain. |
| 8 Quality of the self-assessment | 6 | 80 | 86 | 3 | Staleness put under CI and the two false premises repaired; whether its badge reasoning is sound is still the author's judgement about the author. |
| 9 Documentation navigability | 5 | 60 | 82 | 4, 7, 9 | TOCs, anchors and the 841-character row; ~110 KB of French-only adversarial record is not translated by editing, and README still declares French authoritative. |
| 10 Internal consistency of the record | 10 | 52 | 92 | 3 | All four contradictions repaired **and** each put under CI, which is what turns a diagnostic apparatus into a corrective one. Not 100: CI catches the four sentences it is told to grep. |
| 11 Targeting of the apparatus | 12 | 52 | 80 | 1, 5 | The apparatus finally aims at the four numbers everyone quotes — but the widest it can publish is Fieller on five medians per arm, because the samples are gone. This is the dimension the destroyed samples cap, and it carries the most weight. |
| 12 Reproducibility of the environment | 6 | 48 | 75 | 6, 8 | Withheld files published, HCD compose shipped, atlas-local digest pinned; **two** of the four unscripted raw files still have no producer — item 6's archive holds exactly two scripts (`probes/README.md` gap 8), and `control_read.py` produces `control_read_A_run1/2.json`, leaving `findings_hcd_vec_freshness.json` and `tier_comparison.json` — eight probes still cannot answer `--help`, and the Data API environment is still recorded `[U]`. |
| 14 Persistent identity and citability | 4 | 40 | 90 | 2, 4 | Everything this dimension prices — DOI, tag, release, CITATION fields, topics, homepage — is purchasable in 2.5 hours. It is also the lightest dimension in the table, at 4 of 110. |

Dimensions **3** (positioning, 7), **5** (arithmetic, 6), **7** (research question, 6), **13**
(construct validity, 5) and **15** (novelty, 6) do not move at all. Dimension 5 has nothing to
repair; the other four were fixed by choices made before the first probe ran and cannot be edited
afterwards. Together they carry **30 of the 110**, and that — not a judgement about ambition — is
the arithmetic reason a no-new-measurement ceiling exists at all.

Two notes on reading the column. It is rounded to a tenth: the rounded entries sum to **+13.1**,
the unrounded to **+12.955**, and the total line below quotes both rather than rounding silently,
which is the specific failure this section corrects. And the Δs are computed on §5's dimensional cut,
which §5 now puts at **70.63**, 0.37 below the published 71; applied to that base the full ladder
still lands at **83.6** — unchanged, because raising dimension 11 lifted the base and shortened the
ladder by the same 0.44 — and applied to the published 71 at **84.0**; both **B** on §2's map. §6's
band is stated on the published grade, so **84.0** is the figure to compare against it — but a
reader who prefers §5's base should note that the ladder then lands just *below* the declared band,
which is one more mild argument for 70 rather than 71.

**Total: 20.0 hours, +13.1 by the column (+13.0 unrounded) → about 84.0.** That is inside §6's
without-new-measurement band of 84–87 and sits at its lower edge, not above it. The first four rows
are **9.5 hours for +9.1** and carry the whole distance from C− to B−, landing at **80.1**;
items 5–9 are 10.5 hours for the remaining +4.0. The fastest four hours on the list are items 2 and
3 — **+5.5 at 1.38/hr** — which reach 76.5 in an afternoon. Item 1 is the slowest row in the top
half and is placed first anyway, for the reason stated above the table; taken with item 3 it is
seven hours for **+6.5 at 0.93/hr** and moves the grade from C− to C+ at 77.5.

**What is not on this list, and why:** attributing bytes to a mutation. It would be worth more than items 2 and
4–9 combined (+6.6 of the +13.1) — it is the quantity the title names, it is regime-free, it
transfers to a reader's hardware, and it is the only thing that unlocks dimension 13, which is
frozen at 50 above. But it is a new campaign, not a revision, and it belongs to the *with new
measurement* ceiling in §6.

---

## 8. What a reader may and may not do with this repository today

### You MAY, without re-measuring anything

These results are structural, not statistical. They do not depend on the host, the load, the cache
regime, the percentile or the sample size. They are falsifiable in fifteen minutes by anyone with a
container, and they are the reason this repository is worth its 1.3 MB.

1. **Treat every single-field `$set` on HCD's Data API as a read-modify-write under Paxos whose
   cost is charged against the total indexed content of the document, not against the delta.**
   `SELECT key, tx_id, doc_json` then one `UPDATE … IF tx_id = ?` carrying **eleven assignments**
   over a **twelve-column** row with **nine automatically created SAI**, in 10 of 10 traced
   operations, identical at RF 1 and RF 3. *(M1, M2 — `findings.json`, `findings_rf3.json`)*
2. **Assume no server-side aggregation pipeline on this build.** `aggregate`, `$group` and
   `distinct` return `COMMAND_UNKNOWN`; the corpus crosses the client. *(M20 — the captured
   `COMMAND_UNKNOWN`; note the nineteen-command list itself is report-transcribed, not captured)*
3. **Assume exact counting is capped at 1 000 documents on a stock container**, and that a client
   `upper_bound` does not move it. *(M21)*
4. **Never trust `estimatedDocumentCount()` on a freshly loaded HCD collection.** It returned **0**
   against a true 200 000, reading pre-flush SSTable metadata, with nothing in the API signalling
   the condition. If your code branches on `if count == 0`, it will conclude an empty collection.
   *(M22 — the most actionable single finding here)*
5. **Expect the Data API to refuse any indexed string above 8 000 bytes**
   (`SHRED_DOC_LIMIT_VIOLATION`). *(`probes/README.md` patch table — uncovered in passing, never
   assigned an M-number)*
6. **Fork the apparatus.** The append-only evidence policy, the three-way manifest check, links
   resolved against `git ls-files`, the reserve column that grades ⛔ (voids the claim) apart from
   ⚠︎ (bounds its magnitude), the issue forms that route an objector to the repository's own
   refutations first, and the workflow header that enumerates what a green tick cannot assert —
   this is the best-executed part of the artefact and it generalises.

### You MAY NOT, on this evidence

1. **Quote 44×, 79×, 40× or 72× as a magnitude.** They are ratios of two OLS slopes over five
   median points, fitted on one of two collected passes. On the other pass they are 116.4× and
   86.3×, and on that pass **neither has a finite confidence interval**, because both MongoDB
   denominator slopes have 95 % CIs containing zero. The honest statement on pass 1 is *"at least
   about 26×, upper bound poorly determined"*; on pass 2 there is no honest upper bound at all.
2. **Quote 602×, 19.6×, 21.7×, 0.7775 ms/KiB or any latency ratio as a production figure.** One
   shared QEMU VM at load average 14–16 carrying unrelated workloads, no root so the page cache was
   never dropped, ~13 GiB/node of unpurged `system.paxos` residue, a single sequential closed-loop
   client, three "replicas" co-located on one host so the Paxos round is measured where it costs
   least. The 602× arm is **n = 3**.
3. **Quote any p95 or p99 from this corpus as a tail characterisation.** 141 of 186 published p99
   values sit at n = 30, where p99 is `0.29·x₍₂₉₎ + 0.71·max` — a blend of the top two of thirty.
4. **Use the search-freshness axis for anything.** It compares HCD `{dc1:3}` against a *different
   MongoDB deployment* (8.3.11 `atlas-local`, mongot 1.75.1 `localDev`, single node — audit I8), a
   development container nobody runs in production, and it puts lexical search against vector
   search. The README already marks both HCD-favourable axes **NOT ESTABLISHED**, with intervals
   [0.465, 65.842] and [0.155, 36.683] spanning 1.0. What survives is the **miss-rate count**
   (0/30 against 30/30 at τ = 0, Fisher p = 8.46e-18), not the latency.
5. **Cite the tier's share of the cost.** M12 says ~29 %, M14 says ~9 %, on the same quantity. Never
   reconciled (audit I3). Three estimands, not three estimates.
6. **Read the title as a statement about shredding as a class.** One implementation, no second
   design point, and **no probe attributed bytes written to a mutation** — corpus-level
   `data_dir_bytes` was captured in three files as a regime proof, but write amplification per
   `$set` is unmeasured; the `CITATION.cff` keyword claiming it was retracted for that reason.
7. **Cite this repository at a fixed state.** 0 tags, 0 releases, no DOI, `main` unprotected. The
   citation block resolves to a branch tip that has already moved substantively (`bdbc5c0` rewrote
   figures across eight files), and can be force-pushed without trace.
8. **Believe `DISCLAIMER.md` on dates, `METHODOLOGY.md` §1 on pre-registration, `RESULTS.md` on
   campaign 7 being unchallenged, or `RESEARCH-DESIGN.md`'s closing line on references.** All four
   are false at HEAD, and three of the four are contradicted elsewhere in the same repository.
9. **Assume the published evidence is the whole evidence.** Thirteen files are withheld, including
   `control_read_B.json`, on which a published number rests, and `probe4_traced.json`, which
   qualifies M4's "70/70 at `LOCAL_QUORUM`" with `ONE` 42 and `LOCAL_ONE` 2.

### The one-sentence operative rule

**Read the structural results as findings and the latency results as an anecdote with excellent
provenance** — which is what `README.md` reading rule 8 already tells you to do, and which is the
only instruction in this repository that both the most generous grader and the harshest one agreed
should be followed.

---

## 9. Closing note for the author

The calibration for this exercise warned that grade inflation was the failure mode, and the reason
is specific to this artefact: its integrity is so unusual that a reviewer is tempted to grade the
integrity instead of the study. I have tried not to. An IBM employee publishing a table in which
his own product's only two wins are stamped *the margin is not a result* is something I have not
seen done, and it is worth saying plainly. It is also not a substitute for a confidence interval on
the number on the front page.

The single finding I would ask you to sit with is §4.4. You built a 93-comparison inferential
apparatus, wrote 760 lines of statistical policy, put ten quoting rules in front of the reader, and
then exempted the four numbers everyone will quote — by a policy line in `inference.json`
(*"division or subtraction only. No model, no fit"*) that reads as rigour and functions as an
exclusion. The interval was computable from five medians per arm that have been in `data/raw/`
since the day of the runs. That is not a rigour problem. It is a targeting problem, and the target
it missed is the only one that mattered.

The second is §3.3(ii). Your own `THREATS-TO-VALIDITY.md` X8 wrote the sentence *"That sentence was
true when written and is now false"* about the six campaign-7 disclaimers in `RESULTS.md` — and
then the repository shipped with all six intact. An apparatus that finds its own defects and does
not close on them is a diagnostic instrument, not a corrective one. Item 3 in §7 exists to make
that class of failure impossible rather than merely documented, and it is three hours.

---

*Reconciled from six independent rubrics. All factual claims re-verified against the working tree at
commit `ff84757` on 2026-09-18 — with three exceptions, all since corrected. The §5 dimensional
composite was published as 70.9, a figure reproducible from no reading of its own weight column, and
now reads 70.63 over a stated divisor of 110 (see the correction notes under the §5 table). And §7's Δ column totalled +17.5, putting its
no-new-measurement ladder at about 88 — above the 84–87 band §6 declares for that same programme of
work — and is now re-derived dimension by dimension in §7.1, totalling +13.0 and landing at 84.0
(see the correction notes in §6 and §7.1). And three passages asserted that no probe in seven
campaigns measured a byte, which `probes/disk_regime_driver.py` and three files under `data/raw/`
refute; the true claim is that no probe attributed bytes written to a mutation (see the second
correction note under the §5 table). And §7 item 1 demanded a pass-1 disclosure that
`README.md:118` already carries in bold under ⛔, over-pricing the deduction behind it; dimension 11
is raised from 48 to 52 in consequence (third correction note under the §5 table). All six CI checks were run and pass. The slope refits, Fieller intervals, percentile census, `run_at_utc` count, probe
`--help` survey, inference-census coverage and GitHub surface facts in this document were computed
directly and are reproducible from `data/raw/` and `gh`.*
