# ARTIFACT.md — artefact-evaluation record

This document assesses `shredding-cost-hcd-mongodb` **as a deposited research artefact**, not as
prose. It states what the artefact contains, which ACM badge it can honestly claim and which it
cannot, the exact environment contract, a cryptographic manifest of the evidence, a
claim-to-command table an evaluator can run, and the concrete steps required to make the artefact
archival.

It is written to the ACM badging vocabulary — *Artifacts Available*, *Artifacts Evaluated —
Functional*, *Artifacts Evaluated — Reusable*, *Results Reproduced* — as defined in **ACM Artifact
Review and Badging, Version 1.1, 24 August 2020**
(<https://www.acm.org/publications/policies/artifact-review-and-badging-current>; the four badge
definitions quoted in §2 were verified word for word, on 18 September 2026, against
<https://sigir.org/general-information/acm-sigir-artifact-badging/>, which reproduces the v1.1
wording in full — the ACM page itself refuses automated retrieval. That page's own header dates the
policy 20 August 2020, but each definition it prints is stamped *[v1.1 as of August 24, 2020]*,
which is ACM's approval date and the date used here.)

**The rule that governs this document is the rule that governs the dossier.** The experiment was
built so that it could prove its own author wrong, and repeatedly did. Nothing here softens a
finding unfavourable to HCD, to MongoDB, or to the author. Where this document departs from the
repository's own prose it does so to **narrow** a claim, never to widen one — including in
§8, where it narrows one of the repository's own self-accusations because that self-accusation is
factually overstated.

**Assessment date:** 18 September 2026. **First written** against commit `b61eef4`; **re-verified
and re-stated** against commit `457568f` the same day, after ten further commits landed.
**Assessed tree:** working tree at commit `457568f` (HEAD) — see §1.4, which records both states.
The tree was being edited by other sessions throughout; every count in this document is now
regenerated from the tree by `.github/scripts/check_artifact_table.py` and verified in CI, because
the first writing of it went stale within hours and nothing caught that. Where a defect this
document found has since been **fixed**, §8 says so rather than deleting the finding.

---

## 1. What the artefact contains

### 1.1 Directory contract

| Path | Contract | Mutability |
|---|---|---|
| `data/raw/` | **The evidence** — file count and total size in §1.3, generated from the tree. Every published figure must resolve here or to a named campaign report. Byte-identical to what the probe wrote — not reformatted, not re-keyed, not corrected after refutation. | **Frozen.** Never edit. A correction is a new file plus a note in the campaign report. §4 makes any later alteration detectable. |
| `data/MANIFEST.sha256` | One SHA-256 per evidence file, in `sha256sum` format. Checkable without this repository's scripts: `sha256sum -c data/MANIFEST.sha256`, **from the repository root** — its paths are root-relative, so run from inside `data/` it reports every file missing. | Regenerated only when `data/raw/` legitimately changes; CI job 1 fails otherwise. |
| `data/README.md` | Data dictionary: one entry per raw file, its host fingerprint, and the rules for quoting a number out of the directory. | Prose; may be corrected. |
| `data/derived/` | Re-analysis computed *from* `data/raw/`. Currently `inference.json` (137 KiB), the companion to `docs/STATISTICS.md`. | Regenerable. Not evidence. |
| `probes/` | **The Python instruments**, the code as it ran, plus `.orig` reference copies; counts in §1.3. | Frozen as a record. Patches are declared in `probes/README.md`. |
| `probes/README.md` | Probe index **and provenance register** — which instrument was vendor-supplied, which was patched, which the measurer wrote — plus a numbered list of its own gaps (1–8). | Prose; may be corrected. |
| `docs/campaigns/01..07`, `docs/campagne7bis.fr.md` | **Eight** campaign reports, in French, as written at the time (campaign 6 amended additively, declared in `README.md`). 7bis is the re-run of the aggregation axis; it sits outside `docs/campaigns/` because it is a re-run rather than a new axis, and it reversed three of campaign 7's findings. | Working records. |
| `docs/audit-adversarial.fr.md`, `docs/challenges.fr.md`, `docs/challenges-campagne7.fr.md` | The hostile half: integrity findings I1–I9, challenges C1–C15, meta-challenges D1–D5, and the campaign-7 round. French is authoritative; `LIMITATIONS.md` is an English synthesis **reorganised by severity**, not a translation. | Prose. |
| `docs/adr/ADR-001-modelling-policy.md` | Modelling policy and the evidence register for M1–M8, M10–M19. **M20–M23 are not in it.** | Prose. |
| `docs/RESEARCH-DESIGN.md`, `docs/THREATS-TO-VALIDITY.md`, `docs/RELATED-WORK.md` | The design reconstruction, the threat register (I/C/D identifiers classified by validity type), and the positioning against prior work. | Prose. |
| `docs/synthesis/huit-axes.fr.html` | The eight-axis synthesis, in French. | Prose. |
| `docs/figures/` | `regime-collapse.svg`, re-rendered from `data/raw/` and diffed byte for byte in CI. | Regenerable. |
| `docs/STATISTICS.md` | What may and may not be inferred: separation of support, the discarded-series defect, coordinated omission, quoting rules. | Prose. |
| `docs/article/` | **Out of scope for this artefact.** The author's own publication, under verification. Defects in it are flagged, never edited. | Out of scope. |
| `env/` | `requirements.txt` and the MongoDB replica-set compose file. **Half the system under test is absent** — see §3.3. | Reconstruction. |
| `README.md`, `RESULTS.md`, `METHODOLOGY.md`, `LIMITATIONS.md`, `REPRODUCING.md`, `DISCLAIMER.md`, `CONTRIBUTING.md`, `ARTIFACT.md` | The English documents. `RESULTS.md` §3 is the normative register, M1–M8 and M10–M23. | Prose. |
| `.github/` | **Normative, not prose.** `workflows/verify-evidence.yml` and the `check_*.py` scripts it runs (counts in §1.3), the source-line-citation manifest `probe-citations.sha256`, issue and pull-request templates, and the working records `IMPROVEMENT-PLAN.md`, `WORK-ORDER-d12-html.fr.md`. | CI is normative; the working records are prose. |
| `LICENSE`, `LICENSE-docs`, `CITATION.cff`, `.gitignore` | Apache-2.0 for code, CC BY 4.0 for documents and data; citation metadata; ignore rules. | Fixed. |
| `CITATION.cff` | Citation metadata. Incomplete — no `version`, no `commit`, no `identifiers`, no DOI. | See §7. |

### 1.2 What the evidence is, and what it is not

`data/raw/` is **unedited**. It is **not complete**, and the distinction is load-bearing:

- **Sixteen of the seventeen probes persisted no per-observation latency.** The shared `dist()` /
  `distribution()` helper in every latency probe written before campaign 7bis consumes the sample
  list and returns `{n, min_ms, p50_ms, p95_ms, p99_ms, max_ms, stdev_ms}`. Those samples are
  gone. For any latency figure produced by those sixteen, no reader — including the author — can
  recompute a percentile, bootstrap an interval, test a distributional claim, or apply a different
  estimator.
  An earlier revision of this line read *"No probe persisted a per-observation latency"*. That was
  true when it was written and **campaign 7bis made it false the same day**: `probe_agg_7bis.py`
  defines a `dist()` that returns the same seven keys **plus `raw_ms`**, "every timed observation,
  in execution order", with a `raw_note` saying why. It is the only probe in the tree containing
  `raw_ms`.
- **Four files are the exception, two of them new.** `vector_freshness_idle.json` and
  `vector_freshness_loaded.json` retain all 60 per-cycle `insert_to_vec_visible_ms` observations
  under `cycles[]`, and `docs/STATISTICS.md` uses them. `findings_agg7bis_hcd.json` (five `raw_ms`
  arrays) and `findings_agg7bis_mongodb.json` (nine) retain every timed observation of the
  aggregation re-run. Those two are why `docs/campagne7bis.fr.md` carries the first bootstrap
  confidence intervals and the first rank test in the dossier — on both arms, which no earlier
  comparison could support.
- Consequently "raw evidence" in this repository means **unedited derived summaries**, with four
  files excepted. §5 marks every claim that can be checked against them and §6 marks what can
  never be checked at all. The exception matters to §6 in particular: what is permanently
  uncheckable there is uncheckable for the thirty-four files that kept no observations, not for
  the corpus as a whole.

### 1.3 Scale

Every number in the table below is regenerated from the tree by
`.github/scripts/check_artifact_table.py` and checked in CI (job 9). Do not hand-edit it.

<!-- BEGIN ARTIFACT FACTS — generated, do not hand-edit -->
| Fact | Value |
|---|---|
| `data/raw/` JSON files | **39** |
| their total size in bytes | **225 540** |
| of those, carrying a `run_at_utc` | 27 |
| carrying none | 12 |
| `data/MANIFEST.sha256` entries | 39 |
| `probes/*.py` | **18** (plus 2 `.orig` reference copies) |
| `.github/scripts/check_*.py` | 9 |
| `git tag -l` | (none) |
| tracked files | 120 |
<!-- END ARTIFACT FACTS -->

What does not derive mechanically: **eight campaign reports** — the seven in `docs/campaigns/`
plus `docs/campagne7bis.fr.md`, the re-run of the aggregation axis, which reversed three of
campaign 7's findings — and **22 numbered measurements**, M1–M8 and M10–M23. **No M9 was ever
assigned**, and the register says so rather than renumbering. An earlier revision of this line
said twenty-three, which contradicted its own enumeration: 8 + 14 = 22, and `RESULTS.md` §3 says
the same.

### 1.4 State of the tree at assessment

**As first assessed, at `b61eef4`.** Seven commits, no tags, all of them falling between
`2026-09-18 10:03:02` and `11:06:43 +0000` — i.e. **after every measurement run**, the last of
which is stamped `2026-09-18T09:33:35` in `findings_agg_cqlref.json`. (One raw file,
`findings_mongot_provenance.json`, carries `2026-09-18T10:05:00`; it is a docker-image provenance
read, not a measurement.) `git status` then showed eight untracked paths, written by remediation
work in flight during the assessment: `ARTIFACT.md` (this file), `docs/STATISTICS.md`,
`data/derived/inference.json`, `docs/RESEARCH-DESIGN.md`, `docs/THREATS-TO-VALIDITY.md`,
`docs/figures/`, `CONTRIBUTING.md` and `.github/`.

Two consequences were drawn from that, and **both are now discharged**:

1. ~~**Nothing above is published.**~~ All eight paths were committed in `fe615ba` and are at
   `origin/main`. `README.md`'s links to `docs/STATISTICS.md` resolve in a clean clone. The
   prerequisite this section set for §2 has been met.
2. **The independent cross-check stands, and has been re-run.** `data/MANIFEST.sha256` (then at
   `.github/evidence.sha256`), a
   manifest produced by a different session from the one that wrote §4, agreed line by line with
   the digests computed here: 36 of 36 then, and **38 of 38 now** — `sha256sum -c` reports 38 OK,
   0 failures. Two independent runs of `sha256sum` over `data/raw/` produce the same result, which
   remains the only genuinely independent confirmation in this repository that the evidence
   directory is in the state its documents describe.

**As re-verified, at `457568f`.** Seventeen commits, still no tag, the window running from
`2026-09-18 10:03:02` to `17:08:26 +0000`. Those three figures are prose rather than generated, and
deliberately so: a generated block must not contain a fact that generating it changes, and the
commit that writes such a block moves `HEAD`. Everything that *is* stable across its own commit —
evidence count and size, stamp coverage, probe count, script count, tag list, tracked files,
untracked paths — is in the generated table in §1.3. The material changes since `b61eef4`, each of
which invalidated something this document had asserted:

| Landed | What it changed here |
|---|---|
| `fe615ba` — the remediation paths committed | discharged both consequences above; §2.1's "no committed checksum manifest" and §2.2's "no committed workflow" became false |
| CI workflow `verify-evidence.yml` | §2.2's "no CI" became false; there are now **nine** jobs, the last two added the same day |
| `c30372b` — campaign 7bis | `data/raw/` 36 → 38 files, `probes/` 16 → 17, an eighth campaign report, and — materially for §1.2 and §6 — **the first probe that keeps its raw observations** |
| `457568f` — challenge D12 annulled | added `check_probe_citations.py` and its manifest; shifted line numbers inside `probe_aggregation.py`, which this document cites |

The last row is the reason §1.3's counts are now generated rather than typed: this document's own
§5 cites `probe_aggregation.py` by line number, and a six-line docstring inserted elsewhere in the
tree silently moved every one of them.

---

## 2. Badge assessment

| Badge | ACM v1.1 definition | Verdict today |
|---|---|---|
| **Artifacts Available** | "This badge is applied to papers in which associated artifacts have been made permanently available for retrieval." | **NOT CLAIMABLE** — but one day's work away. §2.1 |
| **Artifacts Evaluated — Functional** | "The artifacts associated with the research are found to be documented, consistent, complete, exercisable, and include appropriate evidence of verification and validation." | **NOT CLAIMABLE** as a whole. A **scoped Functional over the offline-derivation subset passes today** and was verified. §2.2 |
| **Artifacts Evaluated — Reusable** | "The artifacts associated with the paper are of a quality that significantly exceeds minimal functionality. That is, they have all the qualities of the Artifacts Evaluated – Functional level, but, in addition, they are very carefully documented and well-structured to the extent that reuse and repurposing are facilitated. In particular, the norms and standards of the research community for artifacts of this type are strictly adhered to." | **NOT CLAIMABLE.** §2.3 |
| **Results Reproduced** | "The main results of the paper have been obtained in a subsequent study by a person or team other than the authors, using, in part, artifacts provided by the author." | **UNREACHABLE — permanently, by construction.** §2.4 |

### 2.1 Artifacts Available — not claimable today

This is the only badge whose absence is purely administrative, and it is the one to fix first.

The badge requires artifacts **permanently available for retrieval**. What exists is a GitHub
repository (commit count and HEAD in §1.3) with **no tag**, **no release** and **no DOI**;
`CITATION.cff` carries no `identifiers`, no `version`, no `commit`. `README.md`'s "Cite this"
block points at a mutable URL that resolves to whatever `HEAD` happens to be.

Two clauses of the original assessment have since been **discharged and are struck here rather
than deleted**: ~~no committed checksum manifest~~ — the manifest was committed in
`fe615ba`, is at `origin/main`, holds one entry per evidence file and is re-verified by CI on every
push; and ~~`grep -rniE 'zenodo|doi|orcid' .` returns nothing outside `docs/article/`~~ — that grep
now matches in `README.md`, `CONTRIBUTING.md`, `METHODOLOGY.md`, `RESULTS.md` and this file, all of
them *discussing* the missing DOI rather than carrying one. **The badge is still not claimable**:
discussing a DOI is not minting one, and §7 is unchanged.

Three consequences, stated without hedging:

1. **A force-push or a deletion ends the artefact.** GitHub is a working copy, not an archive.
2. **A citation cannot be pinned.** "M13 = 44×" cannot be bound to a state of the repository, and
   the prose *does* change substantively: commit `98ce434` rewrote figures and claims across eight
   files including `README.md` and `RESULTS.md`.
3. ~~**"Byte-identical to the run" is unverifiable by a reader.**~~ **Closed.** The manifest is
   published and CI re-verifies it, so a reader can check the evidence directory against a
   committed digest without trusting the author. This was the one consequence of the three that
   committing could close, and committing closed it. The other two need an archival deposit, which
   GitHub cannot provide — see §7.

I record a disagreement with the framing this assessment was commissioned under, which held the
badge to be plainly claimable. It is not. The artefact's *contents* are public and substantially
complete; its *permanence* is zero. Claiming Available on a mutable GitHub URL would be exactly
the kind of unbacked assertion this dossier exists to refuse. §7 gives the steps.

### 2.2 Artifacts Evaluated — Functional: fails on "complete", passes when scoped

The failure is on the ACM *complete* criterion, and the artefact's own register says why.

**Blocking defects (whole-artefact scope):**

- **Withheld evidence archive.** `probes/README.md` gap 8 records that
  `verif-storage-20260917/raw_evidence.tar.gz` — thirteen files, **none byte-identical to anything
  published** — exists outside the repository. It contains two scripts the register itself names as
  unfindable (`probe3_variant_b.py`, gap 1; `control_read.py`, gap 3) and nine evidence files,
  among them `probe4_traced.json`, whose `consistency_levels_observed` records `LOCAL_QUORUM` 70
  **alongside `ONE` 42 and `LOCAL_ONE` 2** over 200 traces — a qualification of M4's published
  "70/70 statements at `LOCAL_QUORUM`". The register states plainly that it "records no decision to
  withhold these files and no reason for it." Stating a gap does not close it.
- **Four raw files have no producing script in the repository**: `control_read_A_run1.json`,
  `control_read_A_run2.json` (gap 3), `findings_hcd_vec_freshness.json` (gap 2) — which carries
  HCD's 44.972 ms freshness figure — and `tier_comparison.json` (gap 4), which carries M12's
  `divergence_pct` caveat. These four are the whole of that class: §4.1 counts separately one file
  produced by no script at all and four whose producer is named only by register inference.
- **Half the system under test cannot be stood up from the artefact.** `env/` ships the MongoDB
  compose file only. There is no compose or Dockerfile for HCD plus the Data API;
  `REPRODUCING.md` §4 declares the Data API container's environment **`[U] not recorded**` and the
  HCD image's registry prefix unrecorded. Every HCD-side measurement is therefore unexercisable.
- **No published entry point.** There is still no `Makefile`: an evaluator's first action — "run
  the artefact" — has no single defined start. ~~and no CI … Checking scripts exist on disk under
  `.github/scripts/` and are untracked; until they are committed and wired to a workflow, this
  defect stands.~~ **That half is discharged.** The scripts were committed in `fe615ba` and wired
  to `.github/workflows/verify-evidence.yml`, which now runs nine jobs on every push (§1.3 counts
  them). What an evaluator can do without a `Makefile` is run any one of them directly; what they
  still cannot do is run "the artefact", because half the system under test is absent — the
  blocking defect above, which no amount of CI touches.
- **8 of 17 probes will not answer `--help`**: `agg_cql_arm.py`, `hcd_cql_arm.py`,
  `method2_trace.py`, `mongot_floor.py`, `mongot_freshness.py`, `rmw_postflush.py`,
  `turn_latency.py`, `vector_freshness_rf3.py`. That list was verified by running `--help` against
  each of the seventeen, not inferred. Seven of the eight refuse because they import a driver at
  **module scope** — and the driver is not always the one an earlier revision of this line named:
  `agg_cql_arm.py` imports `cassandra`, not `astrapy` or `pymongo`. The eighth, `turn_latency.py`,
  imports both drivers *inside* its functions and refuses for an unrelated reason: it has **no
  argument parser at all**, reading `sys.argv[1]` directly, so `--help` is taken for an engine
  name. The other **nine** answer offline, and **all 17 byte-compile** with no dependency installed
  (`python3 -m py_compile probes/*.py`), which is what makes the scoped claim below possible.

**What passes today, and it is more than most Functional-badged artefacts carry.** Four checks were
run for this document with no network and no engine. When first written, the fourth had to be run
against a working tree newer than `HEAD`, because two of the files it reads were not yet committed;
**that caveat is gone** — every file all four checks read is committed, and all four now run in CI
on every push:

| Check | Result |
|---|---|
| Every file under `data/raw/` parses as JSON | **38/38 pass**, plus 208 latency-distribution invariants (`min ≤ p50 ≤ p95 ≤ p99 ≤ max`, `n ≥ 1`) — CI job 3 |
| `probe_comparative.py --compare cmp_mongo cmp_hcd cmp_hcdcql` reproduces `comparison_v2.json` | **byte-exact apart from `run_at_utc`** |
| `probe_comparative.py --compare cmp_mongo cmp_hcd` reproduces `comparison.json` | **byte-exact apart from `run_at_utc` *and* a top-level `VERDICT` object the recomputation does not emit** — see §8.1 |
| Figure traceability: every number with ≥ 3 decimals in the seven English Markdown documents is reachable in the committed evidence — `.github/scripts/check_figure_traceability.py`, published and run as CI check 7 | **404 occurrences, 120 distinct values, 0 orphans** — under a rule that had to be **weakened twice** before it held, and the weakenings are the finding. (i) *Reachable* means in `data/raw/*.json` **or** in `data/derived/inference.json`; eight occurrences reach only the second exactly, and six distinct values only after rounding there — the `README.md` ratio-interval endpoints `0.465`, `65.842`, `0.155`, `36.683`, plus `0.966` and `1.421`, the interval of challenge D12. All six are **computed and were never measured** and must not be quoted as observations. (ii) A value may match *after rounding to the precision the document prints*: nine distinct values do, three of them against `data/raw/` (`0.0774` ← `0.077422`, `0.1112` ← `0.111247` in `findings_fieldbyte.json`; `0.996` ← `0.9959` in `comparison_v2.json`) and six against the derived layer. Rounding widens the target a published figure is allowed to hit, and the script names every such match individually rather than folding it into the total. **Under the exact-`data/raw/`-only rule this row once stated**, the current tree yields **10 orphans, not 0**. The document list covers `data/README.md` and **excludes `ARTIFACT.md`**, so this audit cannot launder its own quotations into the count. The three counts in this cell drift whenever a document acquires a figure; they are re-derived by CI job 7 on every push, which is the only reason they are quotable here at all |

**A scoped claim is therefore defensible and should be made explicitly:** *Functional over the
offline-derivation subset* — the raw evidence, the merge/comparison code path, and the
figure-to-source traceability. That scope is honest, checkable, and passes. The unscoped badge
does not.

### 2.3 Artifacts Evaluated — Reusable: not claimable

Reusable presupposes Functional, so §2.2 blocks it outright. Beyond that:

- **Environment capture is insufficient to re-create the environment.** The pymongo version is
  nowhere (`env/requirements.txt` declines to pin it, correctly, because no file records it — the
  omission is honest and still disqualifying). No JDK vendor or version for HCD, only a heap size.
  No `docker version`. No mongod `buildInfo`. No `pip freeze`. No hash-pinned lockfile.
- **Container names are hard-coded into instruments.** `DC1 = ['p16-hcd-node1', …]` in
  `method2_trace.py` and `rmw_postflush.py`; `docker exec p16-hcd-node1` in
  `disk_regime_driver.py`. A re-user must edit the code.
- **Licence incoherence.** `README.md` asserts Apache-2.0 over all of `probes/`, but
  `verify_storage_claims.py` and `verify_storage_claims_rf3.py` carry their own upstream grant
  ("Licence: do what you like with it. Attribution appreciated, not required.") — the relicensing
  of supplied code is asserted, never explained. **No probe file carries an SPDX identifier or
  copyright header** (`grep -ril spdx probes/` returns nothing), so any single `.py` extracted
  from the artefact travels unlicensed. `CITATION.cff` declares `license: CC-BY-4.0` for the whole
  deposit although half of it is Apache-2.0. `LICENSE-docs` scopes CC BY 4.0 to "`docs/`, `data/`,
  and the Markdown files at the repository root", which leaves **`env/` outside both licences**.
- **No machine-readable measurement register.** M1–M23 exists only as prose across five documents,
  and has already drifted: `grep -c 'M2[0-3]' docs/adr/ADR-001-modelling-policy.md` = **0**.

### 2.4 Results Reproduced: unreachable, permanently

This badge is not merely unearned. **It cannot be earned by this artefact, and the artefact is
right to say so.** `REPRODUCING.md` opens: *"You will not reproduce our numbers, and you are not
supposed to."* That is correct — but the bar has to be stated at its real height first.

**The ACM bar is weaker than it is often paraphrased to be.** v1.1 asks only that the main results
be obtained in a subsequent study by other people **"using, in part, artifacts provided by the
author"**. *In part*: the reproducer is entitled to supply the rest of the environment themselves.
So the defect that blocks Functional — that `env/` ships no compose file or Dockerfile for HCD plus
the Data API, leaving half the system under test un-standable from the repository (§2.2) — is **not
by itself an obstacle to this badge**. A third party may stand up their own HCD, take only the
probes, and still qualify. Anything in this dossier that reads as "the badge fails because the
artefacts are incomplete" is arguing against the wrong bar.

The obstacles are of a different kind. They lie in the **results**, not in the artefacts supplied,
which is why supplying more artefacts cannot remove them:

1. **The system under test mutated across its own campaigns.** `system.paxos` grew from 0 to
   roughly 13 GiB per dc1 node between campaigns and could not be purged; the 20
   `supply_chain_hcd` SAI indexes were dropped and recreated six times; campaign 1 ran at RF 1 on
   one node and campaigns 2–7 at `{dc1:3}` on six nodes over two datacentres. There is no single
   "the system" whose results could be reproduced.
2. **The host was never idle.** One shared QEMU virtual machine (`alphadebunker`) carrying
   unrelated production-demo workloads at load average 14–16 throughout. Absolute latencies are a
   noisy ceiling, not a measurement.
3. **The page cache was never dropped.** The campaign had no root, so every run described as
   disk-bound is qualified as *dataset on disk, reads still possibly served from RAM below the
   database* (`disk_state.json → evidence.page_cache_note`).
4. **The search-freshness half used a different MongoDB from the mutation half** — a single-node
   `atlas-local` container on which `w:majority` is trivially satisfied (audit finding I8).
5. **No per-observation data survives for thirty-four of the thirty-eight evidence files** (§1.2) —
   an earlier revision said none survived, which campaign 7bis made false — so for those, even a
   bit-perfect re-run could not be compared
   to the original by any statistical test. There is nothing to test against.

Reasons 1–4 say that the published magnitudes are properties of one unrepeatable
host-and-configuration history rather than of HCD or of MongoDB; reason 5 says that no subsequent
study could be compared against the original even if that history could be rebuilt. Both hold
whether the reproducer uses all of the author's artifacts or, as ACM permits, only part of them,
and both would still hold if `env/` shipped a complete HCD stack tomorrow. That is what
*permanently, by construction* means here, and it is the only ground on which the verdict stands.

The honest replacement for this badge is a **qualitative reproduction criterion** — what a
re-runner should be able to observe, with no magnitude in it. §5 supplies one.

---

## 3. Environment contract

### 3.1 What is pinned, and by what evidence

| Component | Identity | Pinned by | Source in this repository |
|---|---|---|---|
| **Host** | QEMU VM `alphadebunker`, Intel Xeon Gold 6148 @ 2.40 GHz, 80 vCPU, 220 GiB RAM | value | `data/raw/cmp_mongo.json → conditions.host` |
| **OS** | Linux 6.8.0-136-generic, glibc 2.39 | value | `data/raw/cmp_mongo.json → conditions.host.platform` |
| **Python** | 3.12.3 | value | `data/raw/cmp_mongo.json → conditions.python` |
| **astrapy** | `astrapy==2.3.1` | exact version | `env/requirements.txt` |
| **cassandra-driver** | `cassandra-driver==3.30.1` | exact version | `env/requirements.txt` |
| **pymongo** | — | **UNPINNED** | `env/requirements.txt` declares the omission deliberate: no file records the version. See §3.2 defect D-ENV-1. |
| **MongoDB (mutation, read, search, aggregation)** | `mongo:8.0.32`, 3-member replica set `rs0`, each `--memory 8g --cpus 4`, network `cmpnet` | **tag only** | `env/docker-compose.mongodb-rs.yml`; `cmp_mongo.json → conditions.TO_BE_COMPLETED_BY_HAND`. See D-ENV-2. |
| **MongoDB / mongot (search freshness only)** | `mongodb/mongodb-atlas-local`, **digest `sha256:e118f5c131c5004e4ccd0554d3f32b048b4af6a33325e80e424eaa1c8986d8f1`**; mongod **8.3.11**; mongot **1.75.1, `localDev` edition**; base `registry.access.redhat.com/ubi9-minimal`; image created `2026-09-17T09:15:42Z`; `vcs_ref 28eadd3b1a5a834acaab9dbfe06d7a5df73b64ee` | **digest — the only digest-pinned image in the artefact** | `data/raw/findings_mongot_provenance.json` |
| **HCD** | `cp.icr.io/cp/cpd/ibm-datastax-hcd/hcd:2.0.6-ubi`; running release `5.0.7.0-ea50e91ba01f` (`nodetool version`, `system.local`) | **fully qualified** | `data/raw/findings.json` (`conditions.TO_BE_COMPLETED_BY_HAND.product_and_version`) records the full reference; `REPRODUCING.md` §4 and `docs/campaigns/01-verification.fr.md` print the short tag. See D-ENV-3. |
| **Data API** | `stargateio/data-api:v1.0.33`, 2 GiB memory limit, no CPU limit, co-located with the nodes | **tag only**; **container environment `[U] not recorded**` | `REPRODUCING.md` §4. See D-ENV-4. |
| **Durability, HCD** | `commitlog_sync periodic`, 10 000 ms, `trickle_fsync true`; writes at `LOCAL_QUORUM` + `LOCAL_SERIAL` | value | `docs/campaigns/01-verification.fr.md` |
| **Durability, MongoDB** | `WriteConcern(w="majority", j=True)`, set per collection in probe code, **not** in the compose file | value | seven probes construct it: `probe_comparative.py`, `probe_aggregation.py`, `probe_agg_7bis.py`, `probe_read_search.py`, `mongot_floor.py`, `mongot_freshness.py`, `turn_latency.py` |
| **Ports** | Data API 8181 (campaign 1), 8182 (campaigns 3–4); `atlas-local` published on 27020; CQL 9042 default, `agg_cql_arm.py` defaults 9142 | value | `REPRODUCING.md` §2, `findings.json`, `findings_tier.json` |
| **JDK / heap** | heap only. `findings.json:conditions` records `heap 2 GiB (Xmx)` for campaign 1 and **nothing for the later campaigns**; the 4 GiB figure quoted in an earlier revision of this row is not in that file and its source was not identified on re-verification, so it is withdrawn here rather than carried. **Vendor and version not recorded.** | **absent** | `findings.json:conditions`. See D-ENV-1. |
| **Docker engine** | **not recorded** | **absent** | — |
| **mongod `buildInfo`** | **not recorded** | **absent** | — |

### 3.2 Environment defects

- **D-ENV-1 — four components have no recorded identity.** pymongo, the JDK, the Docker engine
  version and mongod `buildInfo` — the sentence enumerates four, and an earlier revision counted
  them as three. The repository is honest about pymongo and silent about the other three. *Remedy: `env/environment.md` listing each fact with its source and `[U] not
  recorded` where it is absent — do not guess — plus a `probes/collect_env.py` that a re-runner
  executes first and commits beside their results.*
- **D-ENV-2 — `mongo:8.0.32` is a drifting tag.** A tag is a mutable pointer. Two evaluators
  pulling it on different days can get different images. *Remedy: record the RepoDigest at next
  pull and pin `mongo@sha256:…` in the compose file. The campaign record does not contain it, so
  it cannot be recovered retroactively — mark it `[U]` rather than inventing one.*
- **D-ENV-3 — the HCD image's registry prefix is recorded in the evidence and dropped everywhere
  a reader looks.** An earlier revision of this entry said the prefix was *not recorded*. It is:
  `data/raw/findings.json` carries
  `cp.icr.io/cp/cpd/ibm-datastax-hcd/hcd:2.0.6-ubi` in full. What the reader-facing documents print
  is the bare `hcd:2.0.6-ubi`, which is not a resolvable reference. The defect is therefore a
  transcription loss, not a measurement gap, and it is cheaper to fix than the original entry
  implied: *remedy — print the fully qualified reference in `REPRODUCING.md` §4 and in the pinning
  table above, both of which now do.* The image is behind IBM entitlement either way, so a reader
  without a licence still cannot obtain it; that part of the original entry stands.
- **D-ENV-4 — `REPRODUCING.md` §3.4 instructs an unpinned pull.**
  `docker run -d --name atlas-local -p 27020:27017 mongodb/mongodb-atlas-local` resolves to
  `:latest`, which will **not** be the 8.3.11 / mongot 1.75.1 `localDev` build that produced the
  entire search-freshness campaign — the one axis HCD wins. **The digest is already recorded in
  `data/raw/findings_mongot_provenance.json` and is simply not used where it matters.** *Remedy,
  one line:*

  ```bash
  docker run -d --name atlas-local -p 27020:27017 \
    mongodb/mongodb-atlas-local@sha256:e118f5c131c5004e4ccd0554d3f32b048b4af6a33325e80e424eaa1c8986d8f1
  ```

  This is the single cheapest correctness fix in the artefact.
- **D-ENV-5 — the `localDev` reserve is an environment fact, not a footnote.** mongot 1.75.1
  `localDev` is the edition MongoDB ships for local development, not the search tier that serves
  Atlas. Every M17/M18/M19 magnitude is a property of *that* build on a single-node replica set on
  a loaded shared host, and **may not be quoted as MongoDB Atlas Search lag or as a property of
  MongoDB the product**. The commit/refresh interval is internal to the jar and was never read.
  `findings_mongot_provenance.json` states this correctly and states that it *raises* the reserve
  rather than lowering it. The direction survives — mongot indexes asynchronously off the change
  stream by construction — the magnitude does not.

### 3.3 The reconstruction gap

`env/docker-compose.mongodb-rs.yml` is labelled a **reconstruction** in its own header, which is
the right practice: it distinguishes what the evidence fixes (image tag, member count, member
names, resource limits, network name) from what the file chose (the port mapping). **No equivalent
exists for HCD plus the Data API.** Until `env/docker-compose.hcd-dataapi.yml` is shipped — with
every unrecorded value marked `[U]` and the variable spellings taken from the Data API's own
`CONFIGURATION.md` rather than guessed — no evaluator can exercise the HCD half, and no badge
beyond the scoped Functional of §2.2 is reachable.

---

## 4. Evidence manifest

Generated by running `sha256sum` over `data/raw/`, not by hand. Any later alteration of any
evidence file changes its digest and is detectable against this table.

**Regenerate and verify:**

```bash
cd /path/to/shredding-cost-hcd-mongodb
sha256sum data/raw/*.json > data/MANIFEST.sha256   # mint, from the repository root
sha256sum -c data/MANIFEST.sha256                  # verify, also from the root
```

File count and total size are in the generated table in §1.3, not typed here — the figure that was
typed here went stale within hours. (A ~280 KB figure sometimes quoted is `du`'s on-disk block
allocation, not the byte count.)

<!-- BEGIN EVIDENCE MANIFEST — generated, do not hand-edit -->
| File | Bytes | SHA-256 | `run_at_utc` | Producer |
|---|---:|---|---|---|
| `cmp_hcd.json` | 6180 | `3f65187df1f77830e763bef589953d3ce1d45d1b9d362601228afaacebfe12fc` | `2026-09-18T06:14:06.821001+00:00` | `probe_comparative.py` |
| `cmp_hcdcql.json` | 5417 | `af69cc2157458c5fd289c167aeec03d1806306cc425fa0d7cc52e19c81533638` | — *not stamped* | `hcd_cql_arm.py` |
| `cmp_mongo.json` | 10863 | `f9881df2b3658a22f7b2e084d59ee332259da37c2771cf35d5bc4492d4ef38ff` | `2026-09-18T06:13:39.479032+00:00` | `probe_comparative.py` |
| `comparison.json` | 3122 | `293711d254cef8da99da361d6808cf1b88b2c452f85770d78443c54df9eba722` | `2026-09-18T06:14:12.531755+00:00` | `probe_comparative.py` (merge) **+ a hand-added `VERDICT` block — see §8.1** |
| `comparison_v2.json` | 2626 | `08ba8fb29a794bbcc79148d7f05c603457048ccfdda40fa195e121becddc57ff` | `2026-09-18T06:31:40.491106+00:00` | `probe_comparative.py` (merge) |
| `control_read_A_run1.json` | 1835 | `17656ed7580083830a6552c8c0356dc31c810a18769c1d8951c941a0061ecc47` | — *not stamped* | **none in repo** (`probes/README.md` gap 3) |
| `control_read_A_run2.json` | 1829 | `499051bafd3acce217af0f3ad9e7150dcae983f315f1c0530eed66a907d2d81e` | — *not stamped* | **none in repo** (`probes/README.md` gap 3) |
| `disk_state.json` | 1710 | `adb23b44a840c6fcb5dbba6bded9072e74e71b70e162e146587c8f0f2602c3d1` | `2026-09-17T21:29:41.731243+00:00` | `disk_regime_driver.py` |
| `disk_state_c4.json` | 1710 | `d254419eeacd2e605b226c9628462d9e157bedc935c1e1093d225571fab5b904` | `2026-09-17T22:31:02.926107+00:00` | `disk_regime_driver.py` |
| `findings.json` | 32926 | `b1d245c8f0eb5964d63e7f3b967ffee5a498d05e24d4a6513e7758f0f3788677` | `2026-09-17T14:59:03.702466+00:00` | `verify_storage_claims.py` |
| `findings_agg7bis_hcd.json` | 6784 | `5404bfdedb0640134bdfba30b5c6cf6bbdd93a8d647992fa7a1d45144baf63e4` | `2026-09-18T14:01:30.742167+00:00` | `probe_agg_7bis.py` |
| `findings_agg7bis_mongodb.json` | 9934 | `8df19b8e34331aefed866791fad38820cb7e461919168fceb6c626f500cb02dd` | `2026-09-18T13:09:59.643933+00:00` | `probe_agg_7bis.py` |
| `findings_agg_cqlref.json` | 2114 | `ea7d1b8dd04c3b0de56f1d95736295341d5016c38350b3db5e19c5aa46295813` | `2026-09-18T09:33:35.542303+00:00` | `agg_cql_arm.py` |
| `findings_agg_hcd.json` | 3071 | `d13fb3b823d5bdaf7fb8a4985bfe7dbd870efbf5ed955e8c09e3ee3af7dc1fd2` | `2026-09-18T09:29:31.556897+00:00` | `probe_aggregation.py` |
| `findings_agg_mongodb.json` | 3121 | `e640bfc9c8fa5776d8cee559e50343a7b35d4256ec4bb930df57910bb47200de` | `2026-09-18T09:09:39.086556+00:00` | `probe_aggregation.py` |
| `findings_cql_groupby_expressibility.json` | 4804 | `e78f2cf28e054f6b32d615052fe40f34e50793b96ebb9508fea89bd104bcccf9` | `2026-09-18T20:27:53.919795+00:00` | `cql_groupby_expressibility.py` |
| `findings_disk_rf3.json` | 4280 | `55609dc8aeb71a25f924911eceefa3dfecaa873eb4215107d6c6d2c8d476e87e` | `2026-09-17T21:33:23.725151+00:00` | `verify_storage_claims.py` + `probe3_variant_b.py` (**gap 1, unpublished**) |
| `findings_fieldbyte.json` | 17769 | `c85e78495270132c749475346d486c69987016c5f15597aac56b631d9058290e` | `2026-09-17T21:36:25.094922+00:00` | `probe_field_vs_byte.py` |
| `findings_hcd_vec_freshness.json` | 511 | `100e6531006fae14c14e48938a346aec8d5570a06c27b11e6e17e408354a64d4` | — *not stamped* | **none in repo** (`probes/README.md` gap 2) |
| `findings_mongot_floor.json` | 686 | `b4d6eb235d377c75cadbef7954316c3c5e5f60ae5a5640507f3ab6dbe716b940` | `2026-09-18T08:05:09.148201+00:00` | `mongot_floor.py` |
| `findings_mongot_freshness.json` | 1190 | `279dc7a7a2a34c0b450cd698a0426ff09859e39d7fbdb0a86d8f03a1358150a7` | `2026-09-18T07:45:19.338661+00:00` | `mongot_freshness.py` |
| `findings_mongot_provenance.json` | 3280 | `3c70da5adaa231585974cb8c8c3360319733235ad47ab9fee15881c315be6ae4` | `2026-09-18T10:05:00+00:00` | none — docker image label + on-image file read |
| `findings_rf3.json` | 10028 | `891df4c8121cdd2c056a7f3b3f232360768014fe3d41d6e61cdf11a01d208e50` | `2026-09-17T16:21:37.277964+00:00` | `verify_storage_claims.py` *(self-declared; the register names `verify_storage_claims_rf3.py` — see §8.3)* |
| `findings_rf3_rate50.json` | 9612 | `e686dadda102a1f84a40128a1fc9327aed39608fda9a6c40570f2178b1ccd1d7` | `2026-09-17T16:21:37.277964+00:00` | `verify_storage_claims.py` *(as above)* |
| `findings_rf3_rate50_rep2.json` | 9617 | `4d9dc780f688eeb2073d9d764e9a2f7d95f49470d35311a7b0bf8713e4dd723c` | `2026-09-17T16:26:59.779266+00:00` | `verify_storage_claims.py` *(as above)* |
| `findings_rs_hcd.json` | 1698 | `1341ba0fd8d8e92c040163bd7c9ab6a94ff8043681c641cce4b7899c60054e3c` | `2026-09-18T07:35:40.370231+00:00` | `probe_read_search.py` |
| `findings_rs_mongo.json` | 2557 | `5bd795ecec7398c822cc49c76091dc36f8fbaece2f4dfa6c82441f315d89ad08` | `2026-09-18T07:17:06.155963+00:00` | `probe_read_search.py` |
| `findings_tier.json` | 15126 | `1412549cf0d256c1953473cc61258c668e356ebbf6a92cb169ee50e86a7200f7` | `2026-09-17T22:34:06.905113+00:00` | `probe_tier_vs_storage.py` |
| `findings_tier_method2.json` | 1621 | `3526a54cdb0625dc53b67a4f823d5e11700ffdda7ead23cc0cebe265543afe0d` | — *not stamped* | `method2_trace.py` |
| `findings_turn_hcd.json` | 1111 | `6e77f16140f9f82de8f485945fcc0430b177cab043cac6bdc458b160298e755a` | — *not stamped* | `turn_latency.py` |
| `findings_turn_mongodb.json` | 1126 | `210b83fc92ed3ba23c2cf9c6e2865d999f9e62525604416629c155675b7678bc` | — *not stamped* | `turn_latency.py` |
| `findings_vector_rf3.json` | 3621 | `15deefc117d93227cae1932252bd30a5dcf0718211443429e072a8815e44f69d` | `2026-09-17T16:5x (p16 ring)` | `vector_freshness_rf3.py` *(by register, not by file)* |
| `probe4_rf3_supplementary.json` | 11906 | `0b9a90028278355e4857367b68dce7356d4625586749aff40cb48b1ade4fa48e` | — *not stamped* | `verify_storage_claims_rf3.py` run *(not named in the file)* |
| `rmw_postflush.json` | 1269 | `d063f432b4f2911df91f0e21491308f7fe1af8367b968f338fb8e0be47b27c73` | — *not stamped* | `rmw_postflush.py` |
| `smoke_hcd.json` | 3703 | `1552c1fa8a4c2df3a82b6d15c5bf0f1a023fa81c91b6d8420fa713bac41c6cab` | `2026-09-18T06:13:22.002920+00:00` | `probe_comparative.py` |
| `smoke_mongo.json` | 5938 | `304f06f13443d8843389eff7043c01aa5ab41876e41bfe00f702e32b3221a529` | `2026-09-18T06:12:46.794036+00:00` | `probe_comparative.py` |
| `tier_comparison.json` | 1031 | `6ff56c6193574aeb483d18b4108a03cc84a0b06225f7c020163b64b4cef88ed1` | — *not stamped* | **none in repo** (`probes/README.md` gap 4) |
| `vector_freshness_idle.json` | 9909 | `53e89397ea3b99506ae1190d485fde80cd54373c54f3ab34ecec53769f9655a1` | — *not stamped* | `vector_freshness_rf3.py` *(by register, not by file)* |
| `vector_freshness_loaded.json` | 9905 | `23a0b40bc3a30d9e5713b8003b962961c922989b54955865b25387107d3d98d6` | — *not stamped* | `vector_freshness_rf3.py` *(by register, not by file)* |
<!-- END EVIDENCE MANIFEST -->

### 4.1 What the manifest exposes

Counting from the table, not from prose:

- **12 of 38 files carry no `run_at_utc`**, and none of them carries any alternative run
  timestamp under another key (verified by a recursive key scan). Two of them —
  `rmw_postflush.json` (M15, the measurement that demoted the dossier's own flagship coefficient)
  and the two `findings_turn_*.json` (M19, which bounds HCD's only decisive win) — are **headline
  evidence with the thinnest record in the corpus**. Record provenance runs *inverse* to
  decisiveness here, which is the opposite of the direction `probes/README.md` tabulates for
  instrument provenance.
- **1 further file carries a hand-typed, incomplete stamp**: `findings_vector_rf3.json`,
  `"2026-09-17T16:5x (p16 ring)"`.
- **25 of 38 carry a machine-written stamp.** The twelve unstamped files are unchanged since the first assessment; the two files campaign 7bis added both carry machine-written stamps.
- **Both front-matter claims have since been corrected.** `README.md` line 106 and
  `DISCLAIMER.md` line 18 each named `run_at_utc` as universal; each now names a count — 26 of 38,
  one of those hand-typed — and points at `data/README.md`, which lists all twelve exceptions.
  `DISCLAIMER.md` additionally records what the correction exposes: for the twelve unstamped files
  the date rests on the campaign reports rather than on the evidence. See §8.2.
- **4 raw files have no producing script in the repository** (`probes/README.md` gaps 2–4):
  `control_read_A_run1.json`, `control_read_A_run2.json`, `findings_hcd_vec_freshness.json`,
  `tier_comparison.json`. **1 further file was produced by no script at all**:
  `findings_mongot_provenance.json`, which records a docker image label plus an on-image file read.
  **4 more name their producer only by register inference**: `findings_vector_rf3.json`,
  `vector_freshness_idle.json` and `vector_freshness_loaded.json` (`vector_freshness_rf3.py`, by
  register, not by file), and `probe4_rf3_supplementary.json` (`verify_storage_claims_rf3.py`, not
  named in the file). Both of those scripts are present in `probes/`, so what these four lack is
  the self-declaration, not the instrument — which is why they are counted apart from the 4 above
  and not added to them.

---

## 5. Claims and how to check them

Every command below was executed against the committed tree for this document, offline, with no
engine running and no driver installed. Each is a **qualitative** criterion: **no magnitude is part
of any pass condition**, because §2.4 establishes that magnitudes cannot be reproduced.

Prerequisite: `cd` to the repository root. Nothing here requires a network.

| # | Claim | Command | Passes when |
|---|---|---|---|
| **V0** | The evidence is unaltered since this document was written | `sha256sum -c data/MANIFEST.sha256`, **run from the repository root** — the manifest's paths are root-relative, so from inside `data/` every line reports "No such file or directory", which looks like corruption and is not | 38 lines, every one `OK`. Until 18 September 2026 this row named a file that did not exist; the manifest has been moved to that path |
| **V1** | All evidence is well-formed | `python3 -c "import json,glob;[json.load(open(f)) for f in glob.glob('data/raw/*.json')];print(len(glob.glob('data/raw/*.json')))"` | prints `38`, no exception |
| **V2** | The published three-arm merge is the published code's output | `python3 probes/probe_comparative.py --compare data/raw/cmp_mongo.json data/raw/cmp_hcd.json data/raw/cmp_hcdcql.json --out /tmp/v2.json` then diff against `data/raw/comparison_v2.json` | identical apart from `run_at_utc` |
| **V3** | `comparison.json` carries content no probe emits | same, with `cmp_mongo.json cmp_hcd.json` only | identical apart from `run_at_utc` **and** the top-level `VERDICT` key, which the recomputation does not produce — §8.1 |
| **V4** | **M1** — the shredded row is 12 physical columns with 9 automatic SAI on a collection that declared nothing | `python3 -c "import json;e=json.load(open('data/raw/findings.json'))['findings'][0]['evidence'];print(e['column_count'],e['index_count'])"` | prints `12 9` |
| **V5** | **M2** — a single-field `$set` compiles to `SELECT` + a Paxos-guarded `UPDATE` with 11 assignments, in 10 of 10 traces | `python3 -c "import json;t=json.load(open('data/raw/findings.json'))['findings'][2]['direct_observation_by_query_trace'];u=t['sequence_per_updateOne'][1];print(u.split('SET ',1)[1].split(' WHERE ',1)[0].count(',')+1, [c for c in t['counts'] if c['statement']=='UPDATE'][0]['count'], 'IF tx_id = ?' in u)"` | prints `11 10 True` |
| **V6** | **M11** — the pre-registered field-count rule **straddles its own threshold across two passes** and returns no clean verdict | `python3 -c "import json,re;print(re.search(r'\"verdict_per_pass\": \[[^]]*\]',json.dumps(json.load(open('data/raw/findings_fieldbyte.json')))).group())"` | prints `["BYTES DOMINATE", "INCONCLUSIVE"]` |
| **V7** | **M15** — the flagship per-byte coefficient is a *regime* property spanning ×7.50 / ×5.94 / ×1.52 on the same system | `python3 -c "import json;d=json.load(open('data/raw/rmw_postflush.json'));print(d['p50_growth_factor'],d['comparison'])"` | prints `1.52` and the three-way comparison object |
| **V8** | **M19** — MongoDB's search miss rate falls to 0/30 at τ ≥ 1000 ms; HCD is 0/30 at every τ | `python3 -c "import json;[print(e,{k:v['miss'] for k,v in json.load(open(f'data/raw/findings_turn_{e}.json'))['miss_rate_by_tau_ms'].items()}) for e in ('hcd','mongodb')]"` | HCD all zeros; MongoDB `30,28,25,15,10,0,0,0,0` |
| **V9** | **M21/M22** — HCD's Data API refuses exact count above 1000 documents, and `estimatedDocumentCount()` returns **0** against a true 200 000 | `python3 -c "import json;c=json.load(open('data/raw/findings_agg_hcd.json'))['result']['counts'];print(c['count_all_error'][:40],c['estimated'],c['count_all_correct'])"` | prints the `TooManyDocumentsToCountException`, `0`, `False` |
| **V10** | **M20's evidence is a string literal, not a captured response** | `grep -n 'structural' probes/probe_aggregation.py` then `grep -rn 'aggregate(' probes/*.py` | the `structural` field at line 196 is a fixed string emitted unconditionally, and every `aggregate(` call in `probes/` targets **MongoDB**: the pymongo `$group` at `probe_aggregation.py:109`, the same in `probe_agg_7bis.py`'s `run_mongo`, and the `$search` pipelines in `mongot_floor.py`, `mongot_freshness.py` and `turn_latency.py`. An earlier revision of this cell said *the only* call, which stopped being true when campaign 7bis landed; the conclusion is untouched — **no probe ever issues `aggregate`, `$group` or `distinct` against HCD**, which is what V10 exists to establish. §8.4 |
| **V11** | Every cross-engine slope, r² and ratio is fitted on **pass 1 only** | `grep -n 'pass1' probes/probe_comparative.py` | line 255 hard-codes `k = f"{sz.label}\|pass1"`; pass-2 points sit unused in `cmp_mongo.json` / `cmp_hcd.json` / `cmp_hcdcql.json` — §8.5 |
| **V12** | Figure traceability: every figure in the seven documents is reachable in `data/raw/` or `data/derived/inference.json`, and every rounded or derived-only match is named in the output | `python .github/scripts/check_figure_traceability.py` — published, runnable offline, and CI check 7. Its document list is fixed in the file and excludes `ARTIFACT.md` | `404 occurrences, 120 distinct values, 0 orphan values`; **9 of the 120 match only after rounding, and 6 of those 9 only in `data/derived/inference.json`** — §2.2. Under the exact-`data/raw/`-only rule this row once asserted, the same tree gives 10 orphans. These three counts move whenever a document acquires a figure, so read them from the script's output rather than from this cell; CI job 7 re-derives them on every push |
| **V13** | The declared harness patches touch no size, threshold, repetition count or verdict rule | `diff probes/verify_storage_claims.py.orig probes/verify_storage_claims.py` | only the two declared mechanical fixes. **This check is meaningful only for this one probe**: `probe_tier_vs_storage.py.orig` was reconstructed by reverting the patch it is used to show (mtime 10:03 > 09:35), and no `.orig` exists for `verify_storage_claims_rf3.py` or `disk_regime_driver.py` |
| **V14** | The mongot reserve is on the record | `python3 -c "import json;print(json.load(open('data/raw/findings_mongot_provenance.json'))['versions'])"` | `mongot_version 1.75.1`, `mongot_edition localDev`, `mongod_version 8.3.11` |

### 5.1 What counts as a reproduction

If the HCD half is ever stood up again (§3.3), these are the criteria — **all qualitative, all
free of magnitude**:

| Claim | Reproduced if |
|---|---|
| **M1** | a collection created with no declared index yields a table of generic physical columns with automatic SAI on them |
| **M2** | every traced single-field `updateOne` is a `SELECT` followed by one conditional `UPDATE` rewriting the derived columns and `doc_json`, guarded by `IF tx_id = ?` |
| **M11** | the byte series' endpoint ratio exceeds the field-count series' by a wide margin, and the field-count series stays far below the 1.5 that would make field count an independent driver |
| **M13/M14** | the per-KiB mutation rate of HCD exceeds MongoDB's by more than an order of magnitude in a memtable-resident regime, **and** the ratio is reported as an envelope, not a point |
| **M15** | the same coefficient falls materially when the RMW `SELECT` is forced onto the SSTable path |
| **M20/M21/M22** | `aggregate` / `$group` / `distinct` return `COMMAND_UNKNOWN`; `countDocuments` fails above 1000; `estimatedDocumentCount()` returns 0 on an unflushed collection |
| **M17/M18/M19** | write-to-searchable lag on the measured mongot build is a *refresh interval* (bounded floor, bounded ceiling), not a fixed delay; HCD's index sits on the write path |

**No magnitude is part of any criterion.** A re-runner reporting different numbers has not failed
to reproduce; a re-runner reporting a different *mechanism* has contradicted the dossier, which is
the outcome it was built for.

---

## 6. What can never be checked

Recorded here so that no future badge claim overreaches it.

1. **No confidence interval, significance test, bootstrap, rank test, autocorrelation check,
   stationarity check, distributional-overlap measure or alternative percentile estimator is ever
   recoverable** for any latency figure produced by the sixteen probes that discard their samples,
   with four files excepted — the two
   vector-freshness files identified in §1.2. The per-observation samples were discarded at write
   time by the probes' shared summarising helper. At n = 30 a distribution-free 95.7 % median interval requires x₍₁₀₎ and
   x₍₂₁₎; neither is stored. This is permanent.
2. **The published p95 and p99 are not percentile estimates.** Every probe uses linear
   interpolation at k = (n−1)p. At n = 30 that places p99 at k = 28.71 — a blend of the two
   largest observations — and p95 at k = 27.55. `README.md`, `RESULTS.md` and `data/README.md`
   carry this caveat only for the single n = 3 aggregation arm; it applies to the whole corpus.
3. **`stdev_ms` is the population standard deviation about a mean the dossier declines to
   publish.** `data/README.md` calls it "sample standard deviation" and `METHODOLOGY.md` calls it
   population; the implementation is `statistics.pstdev` in **all thirteen probes that emit a
   distribution** (`grep -c pstdev probes/*.py`). The two documents contradict each other and
   `METHODOLOGY.md` is the correct one.
4. **Pre-registration is testimonial.** `METHODOLOGY.md` asserts the protocol was fixed before the
   numbers. The git history is entirely after the last measurement run stamp (§1.4), and **fourteen of the
   seventeen probe files carry the same mtime to the second — `2026-09-18 09:35:57`** — a single
   post-hoc import, so file times carry no ordering information either. The three exceptions carry
   later times (`probe_agg_7bis.py`, and `agg_cql_arm.py` and `probe_aggregation.py` from the
   docstring edits of 18 September) and add nothing: a file touched *after* the measurements cannot
   evidence a protocol fixed *before* them. When first written this line said all sixteen; the
   count moved and the argument did not. The repository itself accepts mtime
   as evidence when it uses it to discredit `probe_tier_vs_storage.py.orig`; the same instrument
   applied to this claim returns nothing. **Six** raw files echo a pre-registered *rule* back from the code at run time — `findings.json`
   (`rule`, `read_control_pre_registered_rule`), `findings_fieldbyte.json` (`verdict_rule`),
   `findings_disk_rf3.json` (`verdict_by_control_rule`), `findings_rf3.json`
   (`verdict_by_harness_rule`, `verdict_latency_by_control_rule`) and both campaign-7bis files
   (`verdict_rules_preregistered`) — and twelve carry a verdict key of some kind. An earlier
   revision of this line said *only two*, which understated the repository's own position; the
   correction runs against this document's pessimism and is recorded for that reason. What does not
   change is that a rule written into the output at run time evidences the rule, not the moment it
   was fixed.
5. **"Each probe carried its decision rule in its own source before it ran" is false as a
   generalisation.** Counting by `grep -ciE "verdict|threshold|SUPPORTED|INCONCLUSIVE"`, **nine of
   seventeen** probe files now return a non-zero count, but **the grep over-counts by one and the
   over-count is instructive**: `agg_cql_arm.py` matches only because a docstring added on
   18 September quotes an engine error message containing the word *supported*
   (`"Group by is currently only supported on the columns of the PRIMARY KEY"`), and the pattern is
   case-insensitive. That is prose, not a construct. **Eight carry a real one** —
   `verify_storage_claims.py`, `verify_storage_claims_rf3.py`, `probe_field_vs_byte.py`,
   `probe_tier_vs_storage.py`, `disk_regime_driver.py`, `vector_freshness_rf3.py`, and
   `probe_agg_7bis.py`, which carries the strongest in the corpus: a block headed
   *PRE-REGISTERED VERDICT RULES, fixed before execution* and a `verdict_rules_preregistered` key
   written into its output, so the rules that would have refuted the campaign are in the evidence
   file itself. One more, `mongot_floor.py`, carries a classification heuristic that the dossier's
   own meta-challenge D5 already flags as the author's judgement rather than a test. **Eight carry
   none**, and they include every instrument that
   produced a post-campaign-4 headline: `hcd_cql_arm.py` (M14, the 40×/72× tier-stripped
   result), `rmw_postflush.py` (M15, the ×1.52 that demoted the flagship coefficient),
   `probe_read_search.py` (M16, one of the two HCD wins), `mongot_freshness.py` (M17, the other),
   `turn_latency.py` (M19), `method2_trace.py`, `probe_aggregation.py`, `agg_cql_arm.py`,
   `probe_comparative.py`. The pre-registration property and the measurer-written provenance class
   are close to anti-correlated: the weakest-provenance instruments are also the ones with no
   pre-declared rule, so two independent safeguards fail on the same measurements.

   **Two credits are owed here and should not be lost in the criticism.**
   `probe_comparative.py` carries no verdict rule but does carry a genuine pre-registered
   *permission gate* — `cross_engine_comparison_permitted`, which refuses to emit a cross-engine
   ratio unless both records come from the same host with the same series shape and repetition
   counts. And `probe_aggregation.py` carries a pre-declared **correctness** criterion,
   `sums_match()` at `probe_aggregation.py:69`, which checks every arm's result against a deterministic ground truth
   to a stated tolerance — a stronger form of pre-registration than a latency threshold, and the
   reason M23's arms can be described as "exact against ground truth" at all.
6. **No axis was measured under concurrency.** Every probe is a single sequential closed-loop
   client. The article under verification promises "concurrency" in its own title
   (`docs/article/`, the two volets); it is never measured. `README.md` line 1 and the
   `CITATION.cff` title have both been corrected to drop the word, but citations of the earlier
   title are already in circulation and cannot be recalled. `CITATION.cff` also keyworded "write
   amplification", which no file quantifies; that keyword now reads "read-modify-write".

---

## 7. Archival deposit — GitHub is not an archive

### 7.1 Why the current arrangement fails

GitHub is a hosting service with a mutable history. `git push --force` rewrites it; repository
deletion removes it; a renamed account breaks every URL in `CITATION.cff` and in `README.md`'s
"Cite this" block. None of these events leaves a trace a citing reader could detect. The ACM
badge requires artifacts **"permanently available for retrieval"**, and a URL whose owner can
change or delete its target is not that.

The dossier's own standard settles this: it refuses to accept a measurement on the measurer's
testimony, and an unversioned mutable URL asks a citing author to accept the *evidence* on exactly
that basis.

### 7.2 Concrete steps to mint a DOI

Roughly a day's work. **No new measurement is required.**

1. ~~**Commit what is on disk but untracked**~~ — **done** in `fe615ba`. Every path this step
   named is tracked and at `origin/main`, and `README.md`'s links resolve in a clean clone.
2. ~~**Publish the manifest.**~~ — **done, and now signposted**. `data/MANIFEST.sha256` is
   committed, holds one digest per evidence file, and `.github/scripts/check_evidence_manifest.py`
   runs as CI job 1, so a later alteration fails CI at the commit that introduces it. It lived at
   `.github/evidence.sha256` until 18 September 2026, which protected the evidence but hid the
   protection: a reader following `REPRODUCING.md` looks beside the data, not inside a CI
   directory. It was moved with `git mv`, so `git log --follow` carries its history, and
   `REPRODUCING.md` §1 now opens with `sha256sum -c data/MANIFEST.sha256`. **V0 in §5 asserted that
   command against a file that did not exist**; it does now.
3. **Correct the two false integrity claims first** (§8.2). A deposit freezes whatever is in the
   tree, including its errors.
4. **Tag, signed.**
   ```bash
   git tag -s v1.0.0 -m "Dossier de vérification adverse — dépôt archivistique v1.0.0"
   git push origin v1.0.0
   ```
   A signed tag anchors the manifest to a key rather than to a mutable branch. If no signing key
   exists, an annotated tag (`-a`) is the minimum.
5. **Enable the Zenodo–GitHub integration** at <https://zenodo.org/account/settings/github/> and
   switch this repository on. Then **publish a GitHub Release** from `v1.0.0`; Zenodo captures the
   release tarball automatically and mints a DOI. Zenodo issues both a **concept DOI** (all
   versions) and a **version DOI** (this release) — cite the **version DOI** for figures, and name
   the concept DOI as the stable entry point.
   *Alternatives, if Zenodo is not acceptable:* figshare, or Software Heritage
   (<https://archive.softwareheritage.org/>), which archives the git history itself and issues
   SWHIDs rather than DOIs. Software Heritage is the better fit for the *code*; Zenodo is the
   better fit for the *citable dataset*, which is what `CITATION.cff` declares this to be.
6. **Write the identifiers back into `CITATION.cff`.** Add the following keys (replace
   `10.5281/zenodo.XXXXXXX` with the DOI Zenodo returns — **do not write a DOI before it has been
   issued**):
   ```yaml
   version: 1.0.0
   commit: <the 40-character sha of the v1.0.0 tag>
   doi: 10.5281/zenodo.XXXXXXX
   identifiers:
     - type: doi
       value: 10.5281/zenodo.XXXXXXX
       description: Version DOI for release v1.0.0
     - type: doi
       value: 10.5281/zenodo.YYYYYYY
       description: Concept DOI — all versions
     - type: url
       value: https://github.com/davidleconte/shredding-cost-hcd-mongodb
       description: Working copy (mutable; not the citable artefact)
   ```
   While editing, fix the two metadata over-promises of §6.6: either retitle, or append
   "(concurrency: not measured — see RESULTS.md §6)" to the title and abstract, and replace the
   `write amplification` keyword with `read-modify-write`. Fix the licence field, which currently
   declares `CC-BY-4.0` for a deposit half of which is Apache-2.0:
   ```yaml
   license:
     - Apache-2.0
     - CC-BY-4.0
   ```
7. **Update the citation block in `README.md`** to name the version and the DOI, and state in one
   sentence that the GitHub URL is the working copy and the DOI is the citable artefact.
8. **Add a `CHANGELOG.md`** mapping each version to what changed in the prose. `data/raw/` is
   immutable by policy, so the changelog is a prose-drift record — which is precisely what a
   citing reader needs, given that commit `98ce434` rewrote figures and claims across eight files.

### 7.3 After the deposit

*Artifacts Available* becomes claimable. *Functional* remains blocked until the withheld archive
of `probes/README.md` gap 8 is published (or each withheld file is named with its reason) and
`env/docker-compose.hcd-dataapi.yml` exists. *Reusable* remains blocked on §2.3. *Results
Reproduced* remains unreachable, permanently, and the artefact should keep saying so.

---

## 8. Defects found by this assessment

Each is a defect of **provenance or labelling**, not of data. No figure in this dossier was found
to be fabricated; the figure-traceability check (§2.2, V12) reaches **all 120 distinct values** in
the committed evidence. Six of them it reaches only in `data/derived/inference.json` and only after
rounding — **derived, never measured**: the four `README.md` ratio-interval endpoints plus `0.966`
and `1.421`, the interval of challenge D12. Three more it reaches in `data/raw/` only after
rounding. Those nine are the labelling distinction that the earlier "0 orphans against `data/raw/`"
wording erased, and `ARTIFACT.md` itself is outside the checked set. The counts in this paragraph
were 108 and seven when it was written, then 113 and nine; they move with every figure a document acquires, which is
why CI job 7 re-derives them rather than this sentence asserting them.

### 8.1 `comparison.json` carries a block no probe emits

`data/raw/comparison.json` has a top-level `VERDICT` object. `grep -rn '"VERDICT"' probes/*.py`
returns nothing, and re-running the published merge against the committed inputs reproduces the
file exactly **except** for that key. `comparison_v2.json`, same code path, has none. This
contradicts `data/README.md`'s opening claim that every raw file is "byte-identical to the output
the probe wrote… not reformatted, not re-keyed" — for the file that backs the headline measurement
M13, and which `data/README.md` then instructs readers to read first.

**Not a fabrication.** Every figure inside the block (44×, 79×, 0.7775 / 0.0176 / 0.0098 ms/KiB,
40.9–130.787 ms) is present in the file's own `arms` object. *Remedy: do not edit the raw file. Add
an entry to `data/README.md` stating that the `VERDICT` object was added after the run and is
commentary, not instrument output; say whether by hand or by an unpublished revision of the merge
code, and publish that revision if one exists.*

### 8.2 Two front-matter claims about the evidence are false

**Status: closed, both halves.**

~~`README.md` line 61 (`run_at_utc` "stamped in every raw file") and the corresponding line in
`DISCLAIMER.md` are contradicted by the manifest.~~ Both were, and both are fixed. The claim in
`README.md` is now at line 106 and the one in `DISCLAIMER.md` at line 18; each states **26 of the
38** raw files, notes that one of those 26 is the hand-typed `"2026-09-17T16:5x (p16 ring)"` in
`findings_vector_rf3.json`, and points at `data/README.md`, which names all twelve unstamped files.
`DISCLAIMER.md` carries one thing the original remedy did not ask for and that the correction made
visible: **for those twelve files the date rests on the campaign reports, not on the evidence**.
That was true before and nobody had said it.

This was the cheapest claim in the repository to check and it sat in the first two documents a
reviewer reads, unchecked, through three published revisions.

The second half of the original remedy — *"then put the count in CI so the two documents cannot
diverge again"* — has been done for this document only: §1.3's counts are generated and checked by
CI job 9. `README.md` and `DISCLAIMER.md` are still hand-typed, which is why `README.md`'s count
went stale (it said 24 of 36) between the first writing of this section and its re-verification.

Related, and in the same class: `data/README.md` line 14 says fingerprints are "recorded by the
probe, not added by hand", while the same file documents `conditions.TO_BE_COMPLETED_BY_HAND`
blocks "filled in by hand", and `findings_disk_rf3.json` carries a top-level key literally named
`TO_BE_COMPLETED_BY_HAND` holding the disk-regime proof.

### 8.3 Three files self-declare a harness name the register contradicts

`findings_rf3.json`, `findings_rf3_rate50.json` and `findings_rf3_rate50_rep2.json` record
`"harness": "verify_storage_claims.py"`, while `probes/README.md` attributes them to
`verify_storage_claims_rf3.py`. The files are almost certainly right about what ran, because
`harness_version` in each reads *"1.0 + 3 mechanical fixes (env=HCD, deny-index ballast, driver
CL=ONE for system_traces on RF=2 two-DC ring)"* — which is exactly the RF = 3 variant's declared
patch set. This is a naming inconsistency, not a contradiction of evidence, but it means the file
alone does not identify its instrument. *Remedy: one line in `data/README.md` reconciling the two.*

### 8.4 M20's "captured artefact" is a string literal

`RESULTS.md` M20 states that the `COMMAND_UNKNOWN` result "is a captured artefact —
`findings_agg_hcd.json` (`structural` field)". That field is a fixed string typed at
`probes/probe_aggregation.py:196` and emitted **unconditionally**, regardless of server behaviour,
and no probe in the repository ever issues `aggregate`, `$group` or `distinct` against HCD. The
probe's own docstring calls the finding "recon, not a measurement"; the register upgraded it.

This does **not** make M20 false — the nineteen-command allow-list is reported in the campaign
record, and M21/M22 are independently and properly evidenced in the same file (V9). It makes M20's
*evidence column* wrong. *Remedy, cheap half, immediately: downgrade M20's evidence to "transcribed
from the campaign report, no captured artefact", alongside M6 and M8 which are already marked that
way. Expensive half: re-issue the three commands against the same build and ship the HTTP
responses.*

### 8.5 The headline ratios are pass-1-selected, and declared in only one document

`probes/probe_comparative.py:255` hard-codes `k = f"{sz.label}|pass1"`, so every cross-engine slope,
r² and ratio — 44×, 79×, 40×, 72× — is fitted on pass 1 alone. Pass-2 points were collected, sit in
`cmp_mongo.json` / `cmp_hcd.json` / `cmp_hcdcql.json`, and are unused. `docs/RESEARCH-DESIGN.md` line 381 now
declares it — *"the published 44×/79× are fitted on pass 1 only (`probes/probe_comparative.py:255`
selects `pass1`)"* — which lands after this section was first written and narrows the defect without
closing it. Nothing in `METHODOLOGY.md`, `RESULTS.md`, `LIMITATIONS.md`, `probes/README.md` or
`data/README.md` declares the choice, and those are the documents in which a reader meets the four
numbers. A disclosure a reader reaches only through the design reconstruction is a disclosure in the
wrong place. Audit finding I7 characterises inter-pass variance as "roughly 10–15 %". The direction of the
result is unaffected and unaffectable; the *precision* implied by two significant figures is not
supported. It is worth noting that this occurs in the instrument the dossier ranks as its
strongest — vendor-supplied, unmodified — which is a point about the limits of provenance ranking,
not about this probe's author. *Remedy: `docs/STATISTICS.md` is the right home; publish both passes'
fits side by side and state which the headline uses.*

### 8.6 A correction that runs *against* one of the repository's own self-accusations

`probes/README.md` gap 8 states: *"The ×1.56 variant-B read control quoted in `RESULTS.md` M3 —
p50 7.390 → 11.523 ms — is recorded in `control_read_B.json`, which is in that archive and not in
`data/raw/`. So a published number rests on an unpublished file."*

**That is overstated.** Both figures, and the complete n = 30 distributions behind them, are
published in `data/raw/findings.json` at
`findings[2].variant_B_indexed_chunks.read_control` — `p50_ms` `{1kb: 7.39, 8kb: 7.917, 32kb:
8.253, 128kb: 11.523}`, `growth: 1.56`, with min/p50/p95/p99/p999/max/stdev for each size. M3's
×1.56 therefore **does** trace to a published raw file.

What remains true, and is not narrowed: the withheld `control_read_B.json` is presumably the
originating per-run record, it is not published, and **the other twelve files in that archive
remain withheld** — including `probe4_traced.json`, which qualifies M4. The gap is real; this one
sentence of it is wrong, and correcting it is not a softening, because it does not touch any
comparative claim about either engine. *Remedy: restate gap 8 to name what is actually missing.*

### 8.7 Housekeeping

- `probes/__pycache__/` is present in the working tree; `.gitignore` covers it, so it is not
  published. When this section was first written it held compiled copies under `.py.cpython-312.pyc`
  names, i.e. the `.orig` files had been imported at some point — noted because the artefact's own
  provenance argument turns on which files were executed. **That observation is no longer
  reproducible**: the directory now holds exactly seventeen entries, one per probe, all of the
  ordinary `<module>.cpython-312.pyc` form, because the byte-compile check reported in §2.2
  (`python3 -m py_compile probes/*.py`) was re-run over the tree. The original reading is left
  standing rather than deleted, with this note: a verification step overwrote the evidence for one
  of this document's own minor findings, which is a small instance of the harness writing into what
  it measures.
- No probe carries an SPDX header (§2.3) — re-checked, still none of the seventeen.

---

## 9. Provenance of this document

Every factual claim above was established by executing a command against the working tree on
18 September 2026, not by reading prose. The commands are in §5. The document was written against
commit `b61eef4` and **re-verified command by command against `457568f`** the same day; every count
that moved is now regenerated by `.github/scripts/check_artifact_table.py` and re-derived in CI, so
the next time the tree moves under this document the failure is loud rather than silent. Where a
finding was true at `b61eef4` and has since been fixed, it is struck and marked, not removed. The manifest in §4 was generated
by `sha256sum`, not transcribed. The four badge definitions quoted in §2 are verbatim, each
including its final sentence, and were checked word for word against the v1.1 wording reproduced at
<https://sigir.org/general-information/acm-sigir-artifact-badging/>; `acm.org` returns HTTP 403 to
automated retrieval, so the policy page was not read directly.

Nothing under `data/raw/`, `probes/` or `docs/article/` was modified in the writing of this
document, nor in its re-verification. Those directories did change between the two, by work
recorded elsewhere — campaign 7bis added two evidence files and one probe, and the annulment of
challenge D12 edited two probe docstrings — and §1.4 lists what each change invalidated here.

Where this document disagrees with the repository — §2.1 on *Artifacts Available*, §8.6 on gap 8 —
the disagreement is recorded rather than resolved silently, and the reader is given the command
that settles it.
