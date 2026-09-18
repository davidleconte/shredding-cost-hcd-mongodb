# Improvement plan for this repository as a GitHub project

Consolidated from six independent reviews (first impression, project hygiene, CI
self-check, archival and citation, comparison against existing research artefacts,
README craft). Every factual claim below was re-verified against the working tree and
against the live GitHub API on 2026-09-18; where a reviewer's claim did not survive
that check, it was dropped and the reason is recorded in **REJECTED**.

Scope note. This plan is about the *project* — the surface a stranger meets, the
machinery that keeps the dossier honest between commits, and the citability of the
evidence. It is not about the measurements. Nothing here proposes changing a number,
and nothing here proposes making the repository look more confident than it is.

---

## Where this repository stands today

As a measurement dossier it is in unusually good order, and as a GitHub project it is
close to empty. Those two facts are the whole plan. The strength is real and it is
singular: **this repository argues against its own author and ships the evidence for
doing so.** RESULTS.md §4 numbers 52 points at which the measurements contradicted the
article they were written to support (verified: the list runs 1 to 52, contiguous, no
duplicates); §6 names sixteen axes that were never measured; `probes/README.md` records
that one of the two `.orig` reference files was reconstructed after the fact and is
therefore weak evidence; LIMITATIONS.md carries nine integrity findings and twenty
challenges written by the author against himself. The internal consistency behind that
prose also holds up mechanically: all 36 files under `data/raw/` parse as JSON, `git
log --diff-filter=MD -- data/raw/` is empty across the whole history, all 16 probes
compile under Python 3.12, the two declared probe patches are exactly 14 and 21 changed
lines, and an `ast` walk shows the multiset of numeric literals is identical on both
sides of both patches — the machine-checkable half of "no patch touched a size, a
threshold, a repetition count, a warm-up count or a verdict rule". Almost nothing in
the open-source world does this. It should not be diluted.

The weakness is that **none of it is enforced, pinned or reachable.** There is no
`.github/` directory, no workflow (`actions/workflows` returns `total_count: 0`), no
tag, no release, no topic (`"topics": []`), no homepage, no issue template, and ten
stock labels that actively mis-signal — `wontfix` contradicts a repository whose stated
policy is that contradictions are the point. Every invariant the dossier's credibility
rests on is defended by the author's memory alone, and at least one has already slipped
in a way a hostile reader finds in one grep: README.md line 63 and DISCLAIMER.md line 18
**[FAIT le 18 septembre 2026 — les deux documents nomment désormais un compte ; voir `DISCLAIMER.md` ligne 18 et `README.md` ligne 106.]** both assert that `run_at_utc` is stamped in every raw file, and it is present in 24 of
36. Meanwhile a citation to this work points at a rewritable branch tip on a platform
that is explicitly not an archive, which means the one sentence the whole dossier trades
on — "I did not edit this later" — is currently unfalsifiable. If the repository is
going to be quoted, the single highest-value thing that can be added to it is not more
prose, it is **the machinery that converts its promises into checks a stranger can watch
pass**, followed by a frozen, externally held copy of the evidence.

One thing has already changed under this plan's feet. The defect five of the six
reviewers ranked first — README.md line 79 citing `docs/STATISTICS.md`, which did not
exist — was **resolved during this analysis**: the concurrent research workflow committed
a 66 KB `docs/STATISTICS.md` at 11:00 today. A fresh link resolution over every relative
link in the root Markdown plus `data/README.md` and `probes/README.md` now reports zero
broken links. The item survives in this plan only as a pre-flight check (rank 1), because
the link-checking CI gate must not be merged until that file is committed rather than
merely present in the working tree.

---

## TIER 1 — do now, minutes each

### 1. Confirm `docs/STATISTICS.md` is committed before anything else lands

**Why a sceptical reader gains.** It is the target of the citation that backs the most
self-critical sentence in the document — the concession that the 21.7× cannot be tested
because the raw series were not kept, on the one axis HCD wins. A 404 there reads as the
concession being ornamental. It also gates every other item: the link-check job in rank 9
turns red on this path alone, and a red gate on a repository about rigour is worse than
no gate.

**What to do.** `git status --short docs/STATISTICS.md` — at the time of writing it is
**untracked** (present on disk, 66 306 bytes, not in the index). It belongs to the
concurrent workflow; do not add it here. Simply verify it is committed, then re-run:
`python3 - <<'EOF'` link resolution over `*.md`, `data/README.md`, `probes/README.md`
(the script in rank 9 does this). Do not proceed to rank 9 until it returns zero.

**Impact** high (gates the rest) · **Effort** minutes · **Risk** none ·
**Locked path** yes, `docs/` — verification only, no edit.

### 2. Front-load the repository description so the payload survives the unfurl

**Why a sceptical reader gains.** The single most disarming fact about this project is
that it contradicted its own author 52 times, and nobody who meets the link socially ever
sees it. Verified live: the description is 275 characters and GitHub's own
`og:description` meta tag reads `…raw evidence, and 52 points...` — the clause "where the
measurements contradicted the article they were written to support" is cut by GitHub
before Slack, LinkedIn or an HN preview ever gets it.

**What to do.**
```
gh api -X PATCH repos/davidleconte/shredding-cost-hcd-mongodb \
  -f description='A measurement dossier that refuted its own author: 52 self-contradictions, 23 measurements, raw evidence. IBM DataStax HCD 2.0.6 vs MongoDB 8.x storage layout.'
```
Keep the strongest fact inside the first ~150 characters. The number 52 must stay the
number RESULTS.md §4 actually lists; re-check with the contiguity script before changing it.

**Impact** high · **Effort** minutes · **Risk** none · **Locked path** no.

### 3. Set repository topics

**Why a sceptical reader gains.** This one is not about the reader who has the URL; it is
about the reader who could refute the work and does not know it exists. Verified:
`"topics": []`. Cassandra and MongoDB storage engineers find work through topic pages, and
they are the only audience that can produce the counter-measurement the README asks for.

**What to do.**
```
gh api -X PUT repos/davidleconte/shredding-cost-hcd-mongodb/topics \
  -f names[]=mongodb -f names[]=apache-cassandra -f names[]=datastax \
  -f names[]=document-database -f names[]=storage-engine \
  -f names[]=benchmark-methodology -f names[]=reproducible-research -f names[]=open-data
```
Mirror the `keywords` already in CITATION.cff so the two cannot drift. Deliberately omit
a bare `performance` or `benchmark` topic: the dossier's own reading rules argue these
figures establish mechanism and direction, not production magnitudes, and a topic that
advertises it as a benchmark invites exactly the misquotation those rules exist against.
Leave `homepage` null until a DOI exists (rank 18).

**Impact** high · **Effort** minutes · **Risk** none, reversible in one command ·
**Locked path** no.

### 4. RECOMMENDATION — the `run_at_utc` claim is false for a third of the corpus

**Why a sceptical reader gains.** This is a verifiable factual overclaim in the two
documents a hostile reader opens first, on exactly the axis — provenance of evidence —
where the dossier stakes everything. It is also the cheapest possible discredit: one grep.
The dossier's own standard is that the reserve travels with the claim in the same breath;
here the claim has no reserve and is simply wrong.

