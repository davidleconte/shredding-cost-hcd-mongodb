# Disclaimer

**Personal research.** This repository is personal technical research by David Leconte. It is
not a statement, a position, an endorsement or a publication of his employer, of IBM, of
DataStax, or of MongoDB Inc., and it must not be read as one. The opinions, the method and the
errors are the author's alone.

## What was actually measured

One build of each engine, on one shared laboratory host, over two days in September 2026.

| | Build / configuration measured | Source file |
|---|---|---|
| HCD | IBM DataStax HCD 2.0.6, release string `5.0.7.0-ea50e91ba01f` read from the running node; Data API `stargateio/data-api` v1.0.33 | `data/raw/findings.json` |
| MongoDB — mutation, point read, filtered search | MongoDB 8.0.32, replica set `rs0`, three members, `w:majority` | `data/raw/cmp_mongo.json` |
| MongoDB — search freshness | MongoDB 8.3.11, image `mongodb/mongodb-atlas-local`, single-node replica set | `data/raw/findings_mongot_freshness.json` |
| Host | QEMU virtual machine `alphadebunker`, 80 vCPU Intel Xeon Gold 6148 @ 2.40 GHz, 220 GiB RAM, carrying unrelated workloads throughout | `data/raw/findings.json`, `data/raw/cmp_hcd.json` |
| Dates | 17–18 September 2026. **Not every run is stamped**: `run_at_utc` is present in 26 of the 38 raw files, and one of those 26 is hand-typed and incomplete — `findings_vector_rf3.json` records `"2026-09-17T16:5x (p16 ring)"`. For the twelve files carrying no stamp at all, the date rests on the campaign reports, not on the evidence | 26 of the 38 files under `data/raw/`; the twelve exceptions are named in [data/README.md](data/README.md) |

The two MongoDB deployments are not the same deployment. The adversarial audit records that as
finding I8: the comparison is never fully matched (`docs/audit-adversarial.fr.md`).

## Several findings are properties of a default configuration, not of a product

Engine behaviour changes between versions, and a default is not a design. One example, with its
caveat in the same breath as the number, which is the rule throughout this dossier:

- MongoDB `$search` was measured at p50 **1015.201 ms** write-to-visible
  (`data/raw/findings_mongot_freshness.json`). That figure must never be quoted on its own: the
  author's own follow-up established it as the worst phase of a periodic refresh interval on
  `atlas-local` at idle — de-synchronised p50 **664.3 ms**, floor **89.1 ms**, max **1170.2 ms**
  (`data/raw/findings_mongot_floor.json`).
- The symmetrical caveat applies to HCD. "Synchronous, zero lag" was measured as p50
  **44.972 ms** with a median of **1** poll attempt (`data/raw/findings_hcd_vec_freshness.json`).
  That bounds the lag below the probe's HTTP round-trip floor; it does not prove it is zero.

## This is not a benchmark, a product comparison, or advice

Nothing here is a general-purpose benchmark, a comparison fit for procurement, or a
recommendation to choose one engine over the other. The axes measured were chosen to test
specific claims in one article, and that selection is itself a bias.

Campaigns 1 to 5 measured mutation cost — the axis on which HCD's decomposition is expensive by
design. The dossier's own challenge log states the consequence without softening it: a dossier
that measures only the axis unfavourable to HCD would be as biased as a complacent one
(`docs/challenges.fr.md`, C9). The axis where HCD is structurally strongest, synchronous search
freshness, was not measured until campaign 6, on 18 September 2026 — the last day of the
campaign. That ordering should be read for what it is.

The dossier also fails the standard it applies to other people's benchmarks. The adversarial
audit scores it at roughly 2.5 of the six conditions the article itself demands: the load is
closed-loop rather than driven at a fixed offered rate, the disk regime was reached in one
campaign only, and compaction cycles were crossed in that same campaign only
(`docs/audit-adversarial.fr.md`). That belongs here, not in a footnote, because it bears on
every number in the repository.

## Before citing a number, read LIMITATIONS.md

Every figure here belongs to a regime — memtable or disk, cache-resident or SSTable-bound,
RF 1 or RF 3, Data API tier included or CQL-direct. A number quoted without its regime is a
misquote. When you cite one, cite the measurement identifier (Mxx) alongside the value, so the
conditions travel with it, as `CITATION.cff` asks.

The epistemic markers are part of the claims and should be kept when quoting: **[D]** documented
by the vendor's version-pinned documentation, **[R]** reported publicly by the engineers who
built the system, **[U]** unverified, asserted on structural grounds, and **[M]** measured —
stronger than [U] and weaker than [D], because it establishes what one build did on one day, not
what a vendor commits to.

## Vendor licence terms

Some commercial database licences restrict the publication of benchmark results — so-called
DeWitt clauses. The figures here are published as reproducible research, with the full method,
the probe source and the unedited raw JSON, and with an explicit invitation to correct them.
Anyone republishing them in a commercial or competitive context should check the licence terms
that apply to them; that check is theirs to make, not the author's.

## Reporting an error

Open an issue on the repository. Name the file under `data/raw/`, the measurement identifier and
what you believe is wrong. A correction that overturns a finding is the point of this
repository, not an attack on it: the experiment was built so that it could prove its author
wrong, and in several places it did.
