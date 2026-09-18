# Reproducing this campaign

This document describes how to stand up the two engines, how to point each probe at them, and
which raw record each probe produced. It is written so that a reader can run the same
instruments against their own build and contradict us.

Read it with one thing in mind, stated here rather than at the end:

> **You will not reproduce our numbers, and you are not supposed to.** The campaign ran on one
> shared laboratory host that no longer exists in that state. The dossier's own adversarial
> audit records this as finding I1: a single host (`alphadebunker`, a QEMU virtual machine)
> carrying a production-demo ring with Presto, streaming and Jupyter on it, at a load average of
> 14–16 throughout; state that mutated between campaigns, with `system.paxos` growing from 0 to
> roughly 13 GiB per dc1 node and the 20 `supply_chain_hcd` SAI indexes dropped and recreated six
> times (`docs/audit-adversarial.fr.md`). What is reproducible is the **mechanism** — the
> shredded row, the read-modify-write cycle, the Paxos round, the index budget, the refusal of
> indexed strings above 8 000 bytes, the absence of a server-side aggregation pipeline — and the
> **direction** of each result. The magnitudes belong to that machine on those two days.
>
> Before quoting any figure produced by these instruments, read **[LIMITATIONS.md](LIMITATIONS.md)**
> and the final section of this file, *Why your numbers will differ from ours*.

Epistemic markers used below are the dossier's own: **[D]** documented by the vendor, **[R]**
reported publicly by the engineers who built the system, **[U]** unverified and asserted on
structural grounds, **[M]** measured on one build under stated conditions.

---

## 1. Prerequisites

**Step zero, before anything is installed: check that the evidence you are about to compare
against has not been altered.**

```bash
sha256sum -c data/MANIFEST.sha256      # from the repository root
```

Thirty-eight lines, every one `OK`. The manifest's paths are relative to the repository root,
so run it from there — from inside `data/` it reports every file as *No such file or
directory*, which looks like corruption and is not. This is the one check in this document
that needs neither Python, nor a container, nor a network, and it is the one that makes every
other number here quotable.

| | What the campaign used | Where it is recorded |
|---|---|---|
| Host | QEMU virtual machine, 80 vCPU Intel Xeon Gold 6148 @ 2.40 GHz, 220 GiB RAM | `data/raw/cmp_mongo.json` → `conditions.host` |
| OS | Linux 6.8.0-136-generic, glibc 2.39 | `data/raw/cmp_mongo.json` → `conditions.host.platform` |
| Python | 3.12.3 | `data/raw/cmp_mongo.json` → `conditions.python` |
| Container runtime | Docker | `docs/campaigns/05-mutation-comparison.fr.md` |
| Packages | astrapy 2.3.1, cassandra-driver 3.30.1, pymongo (version not recorded) | `env/requirements.txt`, `docs/campaigns/01-verification.fr.md` |

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r env/requirements.txt
```

Two prerequisites that are worth deciding before you start, because the campaign got both wrong
and said so:

- **Root on the host.** The campaign had none. The operating-system page cache could therefore
  never be dropped, which is why every run described as "disk-bound" is qualified as
  *dataset on disk, reads still possibly served from RAM below the database*
  (`data/raw/disk_state.json` → `evidence.page_cache_note`). If you have root, drop the page
  cache and you will measure something the campaign could not.
- **A ring you own.** The HCD side ran on a shared ring. That forced index-budget surgery on
  unrelated keyspaces (section 4.1) and left a `system.paxos` residue that later campaigns ran
  on top of. A dedicated ring removes a confound the campaign could only name.

**Working directory.** Every probe writes its JSON into the current directory. `data/raw/` is
untouched evidence, byte-identical to the run; do not run probes from inside it. Run them from a
scratch directory and compare afterwards.

---

## 2. Environment variables

Every variable the probes read, recovered from the probe sources.

| Variable | Read by | Value used in the campaign |
|---|---|---|
| `DATA_API_ENDPOINT` | every HCD probe | `http://127.0.0.1:8181` (campaign 1, `data/raw/findings.json` → `conditions.endpoint`); `http://127.0.0.1:8182` (campaigns 3–4, `data/raw/findings_fieldbyte.json`, `data/raw/findings_tier.json`) |
| `DATA_API_TOKEN` | every HCD probe | `Cassandra:<base64(user)>:<base64(password)>` — see below |
| `MONGO_URI` | every MongoDB probe | replica set for campaigns 5–7; `mongodb://127.0.0.1:27020/?directConnection=true` is the built-in default of `mongot_freshness.py`, `mongot_floor.py` and `turn_latency.py`, i.e. the `atlas-local` container |
| `CQL_CONTACT_POINT` | `verify_storage_claims*.py`, `probe_tier_vs_storage.py`, `method2_trace.py`, `hcd_cql_arm.py`, `agg_cql_arm.py` | the HCD node reachable from the client |
| `CQL_PORT` | `agg_cql_arm.py` only | that file defaults to `9142`; the other CQL probes build `Cluster([...])` without a port and therefore use the driver default, 9042 |
| `CQL_USER`, `CQL_PASS` | the same CQL probes | `agg_cql_arm.py` defaults both to `cassandra`; the others have no default |
| `AGG_N` | `agg_cql_arm.py` | `200000` (`data/raw/findings_agg_cqlref.json` → `n_loaded`) |
| `AGG_REPS` | `agg_cql_arm.py` | `15` (`data/raw/findings_agg_cqlref.json` → `C3a_per_partition_sweep_10q_ms.n`) |