**What to do.** Hand to the workflow that owns these files. Verified figures: 24 of 36
files carry a top-level `run_at_utc`; 12 carry no ISO-8601 timestamp anywhere —
`cmp_hcdcql.json`, `control_read_A_run1.json`, `control_read_A_run2.json`,
`findings_hcd_vec_freshness.json`, `findings_tier_method2.json`, `findings_turn_hcd.json`,
`findings_turn_mongodb.json`, `probe4_rf3_supplementary.json`, `rmw_postflush.json`,
`tier_comparison.json`, `vector_freshness_idle.json`, `vector_freshness_loaded.json`.
README.md line 63 currently reads ``17–18 September 2026, `run_at_utc` stamped in every
raw file``; DISCLAIMER.md line 18 makes the same claim against the source column ``every
file under `data/raw/` ``. Suggested replacement, in the dossier's own register:
``17–18 September 2026. `run_at_utc` is stamped in 24 of the 36 files under `data/raw/`;
the remaining 12 carry no timestamp of their own and are dated only by the campaign report
that cites them — a traceability gap, listed rather than papered over.`` Note that
`rmw_postflush.json` is among the twelve, and it is the evidence for the ×1.52 correction
the README calls one of its three headline self-refutations. Reproduce with:
`for f in data/raw/*.json; do grep -qE '[0-9]{4}-[0-9]{2}-[0-9]{2}T' "$f" || echo "$f"; done`

**Impact** high · **Effort** minutes · **Risk** none; the correction strengthens the
document · **Locked path** yes, README.md and DISCLAIMER.md.

### 5. Replace the stock labels with the dossier's own register vocabulary

**Why a sceptical reader gains.** Labels are what the issue forms attach, so they must
exist before rank 6 is useful. They are also what lets a reader filter the tracker for
"objections the author conceded" — for this repository, the single most interesting view.
Verified: the label set is the GitHub default plus `accessibility`; `wontfix` in
particular contradicts the stated policy, and `good first issue` / `help wanted` imply a
chore backlog that does not exist.

**What to do.** Via `gh label create` / `gh label delete` against
`davidleconte/shredding-cost-hcd-mongodb`. Create, matching the `labels:` keys used by the
forms in rank 6: `reproduction`, `contested-measurement`, `challenge`,
`counter-measurement`, `citation`, plus three outcome labels mirroring the register's own
verdicts — `confirmed`, `refuted-by-measurement`, `open-unresolved`. Delete
`good first issue`, `help wanted`, `enhancement`, `duplicate`, `invalid`, `wontfix`. Keep
`documentation`, `question` and `accessibility`. Keep `bug` only as a channel for defects
in the probe code itself, which is a real category given `probes/` is Apache-2.0 and
runnable.

**Impact** medium · **Effort** minutes · **Risk** none, fully reversible · **Locked path** no.

### 6. Issue forms keyed to Mxx, raw file and regime

**Why a sceptical reader gains.** The README closes by saying contradictions "are the
point of publishing, and are welcome as issues", and then offers a blank box. For a
dossier where every number is meaningless without its regime, its host, its n and its
percentile, an unstructured box guarantees that the first serious counter-measurement
arrives unusable. A form that will not submit without a measurement identifier and a raw
filename turns a stranger's objection into something adjudicable against `data/raw/` in
minutes — and teaches the quoting discipline at the one moment the reader is paying
attention. Three reviewers proposed variants of this; the union below is deduplicated to
four forms, because five was already past the point where a form suppresses the
submissions it wants.

**What to do.** Create `.github/ISSUE_TEMPLATE/` with four YAML issue forms and a
`config.yml`. Syntax per GitHub's issue-forms documentation: top-level
`name`/`description`/`title`/`labels`/`body`, and body elements `markdown`, `input`,
`textarea`, `dropdown`, `checkboxes`. **Do not use the `type:` key** — it resolves against
organization-level issue types and this is a user-owned repository.

- `01-failed-reproduction.yml` — "I ran a probe and got a different number". Dropdown of
  the 16 probes; the Mxx; host fingerprint (CPU, RAM, load average, virtualisation,
  whether the page cache could be dropped); regime dropdown {memtable or cache resident,
  proven disk-bound, unknown}; n per point; engine build strings (`nodetool version`, Data
  API image tag, MongoDB `db.version()`, pymongo version); percentiles observed; raw JSON.
- `02-contested-measurement.yml` — "I think Mxx is wrong". Which Mxx; which sentence;
  whether the objection is to the mechanism or only to the magnitude; which file under
  `data/raw/` the objector believes contradicts it.
- `03-challenge-or-counter-measurement.yml` — a Cxx/Dxx-style challenge, or an offer to
  measure one of the sixteen axes RESULTS.md §6 lists as never measured (dropdown of
  those axes). Which published conclusion it touches; what would have to be measured to
  settle it.
- `04-misquote-or-citation.yml` — a figure from here is being quoted without its regime,
  or the citation metadata is wrong. Which of the eight reading rules is being broken, and
  where.

`config.yml` with `blank_issues_enabled: true` — keep the escape hatch, a dossier that
invites unanticipated objections must not force them through a dropdown — and
`contact_links` pointing at LIMITATIONS.md, the reading-rules anchor in RESULTS.md, and
DISCLAIMER.md, each labelled "read this before filing". Mark only the genuinely
load-bearing fields `required: true`; keep each form under about twelve fields. Wording
stays in the plain technical voice of LIMITATIONS.md, not support-desk language.

**Impact** high · **Effort** under an hour · **Risk** over-structuring repels the one
serious objector who fits no form; mitigated by blank issues staying enabled ·
**Locked path** no.

### 7. A ten-line pull-request template stating the append-only rule

**Why a sceptical reader gains.** Most contributions here will be issues. But the one
thing a well-meaning pull request can destroy is the property the dataset's value rests
on — that no file under `data/raw/` has been edited after the fact. A contributor
normalising the twelve files that lack `run_at_utc` would be doing the most damaging
possible thing while believing they were helping. The template says so at the moment it
is about to happen; rank 9 enforces it.

**What to do.** Create `.github/pull_request_template.md`, roughly ten lines: which Mxx or
which document this touches; a checkbox `[ ] This PR modifies no file under data/raw/ —
raw evidence is append-only, including the files a later run refuted`; a checkbox
`[ ] If this PR changes a number, the regime, n and percentile are stated in the
description`; one line pointing at CONTRIBUTING.md. No sign-off block, no changelog
section, no reviewer checklist.

**Impact** low · **Effort** minutes · **Risk** none beyond letting it grow into a
checklist · **Locked path** no.

### 8. Disable the unused wiki

**Why a sceptical reader gains.** The repository's structural argument is that every
claim, reserve and piece of evidence lives in one traceable corpus. Verified: the wiki is
enabled and has never been created; Projects is enabled and unused. Both show as tabs, and
both are places a reader's objection can land outside the audited corpus.

**What to do.** `gh api -X PATCH repos/davidleconte/shredding-cost-hcd-mongodb -F
has_wiki=false`. Leave Issues enabled, leave blank issues enabled, and **leave Projects
alone** unless the author says otherwise — C3–C9, C11–C15 and D2–D5 are all unresolved and
a project board is a plausible place to track them. Do not enable Discussions: a second
free-form venue fragments the record the same way.

**Impact** low · **Effort** minutes · **Risk** none, reversible · **Locked path** no.

---

## TIER 2 — worth doing, hours

### 9. One CI workflow, `evidence.yml`, with named jobs that each check one stated promise

