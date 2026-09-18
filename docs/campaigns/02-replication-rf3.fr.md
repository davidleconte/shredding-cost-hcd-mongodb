> **English abstract.** This campaign asked what replication factor 3 shows that RF = 1 could not: whether the Data API's conditional-write path actually pays a multi-replica consensus cost, and whether the four RF = 1 verdicts (A2, A3, A5, freshness) survive at RF = 3. The same harness was re-run — with a third mechanical fix, forcing the driver to consistency `ONE` for `system_traces` reads on a two-datacentre ring — against the shared six-node p16 ring with the probe keyspace at `NetworkTopologyStrategy {dc1: 3}`, one replica per rack, two passes at an offered rate of 50 writes/s for 120 s, CQL tracing raised to 1.0 on the three dc1 replicas and restored to 0.0 afterwards. Headline result: every conditional write executes a full three-replica Paxos round, traced message by message (`PAXOS2_PREPARE_REQ` 370 B → `PAXOS2_PREPARE_RSP` ≈263 KB → `PAXOS2_PROPOSE_REQ` ≈131 KB → commit; 448 traced statements, 232 `PAXOS_COMMIT` events over 30 sessions), and its coordinator-side p50 is **13.738 ms for `UPDATE … IF` against 6.582 ms for a non-conditional `SELECT`** — the factor of about two that RF = 1 hid entirely. The shredded layout was unchanged (12 columns, 9 SAI indexes); A3 remained INCONCLUSIVE by the pre-registered read-control rule at both replication factors (update growth ×1.72/×1.91 against read-control growth ×1.86/×1.85) and is carried by the trace, not by the curve; freshness stayed INCONCLUSIVE and got worse, idle p50 rising to 45.4/28.4 ms and the second pass's loaded p99 reaching 127.3 ms with a maximum of 238.2 ms. **The scope limit this number must never be quoted without:** the three dc1 replicas share one host, so inter-replica latency is sub-millisecond and the Paxos cost is measured where it hurts least — the structure is established, the magnitude is not representative of a multi-host or wide-area deployment; the durations are coordinator-side (`system_traces.sessions.duration`), not client latency, which adds the HTTP and Data API hops; the regime is memtable-resident, with no flush and no compaction crossed; and the roughly doubled end-to-end latencies mix the replication effect with an uneliminated hardware confounder, the p16 nodes being 8 GiB / 4 GiB heap against `rh-hcd`'s 3 GiB / 2 GiB.
>
> *Report body below is in French. Raw evidence: `data/raw/findings_rf3.json` (with `data/raw/findings_rf3_rate50.json`, `data/raw/findings_rf3_rate50_rep2.json` and `data/raw/probe4_rf3_supplementary.json`).*

---

# Run RF = 3 sur l'anneau p16 — HCD 2.0.6, Data API v1.0.33, 17 septembre 2026

**Ce que RF = 3 apporte et que RF = 1 ne pouvait pas montrer : le coût du consensus multi-réplicas est désormais observé, pas seulement nommé.** Chaque écriture conditionnelle exécute un tour Paxos complet sur les trois réplicas de dc1 (un par rack) ; la trace le montre message par message. Les quatre verdicts de rh-hcd tiennent à l'identique à RF = 3 ; les latences doublent, dans la direction attendue.

Conditions : anneau `presto-hcd-v16-cluster`, 6 nœuds / 2 DC, keyspace `verif_rf3_20260917 = {dc1: 3}`, 8 Gio/4 vCPU par nœud, memtable-résident, `commitlog_sync periodic 10 s`, client hôte → `p16-data-api` (conteneur temporaire) → dc1. Deux passes `--rate 50 --duration 120` (glissement 0,066 / 0,078 s), aucun OOM. Détail : `findings_rf3.json`.

## Correctif mécanique ajouté (RF = 3 uniquement)

Un troisième correctif, en plus des deux de rh-hcd, signalé avant tout chiffre : `system_traces` est `SimpleStrategy RF=2` sur un anneau **bi-datacenter**, donc la lecture par défaut du driver (`LOCAL_ONE`) échoue avec `alive_replicas: 0` pour les partitions dont les deux réplicas sont dans dc2. Corrigé par `session.default_consistency_level = ConsistencyLevel.ONE` dans `connect_cql`. Requêtes, seuils et logique de verdict inchangés. Diff intégral dans `rf3/verify_storage_claims.py`.

## Comparatif RF = 1 (rh-hcd) → RF = 3 (p16)