`CQL_CONTACT_POINT` is optional for `verify_storage_claims.py`: without it, probes 1 and 4 report
`NOT_ATTEMPTED` and the run continues. That degradation is written into the record rather than
silently skipped — which is the behaviour you want from an instrument.

### 2.1 The Data API token

The self-hosted Data API authenticates against the underlying Cassandra credentials, and the
token is the literal string `Cassandra`, the base64 of the username, and the base64 of the
password, joined by colons:

```bash
export DATA_API_TOKEN="Cassandra:$(printf 'cassandra' | base64):$(printf 'cassandra' | base64)"
# -> Cassandra:Y2Fzc2FuZHJh:Y2Fzc2FuZHJh
```

Use `base64 -w0` on GNU coreutils if your input is long enough to wrap. The token is passed
straight to `DataAPIClient(token, environment=Environment.HCD)`; the probes never parse it.

### 2.2 The endpoint has no `/v1` in it

Set `DATA_API_ENDPOINT` to the scheme, host and port only — `http://127.0.0.1:8181`. astrapy
appends the rest. The API's own base URL for a keyspace is
`http://HOST:PORT/v1/<keyspace>`, which is what you will see in a packet capture and what you
should use if you drive the API with `curl` instead of astrapy.

---

## 3. Standing up MongoDB

### 3.1 The three-member replica set (campaigns 5, 6, 7)

`env/docker-compose.mongodb-rs.yml` reconstructs the deployment the evidence describes: MongoDB
8.0.32, replica set `rs0`, three members `mongo1`/`mongo2`/`mongo3`, each limited to 8 GiB and 4
vCPU to match one HCD node, on a Docker network named `cmpnet`
(`data/raw/cmp_mongo.json` → `conditions.TO_BE_COMPLETED_BY_HAND`,
`docs/campaigns/05-mutation-comparison.fr.md`). The original run used `docker run` invocations
rather than a compose file, and the host port mapping is not recorded anywhere in the evidence —
the ports in the compose file are this repository's choice, not a measured fact.

```bash
docker compose -f env/docker-compose.mongodb-rs.yml up -d
```

### 3.2 `rs.initiate`, and the one thing that will bite you

The replica set advertises `host:port` pairs, and the client on the host has to be able to reach
every one of them. Each member therefore listens on a **distinct** port inside its own container
(27017, 27018, 27019), published 1:1, and the host resolves the three member names to loopback:

```bash
# once, as root on the client host
printf '127.0.0.1 mongo1 mongo2 mongo3\n' | sudo tee -a /etc/hosts
```

```bash
docker exec -it mongo1 mongosh --port 27017 --eval '
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "mongo1:27017" },
    { _id: 1, host: "mongo2:27018" },
    { _id: 2, host: "mongo3:27019" }
  ]
})'
```

Wait for a primary, then confirm that the majority is real — two of three live members, not the
trivial single-member case that would make `w:majority` free:

```bash
docker exec -it mongo1 mongosh --port 27017 --quiet --eval '
  rs.status().members.map(m => m.name + " " + m.stateStr)'
```

```bash
export MONGO_URI="mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0"
```

### 3.3 Durability: `w:majority` + `j:true`

Do not set these on the URI. Every MongoDB probe sets them itself, per collection, with
`WriteConcern(w="majority", j=True)`, so the durability setting travels in the same file as the
number that depends on it. Verify from the client rather than assuming:

```bash
python3 - <<'PY'
import os
from pymongo import MongoClient
c = MongoClient(os.environ["MONGO_URI"]); c.admin.command("ping")
print(c.admin.command("replSetGetStatus")["myState"], "1 = PRIMARY")
print(c.admin.command({"getDefaultRWConcern": 1}))
PY
```

One caveat belongs here rather than in a footnote, because it decides how the comparison should
be read: MongoDB at `j:true` waits for the journal fsync **before** acknowledging, while HCD ran
at `commitlog_sync periodic` with a 10 000 ms period and acknowledges **before** the fsync
(`docs/campaigns/01-verification.fr.md`). The matching is a declared judgement, and it favours
HCD — the dossier's own challenge log states that this makes MongoDB's win on the mutation axis
more robust, not less (`docs/challenges.fr.md`, C6).

### 3.4 The `mongot` deployment is a different deployment (campaign 6 addendum)

`$search` needs `mongot`, which is not deployable on a plain replica set. The campaign used the
official `mongodb/mongodb-atlas-local` image, carrying MongoDB 8.3.11, as a **single-node**
replica set (`docs/campaigns/06-freshness-read-search.fr.md`). The three freshness probes default
to `mongodb://127.0.0.1:27020/?directConnection=true`, so publish that container on 27020, or set
`MONGO_URI` explicitly.

```bash
docker run -d --name atlas-local -p 27020:27017 mongodb/mongodb-atlas-local
export MONGO_URI="mongodb://127.0.0.1:27020/?directConnection=true"
```

This is not the same MongoDB as section 3.1, and the dossier's audit counts that as a defect of
the comparison, finding I8: *two different MongoDB deployments across campaigns 5–6*
(`docs/audit-adversarial.fr.md`). On a single member `w:majority` is trivially satisfied. The
search-lag figures measured here are `atlas-local` defaults at idle, and the refresh interval is
not user-tunable on that image (`docs/challenges.fr.md`, C10).