**Why a sceptical reader gains.** This is the item that most changes what the repository
*is*. Today, verifying that the README's 602× is `133984.229 / 222.711` and not a typo
costs a reader ten minutes with a JSON viewer; a dossier whose only authority is that it
argued against itself is one careless commit away from losing that authority, and nothing
stands between it and that commit. CI here converts five prose promises — the evidence is
unedited, the figures trace to it, the patches changed no constant, the links resolve, the
registers are complete — into something a hostile reader confirms in one glance. Five
reviewers proposed overlapping workflows; they are consolidated here into one file with
named jobs, because six separate workflow files on a repository with no software in it
would itself read as cargo cult.

Every job below was prototyped against today's tree and **passes**, which is the only
condition under which adding a gate is worth anything.

**What to do.** Create `.github/workflows/evidence.yml`: `name: evidence`; triggers `push`
on `main`, `pull_request`, `workflow_dispatch`; top-level `permissions: {contents: read}`;
a `concurrency` group keyed on the ref. Pin `actions/checkout@v7.0.1` and
`actions/setup-python@v7.0.0` with `python-version: '3.12'` to match the recorded
interpreter 3.12.3 — **both versions verified against the GitHub API on 2026-09-18 as the
current releases** (published 2026-07-20); v5/v6 examples found online are stale. Jobs:

- **`links-internal`** — `.github/scripts/check_links.py`, offline, no third-party action.
  Walk every `**/*.md` outside `.git/`; for each `[text](target)` skip `http(s):` and
  `mailto:`, split `path#anchor`, resolve `path` relative to the containing file, require
  it to exist, and where the target is Markdown require the anchor to match a GitHub-style
  slug of some heading in that file. Verified: zero failures today, once
  `docs/STATISTICS.md` is committed. **Do not extend this to backticked filenames** —
  `data/README.md` and `probes/README.md` deliberately name nine JSON files that live in
  the evidence snapshot archive rather than in `data/raw/`, and a naive existence check
  over backticks would report nine false positives and train the author to ignore the job.

- **`evidence-immutable`** — `checkout` with `fetch-depth: 0`, then a shell script
  asserting (a) `git log --diff-filter=MDR --format=%H -- data/raw/` prints nothing
  (verified: it prints nothing today, across the whole history) and (b) on pull requests,
  `git diff --name-status --diff-filter=MDR <base>..<head> -- data/raw/` is empty.
  Additions are permitted — the declared correction protocol is a new file plus a note,
  never an edit. Apply the same gate to `probes/*.py.orig`, whose whole evidential function
  is being a frozen pre-patch reference. Put a comment at the top of the script stating
  precisely what it does and does not prove: it proves the bytes have not changed since
  they entered git, **not** that they match what the probe wrote — no CI can witness that.

- **`figures-trace`** — the check a sceptic actually wants. `.github/claims.yaml` lists
  each headline figure as an expression over raw-JSON paths, an expected value, a relative
  tolerance, and the prose file plus literal substring that must still be present. Seed it
  with the seven recomputed ratios (21.7, 23.7, 19.6, 602, 9.0, 66.6, 1.52). Fail if the
  arithmetic drifts **or** if the substring has vanished from the prose, so renaming a
  figure without updating the claim fails as loudly as changing it. Add a generic sweep:
  collect every numeric leaf from all 36 raw files, regex every `p50 <number>` in README,
  RESULTS, LIMITATIONS and METHODOLOGY, and require each to match some raw value within
  0.05 % relative tolerance. Give the script an explicit `# ci-figures: ignore` line-suffix
  escape for a figure legitimately quoted from an external source, and require any use of
  it to be justified in the claims file so the escape hatch is itself auditable. Make the
  script fail if `claims.yaml` has fewer entries than a floor recorded inside it, so entries
  cannot be deleted instead of fixed. Print a job-summary table so the run page is readable
  evidence.

- **`patch-provenance`** — the one part of audit finding I2 a machine can answer. For each
  `probes/*.py.orig`: parse the changed-line count out of `probes/README.md` rather than
  hardcoding it, and assert `diff -u orig patched | grep -cE '^[+-][^+-]'` matches, so an
  undeclared extra edit fails **and** a stale README fails; then `ast.parse` both files and
  assert the `Counter` of every int/float `ast.Constant` (excluding bool) is equal. Verified
  today: 14 and 21 changed lines as declared, and identical numeric-literal multisets on
  both patches. **The job must print into the step summary the caveat the register already
  makes in prose** — for `verify_storage_claims.py` the `.orig` is genuinely retained and
  the check is independent evidence, whereas for `probe_tier_vs_storage.py` the `.orig` was
  reconstructed by reverting the very patch it displays, so the check is true by
  construction and rules out nothing. Without that line next to the tick, the job launders a
  weak claim into a strong-looking green check, which would make the repository worse. Name
  `verify_storage_claims_rf3.py` and `disk_regime_driver.py` explicitly as out of scope,
  since they ship no `.orig`.

- **`registers`** — assert M1–M8 and M10–M23 are defined in RESULTS.md §3 with no
  duplicates and M9 explicitly described as never assigned rather than merely absent; every
  Mxx cited in the root Markdown is defined; LIMITATIONS.md defines I1–I9, C1–C15, D1–D5;
  and the numbered list under RESULTS.md `## 4` runs 1..n contiguously with n equal to the
  count asserted in the README. Anchor that last regex to `^\s*(\d+)\.\s` at line start — a
  naive `[0-9]+\.` matches the literal `376.698` inside the section and reports 53 instead
  of 52, which is how a badly written version of this check fails on a correct repository.
  Locate sections by heading anchor, never by line number, and fail with a message naming
  the heading that could not be found. Verified: 52, contiguous, today.

- **`probes-syntax`** — blocking `python -m compileall -q probes/` (verified: all 16
  compile; needs no dependencies, so it can never fail for reasons outside the repository),
  then a **non-blocking** (`continue-on-error: true`) `pip install -r env/requirements.txt`
  as an early warning that the declared environment has stopped resolving. Upload `pip
  freeze` with `actions/upload-artifact@v7.0.1` (verified current) under a name that says
  plainly what it is — `resolved-env-today-NOT-the-run` — because the temptation to read it
  as recovering the deliberately unpinned pymongo version is real, and the README is
  explicit that pinning a version there would be an invented fact. Do not attempt `--help`
  smoke runs: 10 of 16 probes use argparse and 6 do not, and a partial smoke test that
  passes for 10 invites the reading that all 16 were exercised.

- **`cff-validate`** — `dieghernan/cff-validator@v5` (verified: v5 published 2026-04-21)
  against `CITATION.cff`. A malformed CFF kills GitHub's citation widget silently.
  Prefer this over `citation-file-format/cffconvert-github-action@2.0.0`, which is real but
  last released in January 2022.

- **`fingerprint-coverage`** — deliberately **not** a gate on coverage. Blocking: all 36
  files parse as JSON and the count matches the number `data/README.md` states. Reporting:
  a step-summary table of key coverage — verified today at 36 files, 24 with `run_at_utc`,
  and the `probe` and `host` counts to be measured at implementation time. Gate only on
  non-regression against a committed `.github/fingerprint-baseline.json`, so a newly added
  raw file may not be less traceable than the corpus, while the existing corpus is described
  rather than retroactively condemned. **Do not assert a universal `run_at_utc`**: twelve
  files legitimately lack it, and a gate that fails on day one is deleted on day two.