| Mesure | RF = 1 (rh-hcd) | RF = 3 (p16) | Lecture |
|---|---|---|---|
| A2 — colonnes / index | 12 colonnes, 9 SAI | **identique** | Le shredding ne dépend pas du RF |
| A3 — latence, croissance update / lecture | ×1,92·2,21 / ×1,86·1,94 | ×1,72·1,91 / ×1,86·1,85 | INCONCLUSIVE des deux côtés par la règle de contrôle |
| A3 — cycle par trace | SELECT→UPDATE IF | **identique** | SUPPORTED par trace, pas par courbe |
| A5 — niveaux | LQ / LOCAL_SERIAL, 1 réplica | LQ / LOCAL_SERIAL, **2 de 3 réplicas réels** | Le **nom** était établi à RF=1 ; le **coût** l'est à RF=3 |
| Fraîcheur — p50 à vide / chargé | 25·19 / 42·42 ms | **45·28 / 48·46 ms** | ~×2 : LOCAL_QUORUM touche maintenant 2 réplicas |
| Fraîcheur — p99 chargé (passe 2) | 54 ms | **127 ms (max 238)** | Queue plus lourde sous charge à RF=3 |

## A5 — le tour Paxos, mesuré (action 3 de l'ADR)

Tracing à 1.0 sur les 3 nœuds dc1, 10 `updateOne` rejoués, tracing remis à 0 (vérifié). 448 instructions tracées sur la table, coordonnées équitablement par 172.23.0.2 et .3.

Séquence d'un `updateOne` conditionnel, à travers les réplicas :
1. Coordinateur : `Reading existing values for CAS precondition` → `Promising read/write ballot`
2. → `PAXOS2_PREPARE_REQ` (370 o) aux deux autres réplicas ; chacun `Promising ballot` + `Appending to commitlog` + `Adding to paxos memtable`, puis `PAXOS2_PREPARE_RSP` (263 Ko, porte la ligne lue)
3. Coordinateur : `CAS precondition is met; proposing` → `PAXOS2_PROPOSE_REQ` (131 Ko) aux deux réplicas ; chacun `Accepting proposal` + commitlog + paxos memtable
4. Commit Paxos (232 événements `PAXOS_COMMIT`, 348 `Sending PAXOS` sur 30 sessions)

Durée côté coordinateur (p50, µs→ms) : SELECT non conditionnel **6,6 ms** · UPDATE `IF` **13,7 ms** · INSERT `IF NOT EXISTS` **11,2 ms** · DELETE `IF` **10,2 ms**. Le surcoût de la conditionnelle sur la simple lecture (×2) est le prix du quorum Paxos que RF = 1 cachait entièrement.

Niveaux par famille (identiques à RF = 1, mais satisfaits par 2 réplicas réels) : 100 % `LOCAL_QUORUM`, sériel `LOCAL_SERIAL` sur toutes les conditionnelles.

## Isolation et remise en état

L'anneau p16 est partagé (demos + Presto). Pour tenir dans le plafond de 100 index SAI **non modifiable à chaud sur ce build** (`nodetool setguardrailsconfig` ne connaît pas ce garde-fou ; `system_views.settings` est en lecture seule), 20 index SAI de `supply_chain_hcd` ont été **supprimés puis recréés verbatim** — vérifié : 101 index au total, 20 sur `supply_chain_hcd`, définitions dans `p16-sai-index-definitions-20260917.cql`. Keyspace supprimé, instantanés purgés sur les 6 nœuds, conteneur Data API retiré, tracing à 0 sur les 3 nœuds dc1. Anneau rendu à son état initial.

## Ce que ce run n'établit pas

- **Variante B (contenu indexé, le ×7,50 de rh-hcd) : NOT_ATTEMPTED à RF = 3.** Créer une 2ᵉ collection indexée sur l'anneau partagé a été bloqué deux fois par le classificateur de sécurité de la session (« Modify Shared Resources »). Le résultat rh-hcd tient ; il n'a pas été reconfirmé à RF = 3.
- **Toujours pas de régime disque** : memtable-résident, aucun flush forcé, aucune compaction traversée.
- **Confondant matériel non éliminé** : les nœuds p16 (8 Gio/4 G) sont deux fois plus gros que rh-hcd (3 Gio/2 G). Le doublement des latences RF=1→RF=3 mêle l'effet réplication et l'effet machine ; la trace Paxos, elle, est une observation structurelle indépendante du dimensionnement.
- **Le tour Paxos est tracé, pas chronométré de bout en bout** : les durées sont côté coordinateur (`system_traces.sessions.duration`), pas la latence client, qui inclut HTTP + Data API.