---

## 4. Standing up HCD 2.0.6 and the Data API

The campaign record fixes the following, and no more:

| | Value | Source |
|---|---|---|
| Database image | `hcd:2.0.6-ubi` (registry prefix not recorded) | `docs/campaigns/01-verification.fr.md` |
| Release string on the running node | `5.0.7.0-ea50e91ba01f`, from `nodetool version` and `system.local` | `docs/campaigns/01-verification.fr.md` |
| Data API image | `stargateio/data-api:v1.0.33` | `docs/campaigns/01-verification.fr.md` |
| Data API memory limit | 2 GiB, no CPU limit, co-located with the nodes | `docs/campaigns/04-tier-vs-storage.fr.md` |
| Published Data API port | 8181 (campaign 1), 8182 (campaigns 3–4) | `data/raw/findings.json`, `data/raw/findings_tier.json` |
| Topology, campaign 1 | one node, `NetworkTopologyStrategy {dc1: 1}`, 16 vnodes, node limited to 3 GiB with a 2 GiB heap | `docs/campaigns/01-verification.fr.md` |
| Topology, campaigns 2–7 | six nodes over two datacentres, probe keyspaces at `{dc1: 3}`, nodes 8 GiB / 4 vCPU, 4 GiB heap, memtable budget 2048 MiB | `docs/campaigns/02-replication-rf3.fr.md`, `docs/campaigns/03-disk-regime.fr.md` |
| Durability | `commitlog_sync periodic`, 10 000 ms, `trickle_fsync true` | `docs/campaigns/01-verification.fr.md` |

**[U] The Data API container's environment is not recorded.** The campaign preserved the image
tag, the published port, the memory limit and the fact that the API answered on `/v1/<keyspace>`
— not the variables it was started with. You will need to give the container, in whatever form
your image spells them, the Cassandra contact points, the local datacentre name, the credentials
and the HTTP port. Take the spellings from the image's own configuration reference, which this
repository's article already cites:
<https://github.com/stargate/data-api/blob/main/CONFIGURATION.md>. Anything this document told
you about those names would be a guess, and a guess in a dossier about verification is worse than
a gap.

Wait for health before running anything:

```bash
curl -fsS http://127.0.0.1:8181/stargate/health
```

Create the keyspace by CQL, explicitly, so the replication factor is a decision and not a
default:

```sql
-- campaign 1, one node
CREATE KEYSPACE verif_stockage_20260917
  WITH replication = {'class':'NetworkTopologyStrategy','dc1':1};

-- campaigns 2 to 7, three replicas in dc1
CREATE KEYSPACE cmp
  WITH replication = {'class':'NetworkTopologyStrategy','dc1':3};
```

### 4.0 The astrapy gotcha that costs an afternoon

Self-hosted HCD serves the Data API under `/v1`. Astra serves it under `/api/json/v1`. astrapy
2.3.1 assumes Astra unless told otherwise, so **every command returns HTTP 404** against a
self-hosted deployment — collection creation, insert, find, all of them, with no hint that the
prefix is the problem.

```python
from astrapy import DataAPIClient
from astrapy.constants import Environment

db = DataAPIClient(token, environment=Environment.HCD).get_database(endpoint, keyspace=ks)
```

This is the first of the campaign's declared mechanical fixes to the supplied harness; it changes
no threshold, no document size and no repetition count
(`probes/verify_storage_claims.py` line 147, `docs/campaigns/01-verification.fr.md` section 0).
`probes/verify_storage_claims.py.orig` is the unmodified upstream harness, kept in the repository
so the diff can be checked rather than believed.

### 4.1 The SAI index budget, which will stop you creating a collection

A collection created with defaults and **no vector option** receives **nine** storage-attached
indexes automatically (`data/raw/findings.json`, measurement M1 — nine SAI on twelve columns,
identical across two passes). The platform's guardrails are
`sai_indexes_per_table_fail_threshold = 10` and `sai_indexes_total_fail_threshold = 100`, and the
second is a ceiling **per node, across all keyspaces** — not per keyspace
(`docs/adr/ADR-001-modelling-policy.md`).

On this build the total threshold is **not tunable at runtime**: `nodetool setguardrailsconfig`
does not know the guardrail, and `system_views.settings` is read-only
(`docs/campaigns/02-replication-rf3.fr.md`). A ring already carrying other tenants can therefore
refuse to create your campaign collection because someone else's indexes filled the budget. That
is exactly what happened: to make room, 20 SAI indexes belonging to an unrelated keyspace
(`supply_chain_hcd`) were **dropped and recreated verbatim** from captured definitions, bringing
the ring back to 101 indexes in total, and that surgery was repeated at every campaign
(`docs/campaigns/02-replication-rf3.fr.md`, and the ring-state section of campaigns 3 to 6).

Count before you start:

```sql
SELECT keyspace_name, table_name, index_name FROM system_schema.indexes;
```

At nine indexes per collection, a node's 100-index budget is about eleven default collections
across every keyspace it hosts. Campaign 1 left its probe keyspace holding 18 SAI indexes of the
100 (`docs/campaigns/01-verification.fr.md`, section 6).