**Impact** high · **Effort** hours · **Risk** a red gate on a repository whose argument is
rigour is worse than no gate; every job above passes today, and rank 1 must land first ·
**Locked path** no — everything lives under `.github/`.

### 10. A weekly, non-blocking external link-rot sweep

**Why a sceptical reader gains.** The dossier cites CEP-15, the Accord paper, the SAI blog
post, the YCSB paper, a mailing-list archive and a Maven coordinate — the citations that
let a reader check the [D]/[R] evidence markers against their sources. Those rot silently.
Keeping this separate from rank 9 matters: third-party link rot is not the author's defect,
and a red X for it would devalue the ticks that do mean something.

**What to do.** A second file, `.github/workflows/link-rot.yml`, triggered only on
`schedule: '17 6 * * 1'` and `workflow_dispatch`, never on pull requests.
`actions/checkout@v7.0.1` then `lycheeverse/lychee-action@v2.9.0` (verified: current
release, published 2026-07-09) with `fail: false` and
`args: --no-progress --max-retries 2 --exclude '^http://127\.0\.0\.1' --exclude '^http://HOST' --exclude '^http://www\.w3\.org/2000/svg' -- '**/*.md'`.
The exclusions are required: README.md and REPRODUCING.md legitimately contain
`http://127.0.0.1:8181/...` and `http://HOST:PORT/v1/<keyspace>` as instructions, and the
corrected article embeds an SVG namespace URI. Results to the step summary only — **no
auto-filed issues**, which would be noise on a tracker that exists to receive real
objections.

**Impact** medium · **Effort** minutes · **Risk** lychee reports occasional false positives
against rate-limiting hosts; non-blocking by design · **Locked path** no.

### 11. One tool that resolves a headline figure to its raw file in sixty seconds

**Why a sceptical reader gains.** REPRODUCING.md correctly states on its first page that a
reader will not reproduce these numbers. That leaves the sceptic with no cheap act of
verification at all: the gap between "read 80 KB of RESULTS.md" and "stand up two
databases" is the entire repository. One command that resolves an identifier to the raw
file, prints the value, prints the JSON pointer it dereferenced, and prints the regime
alongside it closes that gap — and simultaneously teaches that the regime travels with the
number. Two reviewers proposed this as separate tools (a quoter and a recomputer); they are
one tool with two modes.

**What to do.** Add `tools/quote.py`, standard library only, supporting:
- `python3 tools/quote.py M15` — print the value, the raw file, the JSON pointer
  dereferenced, the file's `run_at_utc` (or "no timestamp of its own" for the twelve that
  lack one), the regime, and the one-line reserve.
- `python3 tools/quote.py --list` — the whole map.
- `python3 tools/quote.py --recompute` — re-derive every published ratio from `data/raw/`
  and print `figure | recomputed | as published | source file | Mxx`, exiting non-zero on
  any mismatch beyond a declared rounding tolerance. Cover at least: 44×/79× stack-to-stack
  and 40×/72× engine-to-engine; 19.6× and 23.7×; 602×, 9.0× and 66.6×; the ×1.52 post-flush
  growth from `rmw_postflush.json`; both tier shares.

Drive it from a small JSON or dict mapping Mxx to (file, JSON pointer, regime) so the
mapping itself is auditable, take published values from a literal dict inside the script and
**never by scraping README.md** (another workflow is rewriting it), and state in the header
that RESULTS.md §3 is authoritative and the dict is a test fixture. Write nothing into
`data/` or `docs/`. Cover the map with the `figures-trace` job so it cannot drift silently.

**Impact** high · **Effort** hours · **Risk** the map is a hand-built layer over the
evidence and can mis-point; printing the dereferenced pointer lets a reader check the
extraction by hand · **Locked path** no.

### 12. Two figures, generated from the raw JSON by a dependency-free script

**Why a sceptical reader gains.** There is no figure, no plot and no diagram anywhere in
the repository, and this project has the rarest thing in benchmarking: data that would make
an honest picture. Two pictures, specifically, and both of them argue *against* the author.

The first is the regime collapse. The repository's whole thesis is that a coefficient is a
property of the measurement regime, not of the engine, and that this is what broke its
author's own headline. Right now that thesis is three numbers scattered across three
paragraphs. The three series exist at identical sizes (1/8/32/128 KiB) and identical n = 30,
so they plot directly against each other with nothing interpolated and nothing invented:
`findings.json` variant_B by_document_size p50 12.104 / 15.718 / 32.108 / 90.783 (memtable,
RF=1, ×7.50); `findings_disk_rf3.json` variantB_indexed_chunks.update_p50 20.389 / 25.127 /
44.314 / 121.189 (disk, RF=3, ×5.94); `rmw_postflush.json` by_size p50 107.765 / 112.086 /
119.22 / 163.402 (SSTable read path, ×1.52). Three lines on a log-x axis show the slope
flattening while the intercept rises — the flattening is the self-refutation, the rising
intercept is the reserve M15 declares against itself. Prose cannot make a reader see both at
once.

The second is the separation of support behind the 21.7×. It is the only axis HCD wins and
the only one where the two samples overlap; the README says so in words and it is the
hardest sentence in the document to absorb. Drawn as three horizontal ranges on a log axis
with the medians marked, a reader sees at a glance that MongoDB's fastest observation beats
HCD's median and that the wildcard arm is disjoint from both.

**What to do.** Add `figures/make_figures.py` — Python standard library only, emitting SVG
text directly. **Do not add matplotlib to `env/requirements.txt`**, which is pinned to what
actually ran during the campaign and would lose that meaning. The script reads the JSON by
path, holds no hard-coded latency, and prints the growth factors it derived so they can be
checked against the files. Emit `figures/regime-collapse.svg` and
`figures/separation-of-support.svg`. Give each an explicit light background rect and dark
text so it stays legible in GitHub's dark theme. Label axes in ms and KiB; caption each line
with its regime and its growth factor; **burn the regime labels and the n into the image
itself**, so a cropped screenshot still carries them — a figure invites exactly the
decontextualised screenshot this repository spends 80 KB warning against. For the second
figure, draw min–max as a rule with p50, p95 and p99 as ticks and **not** a box plot:
quartiles were never recorded and a box would imply data that does not exist; the caption
must read "min, p50, p95, p99, max over n = 50; the per-observation series were not
retained". Round all emitted floats explicitly so the SVG is byte-deterministic, then have
the `figures-trace` job re-run the generator and `git diff --exit-code` the output.
Embedding the figures in README.md and RESULTS.md is a separate, locked step (rank 22).

**Impact** high · **Effort** hours · **Risk** decontextualised reuse, mitigated by burning
the labels in; non-deterministic float formatting would make CI flap, mitigated by explicit
rounding · **Locked path** no for the generator and the SVGs; yes for the embed.

### 13. `CONTRIBUTING.md` written as "how to contradict this dossier"

**Why a sceptical reader gains.** The README promises that corrections are the point and
never specifies what a correction has to contain to be acted on, or what happens to it
afterwards. The machinery already exists internally — challenges get Cxx numbers, integrity
findings get Ixx, self-refutations get numbered entries, and C1, C2, C10 and D1 carry
measured resolutions the author wrote against himself — but a contributor cannot see that
this is a process rather than a posture. Writing it down converts the ethos into a
commitment a reader can hold the author to.

