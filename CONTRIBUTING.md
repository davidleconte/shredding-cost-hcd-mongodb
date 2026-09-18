# Contributing

**The most valuable thing you can send this repository is a refutation.**

Not a feature, not a tidy-up, not a badge. A failed reproduction, a counter-measurement, a number
that is wrong, a citation that does not check out, or an argument that a stated claim over-reaches
its evidence. This dossier was built to be able to prove its own author wrong, and
[RESULTS.md §4](RESULTS.md#4-where-the-dossier-proved-its-own-author-wrong) records **52 numbered
points** at which it did exactly that — against an article the same author wrote. A correction from
outside is the same thing arriving by a better route.

There is no roadmap, no build and no test suite to extend. Do not open an issue asking what needs
doing. Open one saying what is wrong.

---

## 1. What counts as a contribution

| Kind | Use |
|---|---|
| You ran a probe and got a materially different number | issue form *A reproduction that differs* |
| A published claim is wrong, or claims more than its evidence supports | issue form *Challenge a claim* |
| A raw file, a link, a licence, a citation or a quotation of this work is defective | issue form *Evidence or citation defect* |
| A defect in the probe code itself | issue form *Evidence or citation defect*, or a pull request |
| Something none of those fit | a blank issue; blank issues are deliberately left enabled |

The sixteen axes in [RESULTS.md §6](RESULTS.md#6-axes-never-measured) were never measured at all —
concurrency, offered-rate load, multi-host topology, a genuinely disk-bound read, sharded MongoDB,
production Atlas. Measuring one of them is the single largest contribution available. It does not
correct this dossier; it does what this dossier could not.

## 2. The evidence bar

This is not a higher bar than the dossier holds itself to. It is
[METHODOLOGY.md §6](METHODOLOGY.md#6-statistical-policy-and-what-was-not-done) and
[§9](METHODOLOGY.md#9-how-to-quote-a-number-from-this-repository) restated as a filing checklist.

1. **Name the measurement.** M1–M23 (there is no M9). A correction that does not say which
   measurement it corrects cannot be adjudicated against anything.
2. **Name the regime.** Memtable- or cache-resident, proven disk-bound, or unknown. Almost every
   latency figure here is the first. The headline growth factor moves ×7.50 → ×5.94 → ×1.52 across
   the three regimes; a rate quoted without its regime is not a number, and neither is a
   counter-rate.
3. **Report a distribution, not a median.** Give `n`, `min`, `p50`, `p95` and `max` at minimum, and
   the raw sample vector if you have it. A median alone cannot settle a comparison here: campaign 1
   measured the same configuration twice and got ×1.92 and ×2.21 — a spread of the same order as
   effects claimed elsewhere in the corpus (audit finding I7). Two medians that differ prove
   nothing until their supports are shown not to overlap.
4. **No means for latency.** This dossier publishes none, by construction, and will not accept one
   as a counter-figure. The exception it did allow — the three freshness files that carry `mean_ms`
   — is declared in METHODOLOGY.md §6 rather than hidden, and is not a precedent.
5. **Fingerprint the host.** CPU model and count, RAM, kernel, virtualisation, load average during
   the run, and whether you could drop the page cache. Ours: one shared QEMU VM, Xeon Gold 6148,
   80 vCPU, 220 GiB, load average 14–16 throughout, no root, so the page cache was **never**
   dropped. If yours was quiet and isolated, say so — that is a finding in itself.
6. **Give both build strings.** `nodetool version`, the Data API image tag, MongoDB `db.version()`,
   the mongot edition if search is involved, and the pymongo/astrapy versions. `localDev` mongot and
   Atlas production search are not the same product, and neither are HCD's Data API and CQL paths.
7. **Attach the raw output.** The JSON your probe wrote, not a screenshot and not a retyped table.

If you cannot meet all seven, file anyway and say which ones you could not meet. A partial
reproduction that is honest about its gaps is worth more than a complete one that is not. What will
be sent back for more is a bare ratio with no regime, no `n` and no host.

## 3. What happens to a correction

This section is a commitment, not an aspiration.

- **A correction that overturns a finding is merged and credited, not argued down.** It becomes a
  numbered entry in [RESULTS.md §4](RESULTS.md#4-where-the-dossier-proved-its-own-author-wrong) or a
  new Cxx in the challenge register, naming the person who found it. The register already contains
  measured resolutions the author wrote against himself (C1, C2, C10, D1); an external one is
  recorded the same way and is not marked differently for having come from outside.
- **A correction the author cannot reproduce is recorded as open, not closed.** It gets the
  `open-unresolved` outcome and stays visible. "I could not reproduce your refutation" is not a
  refutation of your refutation.
- **Nothing already published is quietly rewritten.** A correction that lands after publication is
  logged with its date, its scope, and whether the conclusions move. The refuted text stays where it
  is, with the correction beside it — which is how campaign 6 was amended on 18 September 2026:
  three additive changes, nothing deleted, nothing reworded.
- **Vendor advocacy without a measurement attached is closed, in either direction.** The author is
  an IBM employee publishing a result unfavourable to the IBM product on most of the axes measured.
  The tracker is not a venue for relitigating that, from either side.

## 4. Raw evidence is append-only

**No file under `data/raw/` is ever edited or deleted.** Not to fix a typo, not to add the missing
`run_at_utc` to the twelve files that lack one, not to correct a figure a later run disproved.

`findings_mongot_freshness.json` still reads `p50_ms: 1015.201` even though
`findings_mongot_floor.json` later established that this was the worst phase of a refresh cycle and
the true p50 is 664.3 ms. Both files are published. The refuted one is not amended and not
withdrawn, because the only thing that makes the dataset worth more than a table in a blog post is
that you can check it against the run instead of against the author's later opinion of the run. A
contributor normalising those twelve files would be destroying the property the whole corpus rests
on while sincerely believing they were helping.

A later measurement is published **alongside** the file it refutes, never in place of it. New
evidence is added as new files.

## 5. Pull requests

Accepted for: probe code, `env/`, typos, prose, broken links, and new derived artefacts that carry
their own generator.

Refused for: anything under `data/raw/`. If your pull request needs a raw file to change, the
correct form is a new file plus an issue explaining what the old one got wrong.

One PR, one subject. If a PR changes a number anywhere in the prose, the description must state the
regime, the `n` and the percentile that number came from.

## 6. Lab safety

The reproduction instructions stand up **deliberately insecure** services, because they are written
for a disposable single-host lab:

- [REPRODUCING.md §2.1](REPRODUCING.md#21-the-data-api-token) uses the Data API token
  `Cassandra:Y2Fzc2FuZHJh:Y2Fzc2FuZHJh` — that is base64 `cassandra` / `cassandra`, the stock
  credentials.
- `env/docker-compose.mongodb-rs.yml` brings up a replica set with **no authentication at all**.

Both are correct for a throwaway VM and dangerous anywhere reachable. Do not run them on a host with
an open security group, a public IP, or any network you do not control. Change the token before you
do anything else if you intend to keep the ring.

The probes also **drop and recreate keyspaces, collections and indexes**, and one of them raises
trace probability on live nodes. Do not point them at a ring anyone else is using without reading
[REPRODUCING.md §6](REPRODUCING.md#6-leaving-the-ring-as-you-found-it), which gives the restoration
procedure and records the one residue the original campaigns could not clear.

## 7. House rules

Hostility to claims is the point of this repository. Say a number is wrong, say a verdict does not
follow from its evidence, say the whole comparison is skewed — challenge C9 already says the axes
themselves lean toward HCD's expected weakness, and the audit says the measurer wrote most of the
instruments carrying the decisive verdicts. None of that is off limits; all of it is already in
[LIMITATIONS.md](LIMITATIONS.md), written by the author against himself.

Hostility to people is not the point, and will be moderated without discussion. The distinction is
not subtle: address the measurement.

## 8. Licences

| What you contribute | Licence it is accepted under |
|---|---|
| Code under `probes/` | Apache-2.0 ([`LICENSE`](LICENSE)) |
| Prose, documentation, data under `docs/` and `data/`, root Markdown | CC BY 4.0 ([`LICENSE-docs`](LICENSE-docs)) |

By opening a pull request you agree your contribution is licensed on those terms. If you attach raw
measurement output to an issue, say whether it may be redistributed under CC BY 4.0; if you do not
say, it will be treated as illustrative and will not be committed to `data/`.

---

Before filing, read [LIMITATIONS.md §1](LIMITATIONS.md#1-read-this-before-quoting-any-number-from-this-repository)
and the eight
[reading rules](RESULTS.md#reading-rules-for-anyone-quoting-this-dossier). Several objections a
first-time reader will want to raise are already there, conceded, with the measurement that concedes
them.