### 4.2 The 8 000-byte indexed-string limit

The Data API refuses any **indexed** string longer than 8 000 bytes. It surfaces as
`SHRED_DOC_LIMIT_VIOLATION` at write time, not at query time: 8 000 bytes was accepted, 8 192
bytes was refused (`docs/adr/ADR-001-modelling-policy.md`). Two related shape limits from the same
shredder, both also `SHRED_DOC_LIMIT_VIOLATION`: nesting depth at most sixteen, and at most one
thousand properties per indexable object (measurement M8, same file).

Three consequences you will meet in this order:

1. **The supplied harness had to be patched.** Probe 3 of `verify_storage_claims.py` carries
   ballast of 8, 32 and 128 KB as a single string, which cannot be indexed. The declared fix adds
   `definition={"indexing": {"deny": ["ballast"]}}` at collection creation. Sizes, mutation, five
   warm-ups, thirty repetitions and the 1.2/1.6 verdict thresholds are unchanged, and the ballast
   still lives in `doc_json` (`probes/verify_storage_claims.py` around line 470,
   `docs/campaigns/01-verification.fr.md`). This is the second mechanical fix.
2. **The obvious experiment does not exist.** The three-arms-at-constant-size design proposed for
   the field-versus-byte question is not executable, because at 128 KB of indexed content the cap
   forces a minimum of 17 fields, which is the reference arm itself. Two series, each holding one
   term fixed, are used instead (`probes/probe_field_vs_byte.py` docstring,
   `data/raw/findings_fieldbyte.json` → `design_note`).
3. **Selective indexing is not optional for large text.** For some payloads, excluding a field
   from indexing is mandatory rather than an optimisation
   (`docs/adr/ADR-001-modelling-policy.md`).

### 4.3 Two more Data API surprises, if you run the aggregation campaign

Both are recorded exactly as the server returned them, in `data/raw/findings_agg_hcd.json`:

- `countDocuments({})` and `countDocuments({cat:"c3"})` both failed with
  `TooManyDocumentsToCountException: Document count exceeds 1000, the maximum allowed by the
  server`, although the probe had asked for `upper_bound = 400000`. The server applies its own
  cap and ignores the client's.
- `estimatedDocumentCount()` answered at p50 6.875 ms and returned **0** while the true count was
  200 000. It is an SSTable-metadata estimate and reads zero until the memtable is flushed; before
  a flush it is not approximate, it is wrong.
- `aggregate`, `$group` and `distinct` return `COMMAND_UNKNOWN` — there is no server-side
  aggregation pipeline on this build (`docs/campaigns/07-aggregation.fr.md`).

### 4.4 Tracing

The consistency-level and Paxos observations need CQL tracing raised on the dc1 replicas and put
back afterwards. `method2_trace.py` does this itself and verifies the reset; for the other runs it
was done by hand:

```bash
for n in p16-hcd-node1 p16-hcd-node2 p16-hcd-node3; do
  docker exec "$n" nodetool settraceprobability 1.0
done
# ... run the probe ...
for n in p16-hcd-node1 p16-hcd-node2 p16-hcd-node3; do
  docker exec "$n" nodetool settraceprobability 0.0
done
```

On a two-datacentre ring there is a third declared mechanical fix, applied only in
`verify_storage_claims_rf3.py`: `system_traces` is `SimpleStrategy RF=2`, so the driver's default
`LOCAL_ONE` read fails with `alive_replicas: 0` for partitions whose two replicas sit in the other
datacentre. The fix sets `session.default_consistency_level = ConsistencyLevel.ONE` in
`connect_cql`. Queries, thresholds and verdict logic are unchanged
(`docs/campaigns/02-replication-rf3.fr.md`).

**Container names are hard-coded.** `method2_trace.py` and `rmw_postflush.py` contain
`DC1 = ["p16-hcd-node1", "p16-hcd-node2", "p16-hcd-node3"]` and shell out to
`docker exec <node> nodetool ...`; `disk_regime_driver.py` reads its SSTable evidence through
`docker exec p16-hcd-node1`. Those names are this laboratory's. Edit them, or name your containers
the same way.

---

## 5. The probes, one by one

All commands are given from the repository root, with the environment of section 2 exported.
Output files are named as they appear in `data/raw/`; the probes write into the current working
directory, so run from a scratch directory.

### Campaign 1 — verifying the article's own [U] claims (one node, RF 1)

| Probe | What it measures | Command | Output JSON |
|---|---|---|---|
| `probes/verify_storage_claims.py` | four probes in one run: the shredded column layout read from `system_schema` (M1); write-to-searchable interval at idle and under load (M2); one-field `$set` cost across document sizes with a same-size read control (M3); consistency levels by CQL trace (M4) | `python3 probes/verify_storage_claims.py --keyspace verif_stockage_20260917 --collection storage_probe_20260917 --rate 50 --duration 120 --out findings.json` | `findings.json` |

`--rate 50 --duration 120` is the offered rate the campaign held, open loop, with a schedule slip
of 0.056 s on pass 1 and 0.055 s on pass 2 (`docs/campaigns/01-verification.fr.md`). The default
in the script is `--duration 60`. Two passes were run against a fixed `--out` name, so the record
on disk is the later one — campaign 1 flags that as a record-keeping fault for its pass-1 read
control, whose values had to be transcribed from the log and are marked as transcribed in
`findings.json`.