**What to do.** Create `CONTRIBUTING.md` at the root, under about 150 lines, in the plain
technical English of LIMITATIONS.md. Sections:

1. *What a contribution is here* — a correction, a failed reproduction, a counter-measurement,
   a challenge to a published conclusion, or a misquotation report. Explicitly not a feature.
2. *The evidence bar*, restated from METHODOLOGY.md rather than invented: state the regime,
   state n, report percentiles and never a mean for latency, give the host fingerprint
   including load average and whether the page cache could be dropped, give both engine build
   strings, attach the raw JSON. A number without its regime cannot be entered.
3. *What happens to it* — a confirmed contradiction becomes a numbered point in RESULTS.md §4
   or a new Cxx in the challenge register, credited to the reporter; one the author cannot
   reproduce is recorded as open rather than closed; nothing under `data/raw/` is ever edited
   or deleted to accommodate a correction, because a later refutation is published alongside
   the refuted file, not in place of it — `findings_mongot_freshness.json` still reading
   `p50_ms: 1015.201` is the worked example the README already cites.
4. *Pull requests* — accepted for probes, typos and prose; refused for anything under
   `data/raw/`, with the `evidence-immutable` job named as the enforcement.
5. *Lab safety*, two short paragraphs, replacing a generic SECURITY.md: REPRODUCING.md
   instructs the reader to stand up HCD with the token `Cassandra:Y2Fzc2FuZHJh:Y2Fzc2FuZHJh`
   (base64 `cassandra`/`cassandra`) and `env/docker-compose.mongodb-rs.yml` brings up an
   unauthenticated replica set. Those are correct for a disposable single-host lab and
   dangerous anywhere reachable; the realistic harm is a reader following the instructions on
   a cloud VM with an open security group. Say they must not be exposed to any network you do
   not control, and that the probes drop and recreate keyspaces and indexes — cross-link
   REPRODUCING.md §6, which already documents the restoration procedure.
6. *House rules*, two paragraphs in place of a Contributor Covenant: hostility to claims is
   the point of this repository and is welcome; hostility to people is not; vendor advocacy
   without a measurement attached will be closed in either direction, since the author is an
   IBM employee publishing a result unfavourable to IBM and the tracker is not a venue for
   relitigating that.

**Impact** high · **Effort** hours · **Risk** section 3 is a promise, and a public tracker
makes breaking it visible. Do not write section 3 unless the author confirms he will honour
it · **Locked path** no.

### 14. `ERRATA.md` — a dated log for corrections that arrive after publication

**Why a sceptical reader gains.** RESULTS.md §5 records refutations the campaigns produced
internally, which is rare and good, but there is nowhere for a correction that arrives next
month. Without such a log, a future correction either silently rewrites a document —
destroying the exact property this repository trades on — or is lost. Both of the critique
exemplars solved it the same way: a dated in-README erratum naming the third party who found
the flaw, the scope affected, and whether the conclusions move.

**What to do.** Create `ERRATA.md` at the root: reverse-chronological, one dated entry per
correction, each stating who reported it (or that it was the author), which Mxx and which raw
file it touches, what changed in the documents, what did **not** change in `data/raw/`, and
whether the conclusion moves. State the rule at the top, matching `data/README.md`: raw files
are never edited; a correction is a new file plus an entry here. Linking it from the README
"Honesty statement" and the DISCLAIMER "Reporting an error" section is one line each and is
locked (rank 22).

**Impact** medium · **Effort** minutes · **Risk** a stale errata log is worse than none ·
**Locked path** no for the file; yes for the two inbound links.

### 15. A SHA-256 manifest of `data/raw/`, with an honest paragraph about what it does not prove

**Why a sceptical reader gains.** "Byte-identical to the runs" is the load-bearing sentence
of the dossier and it appears at least six times across README, METHODOLOGY, LIMITATIONS and
`data/README.md`. There is no checksum, manifest or signature anywhere in the tree. A reader
who forks or mirrors the data has no way to tell a corrupted copy from the original. This is
the one place where the repository asserts something about itself and gives the reader no
means to test it — precisely the failure mode it spends LIMITATIONS.md attacking in others.

**What to do.** Generate the manifest as `.github/evidence-manifest.sha256` — **not** under
`data/raw/`, which is locked and whose file count is itself an asserted figure — with
`(cd data/raw && sha256sum *.json) > .github/evidence-manifest.sha256`. Verify it in the
`evidence-immutable` job. Then hand a short paragraph to the owner of `data/README.md`, to sit
under the existing "byte-identical" claim, and **the wording matters more than the file**:
(a) a manifest committed in the same repository as the data proves almost nothing on its own,
because whoever can edit a JSON file can edit the manifest in the same commit — it catches
accidental corruption, forks and mirrors, not bad faith; (b) it becomes evidence only when
bound to something the author cannot retroactively change, which is the signed tag and above
all the Zenodo deposition, whose files are immutable after publication and which publishes
per-file checksums held by CERN rather than by the author; (c) even then it does not prove the
JSON is what the probe wrote at run time, since the hash is computed after the fact by the same
person who ran the probe — nothing short of an independent re-run closes that gap; (d) it does
not touch the 13 evidence files `data/README.md` already discloses as held in an archive outside
this repository. A `SHA256SUMS` file that reads as a claim to tamper-evidence it does not deliver
would, in this repository, be worse than nothing. The paragraph is the point.

**Impact** high · **Effort** hours (mostly the paragraph) · **Risk** rhetorical, as above;
also the manifest must be regenerated whenever a raw file is added, so it needs the CI check
or it drifts silently · **Locked path** no for the manifest; yes for the paragraph.

---

## TIER 3 — needs an external service, a second host, or new measurement

### 16. Tag a signed `v1.0.0` and mint a Zenodo concept DOI

**Why a sceptical reader gains.** This is the difference between an artefact a thesis can
cite and one it cannot. Verified: zero tags, zero releases, five unsigned commits (`%G?` = `N`
on all five), no `version`, `doi`, `identifiers`, `commit`, `orcid` or `contact` in
CITATION.cff. Every citation the README offers points at a mutable branch tip on a platform
that is explicitly not an archive. A reader who quotes M13 today cannot get back to the bytes
they read, and a reviewer who wants to check that a number was not adjusted after publication
has only the author's word — which is exactly the force this artefact's whole claim to
authority depends on. A Zenodo deposition gives an immutable file set, a version DOI that
always resolves to it, and a concept DOI that resolves to whichever version is newest, so a
citation survives later corrections instead of rotting. It also moves a copy of the evidence
off the platform the author controls.

**What to do, in this order.** (1) Wait for the concurrent workflow to land — tagging a tree
mid-rewrite freezes a half-revised dossier, and rank 4's false `run_at_utc` claim must be
corrected first. (2) Configure a signing key (`commit.gpgsign`, `user.signingkey` and
`gpg.format` are all currently unset), then `git tag -s v1.0.0 -m 'Seven campaigns, M1–M23,
raw evidence as run'` and `git push origin v1.0.0`. (3) On zenodo.org, open the profile menu →
GitHub → Sync now, find the repository and toggle it on. (4) *Only then*
`gh release create v1.0.0`: Zenodo's webhook fires on the release event, and releases created
before the repository is toggled on are **not** retroactively archived. Release notes should
state what the snapshot contains and, in one sentence, that later releases may refute figures
in this one rather than remove them. (5) The published record carries both a version DOI and a
concept DOI; the concept DOI is the one to use. (6) The badge endpoint
`https://zenodo.org/badge/DOI/<concept-doi>.svg` is real and one DOI badge is infrastructure,
not decoration — do not add a row of others.

**Impact** high · **Effort** hours, plus waiting · **Risk** a DOI is permanent and its files
immutable, so a DOI over a mid-revision tree is a permanent record of a draft. It also raises
the stakes on the honesty statement: an archived artefact cannot be quietly corrected, only
superseded — which is consistent with this repository's policy but should be a deliberate
choice · **Locked path** no for the tag and release; yes for the write-back (rank 22).

### 17. Archive the commit graph in Software Heritage

**Why a sceptical reader gains.** Zenodo archives a zip of one release; Software Heritage
archives the full history, independently, under identifiers that are cryptographic hashes of
content rather than registry entries — so a SWHID cannot be repointed by anyone, including
Software Heritage. For an artefact whose credibility rests on its history not having been
rewritten, an external copy of the *history* is a stronger claim than an external copy of one
snapshot.

**What to do.** Submit the clone URL at `https://archive.softwareheritage.org/save/` after the
concurrent workflow lands. Retrieve the snapshot SWHID and record it in CITATION.cff as an
`identifiers` entry with `type: swh`, which CFF 1.2.0 accepts as a first-class identifier type.
Do this separately from Zenodo's own forwarding.

**Impact** medium · **Effort** minutes plus ingestion time · **Risk** archiving is irreversible
and public, which is appropriate for an already-public repository but preserves any mistake in
the tree · **Locked path** no for the archiving; yes for the SWHID write-back.

### 18. Custom social preview card

**Why a sceptical reader gains.** The current card is GitHub's auto-generated fallback —
avatar, repository name, truncated description — indistinguishable from any other repository.
For a link that will mostly travel through Slack and LinkedIn, a card carrying the
regime-collapse plot would convey the premise before anyone clicks, and do it with a
measurement rather than a slogan, which is the only register this repository can afford.

**What to do.** Once rank 12 exists, render a 1280×640 PNG from `regime-collapse.svg` with a
one-line caption that **names the regime, not just the number**. Upload under Settings →
General → Social preview. There is no REST endpoint for this; it is a web-UI-only setting and
cannot be scripted with `gh`.

**Impact** low · **Effort** minutes · **Risk** a card built around a single ratio is exactly
the decontextualised quotation the dossier warns against; the caption is the mitigation ·
**Locked path** no.

### 19. A "Related public evidence" section

**Why a sceptical reader gains.** The dossier compares two named products across ten axes and
cites no external evidence about either. A sceptic's first question is "who else has measured
this, and do they agree?" and there is currently no answer, which makes the work look more
isolated than it is. It would also let the repository state the thing it is uniquely
positioned to state: that these axes are not covered by the existing public benchmarks, which
is why the campaigns exist.

**What to do.** A short `docs/RELATED.md` (or a README section) listing what already exists
publicly on these engines and what it does and does not cover — Jepsen's MongoDB analyses
(safety, not storage layout), ClickBench's MongoDB entry (analytical queries, not mutation
cost or index freshness), and any vendor-published figures — each with its URL and one
sentence on why it does not answer the question these campaigns asked. **Invent nothing: list
only sources actually opened.** The honest framing against Jepsen is "different question,
weaker apparatus", since the dossier already concedes both isolation and concurrency; the
section must not imply endorsement by any cited party.

**Impact** medium · **Effort** hours · **Risk** citing Jepsen alongside this work invites a
comparison of rigour the dossier loses on isolation and concurrency — which is why the framing
has to be explicit · **Locked path** yes, `docs/` and README.

### 20. Publish the referenced-but-unobtainable evidence archive, or say plainly it will not be

**Why a sceptical reader gains.** `data/README.md` and `probes/README.md` both reference
`verif-storage-20260917/raw_evidence.tar.gz`, an archive that exists outside the repository and
that a reader cannot obtain. A referenced-but-unobtainable archive is a hole a hostile reader
will find, and it sits next to the sole record of a figure RESULTS.md M3 quotes.

**What to do.** Either attach it to the `v1.0.0` release after checking it contains nothing
beyond what `data/raw/` already publishes and nothing sensitive, or add a data-availability
statement (locked, rank 22) saying explicitly that those 13 files are not published, naming
them, and giving a contact route for requests. Either is defensible; silence is not.

**Impact** medium · **Effort** hours, requires access to the archive · **Risk** an unreviewed
tarball may contain host identifiers or credentials from the lab · **Locked path** no for the
release asset; yes for the statement.

### 21. A reproduction register that outsiders' numbers can enter

**Why a sceptical reader gains.** The README says corrections and reproductions "are the point
of publishing" and provides no row, no column and no file where a disagreeing measurement would
go. The gnn-comparison repository's own comparison table became the place where other people's
numbers landed, which is a far stronger invitation than a sentence. The repository already knows
which rows are weakest — campaign 7 sits outside the adversarial audit and no figure in it has
been challenged — and those are exactly the rows an outsider could strengthen.

**What to do.** Add an "Independent reproductions" column to the RESULTS.md §2 headline table,
seeded `none to date` on every row, and a short §7 holding one entry per outside report: who,
which build strings, which host, which Mxx, their numbers, their raw output, and whether the
author accepts the correction. **This requires an actual outside reproduction to be worth
anything**, and an empty column advertises that nobody has checked the work — which is honest,
and is the same signal the exemplar carried before its rows filled in. Only add it if the author
intends to maintain it; a stale reproduction register is worse than none.

**Impact** medium · **Effort** hours, plus an external event · **Risk** as above ·
**Locked path** yes, RESULTS.md.

---

## Items touching paths locked by the concurrent workflow

These are recommendations only. Nothing in this list was edited. **Rank 22** below is the
handover: it collects every locked-path change proposed anywhere in this plan, so the owner of
README.md, RESULTS.md, DISCLAIMER.md, CITATION.cff, `docs/` and `data/` has one list to work
from.

### 22a. Correct the `run_at_utc` claim (README.md line 63, DISCLAIMER.md line 18)

See rank 4 for the verified counts, the twelve filenames and the suggested replacement wording.
**This is the highest-priority locked-path item**: it is factually false today, it sits in the
provenance claim, and rank 16 must not freeze it into a permanent DOI.

### 22b. Break up the headline table

README.md lines 77–83 are single table rows of 1 110 / 534 / 1 456 / 490 / 1 592 / 1 532 / 1 479
characters, with caveat cells of 269–1 135 characters against axis labels of 80–148. GitHub wraps
README tables in a horizontal scroll container, so a six-column row whose sixth cell is 1 135
characters renders as a narrow column of roughly forty wrapped lines beside five squeezed slivers;
on a ~380 px phone the seven-row table becomes several hundred lines of vertical scroll with axis
names broken one or two words per line. The caveats are the best writing in the repository and
they are the part a reader skips, because at that density the eye bounces — so in practice the
hurried reader copies the margin out of the narrow Margin column and never reads the wall beside
it, which is the precise failure the design was built to prevent. The table's own banner says a
margin quoted without the caveat is a misquote; the layout is working against the instruction.