### Campaign 2 — the same four probes at RF 3, plus vector freshness

| Probe | What it measures | Command | Output JSON |
|---|---|---|---|
| `probes/verify_storage_claims_rf3.py` | the campaign-1 probes on a `{dc1:3}` keyspace, where `LOCAL_QUORUM` and `LOCAL_SERIAL` are satisfied by two real replicas instead of one | `python3 probes/verify_storage_claims_rf3.py --keyspace verif_rf3_20260917 --collection storage_probe_rf3 --rate 50 --duration 120 --out findings_rf3.json` | `findings_rf3.json`, `findings_rf3_rate50.json`, `findings_rf3_rate50_rep2.json` |
| `probes/vector_freshness_rf3.py` | whether a vector ANN query, which the tier runs at `LOCAL_ONE`, can miss a write acknowledged at `LOCAL_QUORUM`; per cycle it contrasts the vector search against a key read on the same first attempt | idle: `python3 probes/vector_freshness_rf3.py --keyspace verif_vec_20260917 --collection vec_freshness --dim 16 --corpus 200 --cycles 60 --rate 0 --out vector_freshness_idle.json` · loaded: same with `--rate 40 --out vector_freshness_loaded.json` | `vector_freshness_idle.json`, `vector_freshness_loaded.json` |

`data/raw/probe4_rf3_supplementary.json` holds the message-level Paxos evidence for that campaign
— statement counts, coordinators, `PAXOS_COMMIT` event counts per session — assembled from
`system_traces` rather than emitted by a probe file.
`data/raw/findings_vector_rf3.json` is likewise a hand-assembled summary of the two vector runs
above, not a probe output.
`data/raw/control_read_A_run1.json` and `control_read_A_run2.json` are variant-A read controls on
collection `storage_probe_rf3`, 30 repetitions after 5 warm-ups, with the recorded `updateOne` and
`findOne` wire sizes. Campaign 1 notes that its own pass-1 read control was overwritten by pass 2
because the filename was fixed, and marks the transcribed values as such in `findings.json`.

### Campaign 3 — a proven disk regime, and field count versus byte volume

| Probe | What it measures | Command | Output JSON |
|---|---|---|---|
| `probes/disk_regime_driver.py` | nothing: it puts the ring into a disk-bound state and **proves** it — data on disk above the memtable budget, SSTables present, at least one compaction crossed, caches invalidated — then stops | `python3 probes/disk_regime_driver.py --keyspace verif_disk_20260917 --collection disk_fill --data-dir <container data dir> --nodetool ./nodetool-p16 --memtable-budget-mb 2048 --target-multiple 3 --doc-bytes 262144 --out disk_state.json` | `disk_state.json` |
| `probes/probe_field_vs_byte.py` | the decisive separation: series 2 varies field count 9→128 at a fixed 64 KiB of indexed content, series 1 varies 512→8000 bytes per field at a fixed 16 fields; an internal control configuration appears in both series | `python3 probes/probe_field_vs_byte.py --keyspace verif_disk_20260917 --collection fieldbyte_probe --reps 30 --passes 2 --out findings_fieldbyte.json` | `findings_fieldbyte.json` |

`--memtable-budget-mb` is required and has no default on purpose: the script refuses to guess the
number its proof depends on. Read it from the running configuration. `--doc-bytes 262144` is the
256 KiB incompressible ballast document; the value is derivable from the record
(24 576 documents for a 6 442 450 944-byte target, `data/raw/disk_state.json`).
`--nodetool` takes a **single executable**, so a containerised node needs a wrapper:

```bash
cat > ./nodetool-p16 <<'SH'
#!/bin/sh
exec docker exec p16-hcd-node1 nodetool "$@"
SH
chmod +x ./nodetool-p16
```

Run `--dry-run` first: it prints the target and the before-state without writing anything.

The fill must be **incompressible**. The first attempt used constant bytes and the table's LZ4
compressor reduced 6 GiB of logical data to about 50 MiB on disk, so the driver correctly returned
`disk_bound = False` on the `data_exceeds_memtable_budget` check. The declared fix is random
base64, a fresh value per document (`docs/campaigns/03-disk-regime.fr.md`).

What the run produced, as evidence rather than assertion (`data/raw/disk_state.json`): 24 576
documents in 1 137.8 s, 82 SSTables after the flush, 40 after a major compaction, the compaction
counter moving 651 → 729 (78 crossed), 6 491 369 675 bytes in the keyspace directory, caches
invalidated, `disk_bound = True`. Campaign 4 re-ran the same driver on its own keyspace
(`disk_state_c4.json`: 88 SSTables after flush, 40 after compaction, counter 875 → 951, 76
crossed).

`data/raw/findings_disk_rf3.json` is campaign 3's assembled record: the disk proof plus the
variant-A and variant-B read-modify-write repeat measured against that state.

**Read the caveat with the result.** "Disk-bound" here describes the *dataset*, never the *probed
read*. The read-modify-write probe re-reads the row it has just written, which stays
memtable-resident whatever the dataset size, and the page cache could not be dropped. The
dossier's own challenge log calls this C2 and the audit calls it I5; the measurement that closed
it is `rmw_postflush.py` below.

### Campaign 4 — where the cost is charged: stateless tier or stateful engine

| Probe | What it measures | Command | Output JSON |
|---|---|---|---|
| `probes/probe_tier_vs_storage.py` | method 1, bypass: the same mutation through the Data API, then as the identical CQL statement pair against the same row with the shredded values read back rather than recomputed; the difference is the tier | `python3 probes/probe_tier_vs_storage.py --keyspace verif_tier_20260917 --collection tier_probe --reps 30 --passes 2 --out findings_tier.json` | `findings_tier.json` |
| `probes/method2_trace.py` | method 2, trace: client-observed Data API latency minus the coordinator-side duration of the CQL statements the tier issued, read from `system_traces.sessions` | `python3 probes/method2_trace.py --keyspace verif_tier_20260917 --collection tier_probe --reps 30 --out findings_tier_method2.json` | `findings_tier_method2.json` |

`method2_trace.py` deliberately reuses the `tier_probe` collection left by the first probe rather
than creating its own, to stay inside the index budget of section 4.1. It raises tracing to 1.0 on
the dc1 nodes and resets it to 0.0 on exit, verifying the reset.

`data/raw/tier_comparison.json` is the per-size comparison of the two methods, with the
divergence and a `within_25pct` flag per size. **The flag is the finding**: the two methods agree
within 25 % at 8, 16 and 32 KiB and diverge by 34 % at 64 KiB and 27.7 % at 125 KiB, so the
campaign publishes a direction and a range rather than a single split
(`docs/campaigns/04-tier-vs-storage.fr.md`). That range is contested further down the dossier: a
cache-regime HCD-CQL-direct arm put the tier share near 9 % against this campaign's 29 %, and the
adversarial audit records the unreconciled factor of three as finding I3
(`docs/challenges.fr.md`, `docs/audit-adversarial.fr.md`).

### Campaign 5 — HCD against MongoDB on the single-field mutation

| Probe | What it measures | Command | Output JSON |
|---|---|---|---|
| `probes/probe_comparative.py` (MongoDB) | a one-field `$set` over 16 indexed fields of 512→8000 bytes, in two arms: `mongo-default` with nothing indexed on the ballast, and `mongo-wildcard` with a `$**` index that matches HCD's automatic indexing | `python3 probes/probe_comparative.py --engine mongodb --db-name cmpdb --reps 30 --passes 2 --out cmp_mongo.json` | `cmp_mongo.json` |
| `probes/probe_comparative.py` (HCD) | the same series through the Data API, on a collection with the platform's default automatic indexing | `python3 probes/probe_comparative.py --engine hcd --keyspace cmp --collection cmp_probe --reps 30 --passes 2 --out cmp_hcd.json` | `cmp_hcd.json` |
| `probes/probe_comparative.py --compare` | merges records and fits a per-KiB slope; **refuses to emit a ratio** unless every record came from the same host with the same series shape | `python3 probes/probe_comparative.py --compare cmp_mongo.json cmp_hcd.json --out comparison.json` | `comparison.json` |
| `probes/hcd_cql_arm.py` | the same mutation driven straight through the CQL driver — the `SELECT` plus conditional `UPDATE` the tier issues, on the row the tier shredded — so the comparison becomes engine-versus-engine instead of stack-versus-stack | `python3 probes/hcd_cql_arm.py cmp cmp_hcdcql.json` | `cmp_hcdcql.json` |
| `probes/probe_comparative.py --compare` (v2) | the three-way merge including the tier-removed arm | `python3 probes/probe_comparative.py --compare cmp_mongo.json cmp_hcd.json cmp_hcdcql.json --out comparison_v2.json` | `comparison_v2.json` |
| `probes/rmw_postflush.py` | `nodetool flush` on the dc1 nodes **before each timed update**, so the cycle's internal `SELECT` reads from an SSTable instead of the memtable | `python3 probes/rmw_postflush.py cmp rmw_postflush.json` | `rmw_postflush.json` |

`--smoke` runs one pass of five repetitions. It validates that the instrument runs and measures
nothing; the record it writes carries a `publication_note` saying so. The two smoke records in the
repository are `smoke_mongo.json` and `smoke_hcd.json`, and they must never be quoted.

`hcd_cql_arm.py` takes positional arguments — keyspace, then output file — not flags. It is the
measurer's own code, declared as such under challenge C5, and it refuted its author's own
challenge C1: removing the tier moved the per-KiB slope from 0.7775 to 0.7037 ms, a 9 % reduction,
not the 29 % the tier-share estimate had predicted (`data/raw/comparison_v2.json`,
`docs/challenges.fr.md`).

`rmw_postflush.py` is the measurement that qualifies the whole dossier's headline coefficient. Its
declared limitation belongs with its result: flushing before every update creates one small
SSTable per flush, up to about 35 fragments for a `SELECT` to merge, which a normal compaction
would never leave — so its absolute figures are inflated by fragmentation, and the true
disk-bound value sits between the memtable runs and this worst case. And the page cache still
could not be dropped, so "SSTable path" is not "cold platter"
(`docs/challenges.fr.md`, C2 resolution).

### Campaign 6 — the axes the article claims for HCD