Two options, and they are not equivalent. **Preferred:** keep the caveat *inside the margin cell*
but reduced to its disqualifying clause in bold — "44×–79× as stacks, 40×–72× engine-to-engine —
**memtable rate only; the coefficient collapses ×5.94 → ×1.52 once the RMW read is forced onto
SSTables**" — so the killer clause is physically inside the string a reader copies, and move the
full reserve to a `### ` block directly beneath the table. **Weaker:** keep the table to
Axis / MongoDB / HCD / Winner / Margin / Note with the last column carrying only a marker, and
move each caveat verbatim below as a numbered note. The second is easier to skip. Either way, no
text is lost and none is softened, every raw-file link survives in the moved prose, and the bolded
banner stays directly above the table. **The preferred option is only a net gain if the in-cell
bold disqualifier is genuinely non-negotiable** — if it gets trimmed to save table width in a later
editing pass, the current design is better.

### 22c. Add a "three doors" routing block and surface the quoting rules early

There is no next click for any of the three reader types: the refuter, the reproducer and the
decision-maker all land in the same opening paragraph and then a 19-row file index. Worse, the
eight quoting rules — the document's actual defence against misquotation — are named for the first
time in the last five lines of a 180-line file, and a reader who quotes badly has almost certainly
stopped before then. Insert after the headline block, before `## What this is`, three declarative
doors: *You want to refute this* → LIMITATIONS.md, then `data/raw/`; *You want to reproduce it* →
REPRODUCING.md, which says on its first page that you will not reproduce these numbers and are not
supposed to; *You want the conclusion and intend to quote it* → the table, then the eight quoting
rules. Keep the door labels as full declarative sentences rather than verb-phrase calls to action
("You want to refute this", not "Get started") — that is what stops a bulleted routing block
reading as a product launch. Also extend the banner above the table to link the quoting rules
directly.

### 22d. Break the 170-word opening paragraph into three

The first block after the rule is 1 051 characters, 170 words and seven parenthetical asides, one
nested two deep. The claim it opens with is the right claim in the right place, but a reader must
parse the whole block to extract it. Split at the existing sentence boundaries into: the
five-two-three verdict; MongoDB's five; the aggregation caveat promoted to its own sentence; HCD's
two. Three sentences must survive verbatim: the five-two-three verdict, "a tier gap", and "the one
comparison in the dossier whose two samples overlap".

### 22e. State the language split, and that no finding is French-only

An anglophone currently learns the split only by noticing "in French" on rows 12, 14 and 15 of the
file index, and has no way to know whether the French material contains findings the English
material does not — the worst possible ambiguity for a repository whose value is that a sceptic can
check it. It is also needlessly pessimistic: every French document (seven campaign narratives, the
adversarial audit, the challenge register) opens with a 359–474-word English abstract carrying its
method, its headline and the results that went against the author. Add two lines to the headline
block saying so. Phrase it as "every French document in this repository opens with an English
abstract" rather than "no finding is French-only", so the claim stays checkable if a document is
added later — and note that `docs/challenges-campagne7.fr.md`, added today, should be checked
against it.

### 22f. Disambiguate "concurrency" in the H1

The H1 promises "write cost, index freshness and concurrency"; line 28 says every figure is "with
no concurrency"; RESULTS.md §6 opens its never-measured table with "**Concurrency** | Never
measured. Every probe in every campaign is a single sequential closed-loop client." The word is
doing two jobs — the concurrency-control *mechanism* (the Paxos-guarded conditional, measured, and
the core finding) and concurrent *load* (never measured). A hostile reader who notices the collision
before the explanation reads it as the document overselling itself in its own title. Prefer adding
one clause to the version subtitle over dropping the word from the H1, since the H1 tracks the
article under verification and is matched by CITATION.cff and the citation block.

### 22g. Reconcile the undeclared-field row with RESULTS.md §2

The README sends the reader to RESULTS.md §2 for "the full table", but on the undeclared-field axis
the README gives Winner = "HCD, at the median only", the honest interval [0.46×, 65.8×] containing
1.0, and a 1 135-character caveat explaining the overlap — while RESULTS.md §2 gives Winner = "HCD",
Margin = "21.7×", and a 269-character caveat that never mentions it. A sceptic who follows the
pointer to the authoritative table finds a *weaker* hedge than the summary they just left, on the
single axis where HCD wins. That inversion makes the strongest caveat look like something the
summary added rather than something the register established. Bring §2 up to the README's rigour;
the register should not be the weaker document. Changing the published verdict to "HCD, at the
median only" also touches the five-two-three count's meaning at the margin, so check the §1 summary
sentence in the same pass.

### 22h. Trim the two paragraph-length cells in "At a glance"

The Measurements cell is 429 characters and contains a three-clause argument about M9 never being
assigned and M20–M23 never reaching the ADR; the Host cell is 233. A reader scanning for "which
versions, which host, how many runs" must read a paragraph about register bookkeeping to reach the
number 23. Reduce both to the fact plus a pointer — but the two load-bearing host facts (**shared,
load average 14–16 throughout; no root, so the OS page cache was never dropped**) must stay in the
cell, because they are the reason every absolute in the dossier is a noisy ceiling.

### 22i. A short section on what CI proves and, at greater length, what it cannot

If rank 9 lands, this is not optional. The dossier's method is that every figure travels with its
reserve; a green check that travels without one contradicts the method. State that CI verifies
(i) no file under `data/raw/` has been modified or deleted since publication, (ii) the ratios and
p50 figures quoted in the prose recompute from those files, (iii) the declared probe patches changed
no numeric constant, (iv) every relative link and anchor resolves, (v) the M/I/C/D registers are
complete — and that it checks **none of the measurements**, because they require a live HCD ring and
a MongoDB replica set on a loaded 80-vCPU host and the regime is the finding. Two specific non-claims
belong here: the immutability check proves the bytes have not changed since they entered git, not
that they match what the probe wrote; and the `probe_tier_vs_storage.py.orig` diff is true by
construction. **If a badge is added, put it beside this paragraph, not at the top of the file**, so
it is never read alone.

### 22j. A data-availability statement, including what is *not* available

Journals and institutional repositories look for this as a named section before they look at any
number. This repository can write an unusually strong one and, because it already discloses its own
gaps, an unusually credible one: data under CC BY 4.0 at the concept DOI, probe source under
Apache-2.0, the Zenodo deposition as the version of record and this repository as the development
copy. Then the negative half, all drawn from facts the repository already states: 13 files of the
original run's evidence are held in an archive outside this repository and are not published
(including `control_read_B.json`, the sole record of a figure M3 quotes); the per-observation series
behind the undeclared-field comparison were not retained, so no statistical test is possible; the
environment cannot be reconstructed byte-for-byte because the host was shared and under unrelated
load. Give a contact route. Do not restate conclusions — RESULTS.md does that better.

### 22k. Complete and reconcile CITATION.cff

The file validates cleanly against the real CFF 1.2.0 schema today, but it is thin: no `version`,
`doi`, `identifiers`, `commit`, `url`, `orcid` or `contact`. Add them once rank 16 produces a DOI —
the concept DOI as the citable identifier, the version DOI under `identifiers` with a `description`
saying which release it pins, the tagged SHA under `commit`, the Zenodo landing page under `url`
(distinct from `repository-code`), and a `contact:` block, since a reader with a serious objection
currently has one channel and no way to reach the author off the tracker. Add `orcid:` only if the
author supplies one — **do not guess; an incorrect ORCID attributes the work to a real stranger.**