| Probe | What it measures | Command | Output JSON |
|---|---|---|---|
| `probes/probe_read_search.py` (MongoDB) | at 1 M documents: filtered read on an undeclared field (collection scan by default, wildcard index in the second arm), point read by `_id`, and write-to-visible on an ordinary secondary index | `python3 probes/probe_read_search.py --engine mongodb --n 1000000 --reps 50 --out findings_rs_mongo.json` | `findings_rs_mongo.json` |
| `probes/probe_read_search.py` (HCD) | the same three axes through the Data API, where every field is automatically covered by SAI | `python3 probes/probe_read_search.py --engine hcd --n 1000000 --reps 50 --keyspace cmp --collection rs_probe --out findings_rs_hcd.json` | `findings_rs_hcd.json` |
| `probes/mongot_freshness.py` | write-to-`$search`-visible lag on `atlas-local`, by polling until the just-written document is returned; contrasted with a synchronous `find({_id})` | `python3 probes/mongot_freshness.py 40` | `findings_mongot_freshness.json` (filename fixed in the script) |
| `probes/mongot_floor.py` | the **true floor** of that lag: a random 0–1200 ms sleep before each insert de-synchronises the probe from the commit cycle, then it polls at 5 ms | `python3 probes/mongot_floor.py 60` | `findings_mongot_floor.json` (filename fixed) |
| `probes/turn_latency.py` | miss rate of a single search issued τ ms after the write, for τ in 0…3000 ms, 30 cycles per τ — does the freshness window survive a realistic RAG turn latency | `python3 probes/turn_latency.py mongodb` then `python3 probes/turn_latency.py hcd` | `findings_turn_mongodb.json`, `findings_turn_hcd.json` |

The positional argument to `mongot_freshness.py` and `mongot_floor.py` is the cycle count; the
defaults are 40 and 60, which are the values in the records.

`data/raw/findings_hcd_vec_freshness.json` is the HCD half of that session — 40 cycles, poll
attempts minimum, median and maximum all 1, p50 44.972 ms. There is **no probe file for it in this
repository**; it was recorded inside the same session as the mongot runs. Treat it accordingly.

Two caveats that must be quoted with these numbers rather than after them. `mongot_freshness.py`
self-synchronises: because each cycle inserts and then immediately polls, every insert lands just
after a commit, and the resulting p50 of 1015.201 ms is the **worst phase** of a periodic cycle.
`mongot_floor.py` corrects it — de-synchronised p50 664.3 ms, minimum 89.1 ms, maximum 1170.2 ms
— an overstatement of his own figure by ×1.53 on the medians (1015.201 → 664.3 ms). ADR-001
rev. 12 records it as "~1.6×", which is the ratio of the `mean_ms` fields (1021.553 / 646.3 =
×1.58) that this dossier does not publish for latency
(`data/raw/findings_mongot_floor.json`, `docs/adr/ADR-001-modelling-policy.md`, M18). Symmetrically,
HCD's "synchronous, no lag" is *lag below the probe's HTTP round-trip floor*: a poll attempt
median of 1 at p50 44.972 ms bounds the window under about 45 ms, it does not prove it is zero
(`docs/challenges.fr.md`, C11).

### Campaign 7 — aggregation

| Probe | What it measures | Command | Output JSON |
|---|---|---|---|
| `probes/probe_aggregation.py` (MongoDB) | count-all, filtered count without and with an index on the group key, and a server-side `$group` with `SUM`, over 200 000 documents in 10 categories; every result checked against a precomputed ground truth | `python3 probes/probe_aggregation.py --engine mongodb --n 200000 --reps 30 --out findings_agg_mongodb.json` | `findings_agg_mongodb.json` |
| `probes/probe_aggregation.py` (HCD) | the same corpus through the Data API, where the only path in the document model is a client-side scan-and-aggregate over paginated `find()` | `python3 probes/probe_aggregation.py --engine hcd --n 200000 --reps 30 --keyspace cmp --collection agg --out findings_agg_hcd.json` | `findings_agg_hcd.json` |
| `probes/agg_cql_arm.py` | the labelled apples-to-oranges reference: a purpose-built native CQL table partitioned by the group key, swept per partition and then with a cross-partition `GROUP BY` | `AGG_N=200000 AGG_REPS=15 CQL_PORT=9142 python3 probes/agg_cql_arm.py` | `findings_agg_cqlref.json` (filename fixed) |

`agg_cql_arm.py` takes no command-line arguments at all; everything comes from the environment,
and it drops its table on exit.

Its label is part of the result and should not be detached from it: reaching the CQL arm means
abandoning the document model and pre-designing a table partitioned by the group key — the index
design work the Data API's pitch is to avoid. And the HCD scan arm has **n = 3** repetitions
(`max(reps//10, 3)` in the probe), so its p95 and p99 carry no information
(`docs/campaigns/07-aggregation.fr.md`).

---

## 6. Leaving the ring as you found it

The campaigns ran on a shared ring, and each one ends with a restoration section. If you borrow
someone else's ring, do the same, and record it:

```bash
# drop the probe keyspace
cqlsh -e "DROP KEYSPACE verif_stockage_20260917;"

# clear snapshots on every node
for n in p16-hcd-node1 p16-hcd-node2 p16-hcd-node3 p16-hcd-node4 p16-hcd-node5 p16-hcd-node6; do
  docker exec "$n" nodetool clearsnapshot --all
done

# put tracing back and verify it
for n in p16-hcd-node1 p16-hcd-node2 p16-hcd-node3; do
  docker exec "$n" nodetool getlogginglevels >/dev/null
  docker exec "$n" nodetool settraceprobability 0.0
done

# recreate any borrowed index slots from the definitions you captured BEFORE dropping them
cqlsh -f p16-sai-index-definitions-YYYYMMDD.cql

# remove the temporary Data API container and the MongoDB stack
docker rm -f p16-data-api
docker compose -f env/docker-compose.mongodb-rs.yml down -v
docker rm -f atlas-local
```

One residue the campaign could not clear, and declared rather than hid: the disk-regime fills of
campaigns 3 and 4 were roughly 24 600 lightweight transactions each, and they grew `system.paxos`
to about 13 GiB per dc1 node. `paxos_state_purging = legacy` holds the ballots and purges them
lazily, so a manual compaction released nothing, and the residue was left to the engine's own
purge rather than hammering a system table on a shared ring
(`docs/campaigns/03-disk-regime.fr.md`, `docs/campaigns/04-tier-vs-storage.fr.md`). Campaigns 4, 5
and 6 then ran on top of that residue, which the audit records as finding I6: memory and
compaction pressure that may have slowed HCD, never quantified and never subtracted.

---

## 7. Why your numbers will differ from ours

This section is the point of the document. If you take one thing from this file, take this.

**1. The headline coefficient is not a property of the engine. It is a property of a regime.**
The growth factor of the indexed-content variant was measured three times, on three regimes, and
it spans a factor of five: **×7.50** memtable-resident at RF 1 (`data/raw/findings.json`),
**×5.94** with the dataset on disk at RF 3 (`docs/campaigns/03-disk-regime.fr.md`), and **×1.52**
once the cycle's read is forced onto the SSTable path (`data/raw/rmw_postflush.json`). The
per-kilobyte rate of 0.7775 ms that carries the comparison is a **cache/memtable** rate. The audit
records this as finding I4 and states the consequence without softening: quoting one of those
numbers as *the* mutation cost of HCD is misleading. If your working set does not sit where ours
sat, your coefficient will not be ours — and the mechanism, not the magnitude, is what transfers.

**2. The load was closed-loop, which is the first rule the article imposes on other people.**
Every mutation, read and comparison probe measures one operation, then the next. Only the
freshness probe drove a fixed offered rate. The dossier's audit scores it against the article's
own six conditions for a defensible benchmark and gives it roughly 2.5 of 6
(`docs/audit-adversarial.fr.md`). A closed loop hides exactly the stalls an open loop exposes. If
you drive a real offered rate, expect worse tails than ours — on both engines.

**3. The host was shared, loaded and mutating.** Load average 14–16 throughout, other tenants on
the same ring, and a `system.paxos` residue that grew from campaign to campaign. Absolute HCD
latencies are a noisy ceiling, not a clean measurement (audit finding I6).

**4. Two different MongoDB deployments.** The mutation, read and search figures come from a
three-member replica set; the search-freshness figures come from a single-node `atlas-local`
image, where `w:majority` is trivial and the `mongot` refresh interval is not user-tunable. They
are not the same MongoDB (audit finding I8; `docs/challenges.fr.md`, C10 and D2).

**5. Five of the decisive instruments were written by the measurer.** `method2_trace.py`,
`hcd_cql_arm.py`, `rmw_postflush.py`, `mongot_freshness.py` and `probe_read_search.py` are the
measurer's own code, and among them are both of the measurements in which HCD wins. The supplied
harness was also patched three times, each fix declared and mechanical. The audit records this as
finding I2 and draws the ranking you should apply: the verdicts resting on an **unmodified**
supplied script — the shredded layout, the traced cycle, the field-versus-byte result — are the
solid ones (`docs/audit-adversarial.fr.md`, `docs/challenges.fr.md`, C5).

**6. Thirty to fifty repetitions, two passes, medians only.** No confidence intervals, no
significance tests — except in campaign 7bis, whose probe keeps every observation and whose report
therefore carries both. The between-pass variance is roughly 10–15 %, which exceeds some of the
effects claimed, and the MongoDB slopes carry r² of 0.78 and 0.88 because they are so nearly flat
that noise dominates — which *is* the result, and is also a reason not to quote those slopes to
four digits (audit finding I7).

**7. The Paxos round was measured where it hurts least.** All three dc1 replicas shared one host,
so inter-replica latency was sub-millisecond. The structure of the consensus round is established;
its cost on a multi-host or wide-area deployment is not, and it would be larger
(`docs/challenges.fr.md`, C3).

**8. The storage class was never established.** A QEMU virtual disk, `rotational=1` by default
rather than by evidence, no `smartctl`, no root. Effective sequential write throughput measured at
101 MB/s (`docs/campaigns/03-disk-regime.fr.md`). On an NVMe device or a slow network volume the
absolutes change.

**9. One build of each engine, on two days.** HCD 2.0.6 with Data API v1.0.33; MongoDB 8.0.32, and
8.3.11 for the search-freshness half. Nothing here transfers to another version, to Apache
Cassandra, or to Atlas in production.

If your run contradicts ours, that is the outcome this repository was built for. Open an issue,
name the file under `data/raw/`, the measurement identifier and what you believe is wrong —
`DISCLAIMER.md` explains why a correction that overturns a finding is the point rather than an
attack.

**Then read [LIMITATIONS.md](LIMITATIONS.md) before you quote a single number from either run.**