On the licence mismatch: GitHub's sidebar reports Apache-2.0 (from `LICENSE`, since `LICENSE-docs`
is not a filename the detector recognises), CITATION.cff declares `CC-BY-4.0`, and the README
correctly describes a split by path. **Do not fix this with a licence array**: CFF 1.2.0's own schema
comment on that branch reads "When there are multiple licenses, it is assumed their relationship is
OR, not AND", which is not what this repository means — the split is by path, not a choice offered to
the user. Keep the single `license: CC-BY-4.0` (correct for a record typed `dataset`) and state the
Apache-2.0 carve-out for `probes/` in the `message:` field, where a human reads it. `license-url:` is
documented as being for non-standard licences absent from the SPDX list and is redundant here. Keep
the existing `message:` instruction to cite the Mxx identifier — it is the best thing in the file.

### 22l. Rewrite the "Cite this" block around the DOI

Once rank 16 lands, the DOI becomes the identifier and the GitHub URL becomes secondary. GitHub's
"Cite this repository" sidebar renders APA and BibTeX from CITATION.cff and does use the DOI field,
so the write-back reaches every reader of the landing page without them knowing what CFF is.
**Never add a placeholder DOI**: an invented identifier in a repository whose whole argument is
evidentiary discipline would be the most damaging possible error.

### 22m. Embed the two figures, and link ERRATA.md

Rank 12's `regime-collapse.svg` goes high in README.md, immediately after the paragraph on the
×7.50 collapse; `separation-of-support.svg` goes in RESULTS.md §2 beside the undeclared-field row.
`ERRATA.md` (rank 14) needs one line from the README "Honesty statement" and one from the
DISCLAIMER "Reporting an error" section.

---

## REJECTED

Saying no explicitly is part of the plan. Each of these was proposed by at least one reviewer.

**Status and build badges at the top of the README.** A badge that asserts nothing is decoration,
and decoration is the specific failure mode for a repository whose value is that it does not look
like a product launch. The one exception is a DOI badge, which is infrastructure — and even that
belongs beside the CI-honesty paragraph (22i), not above the H1.

**`CODE_OF_CONDUCT.md` / Contributor Covenant.** Cargo cult on a single-author dataset with no
community. Two paragraphs of house rules in CONTRIBUTING.md (rank 13 §6) do the actual work, in the
repository's own register, and say the thing a generic covenant cannot: that hostility to *claims*
is welcome here.

**A generic `SECURITY.md` with a disclosure policy and a supported-versions table.** There is no
deployed service, no published package and no dependency surface anyone installs. A vulnerability
policy invites people to expect a process the author has no intention of running. The one real
safety issue — the deliberately insecure lab credentials in REPRODUCING.md and `env/` — is folded
into CONTRIBUTING.md §5 instead.

**A `CONTRIBUTING.md` describing a fork-branch-PR flow.** There is no build, no test suite to
extend, no roadmap, and the likely contribution is not code. Rank 13 keeps the file and throws away
the boilerplate.

**`.zenodo.json`.** Zenodo's own documentation states that when both files are present, only the
`.zenodo.json` metadata is used for GitHub release archiving and the CITATION.cff metadata is
ignored. Adding it would silently discard the CITATION.cff work.

**Removing or documenting the two tracked `.orig` files.** One reviewer read them as editor debris
and another as undocumented evidence. Both are wrong: verified, `probes/README.md` lines 40, 41 and
46 document each one explicitly, including the unusually honest note that
`probe_tier_vs_storage.py.orig` was reconstructed during the documentation pass, that its mtime
(10:03) is later than the patched probe it supposedly predates (09:35), and that it is "a convenience
for reading the diff, not independent evidence". No action needed. This is an example of the register
doing its job.

**GitHub Discussions.** A second free-form venue fragments the record exactly as the wiki does. The
issue forms plus `blank_issues_enabled: true` already give unstructured objections a home.

**REUSE/SPDX headers in the probe sources.** The mapping file is defensible; the headers are not.
`probes/README.md` tabulates file mtimes as evidence — the `.orig` reconstruction argument turns on
one — and editing every instrument to add a comment line touches the objects whose provenance is
being argued about. If the split licence needs to be machine-readable, put it in `REUSE.toml` and
leave the instruments alone.

**matplotlib in `env/requirements.txt`.** That file is pinned to what actually ran during the
campaign and adding a plotting library would destroy that meaning. Rank 12 emits SVG from the
standard library.

**A blocking external link check.** Third-party link rot is not the author's defect and a red X for
it devalues the ticks that mean something. Rank 10 makes it weekly and non-blocking.

**`pip install -r env/requirements.txt` as a blocking gate.** It will eventually fail for reasons
entirely outside the author's control — an upstream yank, a transitive pin. Advisory only.

**A CI check asserting `run_at_utc` in every raw file.** Two reviewers proposed it. It is false for
twelve of thirty-six files today, so it would fail on day one and be deleted on day two. Rank 9's
`fingerprint-coverage` job reports the coverage and ratchets it instead.

**Extending the internal link checker to backticked filenames.** Nine JSON names in `data/README.md`
and `probes/README.md` are deliberately declared as living in the evidence snapshot archive rather
than in `data/raw/`. A naive existence check over backticks reports nine false positives and trains
the author to ignore the job.

**`--help` smoke runs of the probes in CI.** Ten of sixteen use argparse and six do not; a partial
smoke test that passes for ten invites the reading that all sixteen were exercised.

**Auto-filed issues from the link-rot job.** Noise on a tracker that exists to receive real
objections from real people.

**`type:` in the issue forms.** It resolves against organization-level issue types; this is a
user-owned repository and it would simply not work.

**A licence array in CITATION.cff.** CFF 1.2.0 assigns OR semantics to multiple licences, which is
not what a by-path split means. See 22k.

**A homepage pointing at the published article.** The homepage field should carry the DOI once one
exists, or stay empty. Pointing it at the article being verified inverts the relationship: this
repository is the check on that article, not its landing page.

**Disabling Projects.** Proposed alongside the wiki, but C3–C9, C11–C15 and D2–D5 are unresolved and
a board is a plausible place to track them. Ask the author; do not disable unilaterally.

**Creating a thin `docs/STATISTICS.md` stub.** Moot as of 11:00 today — the concurrent workflow
committed a 66 KB file. It was the right call to leave it: a stub would have been worse than the
404, because a reader would then find an empty promise rather than a missing one.

---

## Sequencing

1. Rank 1 (verify `docs/STATISTICS.md` is committed) → ranks 2, 3, 5, 8 in any order (pure
   GitHub-side metadata, no file conflicts).
2. Rank 4 handed to the owner of README.md and DISCLAIMER.md; everything in rank 22 follows it.
3. Ranks 6, 7, 13, 14 (contribution surface) — independent of the concurrent workflow.
4. Ranks 11, 12, 15 (tooling, figures, manifest) — these produce what rank 9 checks.
5. Rank 9, then rank 10. **Run every job locally and confirm green before the first push**, then
   rank 22i so the ticks never travel without their scope.
6. Only after the concurrent workflow lands *and* rank 4 is corrected: ranks 16, 17, then 22k, 22l.
   A DOI freezes whatever is true at that moment, permanently.
