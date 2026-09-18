> **English abstract.** This campaign asked whether MongoDB is cheaper than HCD on the one axis the article reasons about structurally — mutating a single field of a document — and by how much. Both engines ran on the same host in the same session (HCD 2.0.6 with Data API v1.0.33 on a `{dc1:3}` keyspace; MongoDB 8.0.32 as a three-member replica set), over the same series of sixteen indexed fields of 512 to 8000 bytes, 30 repetitions and two passes, in a matched cache-resident regime, with durability matched by a declared judgement (`w:"majority"`+`j:true` against `LOCAL_QUORUM`+`LOCAL_SERIAL`, two of three real replicas on each side) and resources matched at 8 GiB / 4 vCPU per node. MongoDB won decisively: per indexed kibibyte the full HCD stack cost 0.7775 ms (r² 0.997) against 0.0176 ms for MongoDB carrying the wildcard index that matches HCD's automatic indexing (r² 0.88) and 0.0098 ms for MongoDB as a team actually deploys it (r² 0.78) — ratios of 44× and 79× — with update medians of 40.9→130.8 ms on HCD against 5.5–7.6 ms on MongoDB; removing the Data API tier (measurement M14, `comparison_v2.json`) left the bare HCD storage engine at 0.7037 ms/KiB, still 40× the wildcard arm, so the gap is an engine result and not a tier artefact. Both MongoDB arms are the finding: quoting the default arm alone overstates MongoDB's advantage, quoting the wildcard arm alone understates how MongoDB is really used, and the report requires both or neither. Scope limit that must never be dropped when this number is quoted: these are **cache-resident (memtable) rates**, on one host, one build of each engine, one sequential single-client load, on the single axis where HCD's shredding is expected by design to cost most — the later post-flush measurement (M15, `rmw_postflush.json`) shows the per-byte coefficient collapsing from ×5.94 to ×1.52 once the read half of the read-modify-write cycle is forced onto SSTables, so 0.7775 ms/KiB characterises a regime, not "the" mutation cost of HCD; and this campaign measures nothing of read, search, aggregation or index freshness, which are the axes the article claims for HCD.
>
> *Report body below is in French. Raw evidence: `data/raw/comparison.json`, `data/raw/cmp_hcd.json`, `data/raw/cmp_mongo.json`; tier-removed arm: `data/raw/comparison_v2.json`, `data/raw/cmp_hcdcql.json`.*

---

# Campagne 5 — mesure comparative HCD vs MongoDB — 18 septembre 2026

## Résultat (première phrase, sans atténuation)

**Sur l'axe de la mutation d'un champ, MongoDB coûte nettement moins cher que HCD : environ 6 à 20 fois moins en latence absolue, et ~44 fois moins par kilo-octet indexé pour la pile HCD complète (Data API incluse), ~40 fois moins pour le moteur de stockage HCD nu (niveau retiré — mesure M14) — même quand on impose à MongoDB l'index wildcard qui apparie sa capacité au défaut de HCD.** La latence de mutation de MongoDB est essentiellement plate en taille de document ; celle de HCD croît linéairement avec les octets indexés. C'est le résultat que le raisonnement structurel du diptyque prédit.

## Le tableau

Même hôte (`alphadebunker`), même session, même série (16 champs × 512→8000 B), 30 répétitions, 2 passes, **régime cache apparié des deux côtés**. `cross_engine_comparison_permitted: true` (même hôte + même forme vérifiés par le harnais).

| Bras | Pente (ms / Kio indexé) | r² | p50 update, 8 Kio → 125 Kio |
|---|---|---|---|
| **mongo-default** (aucun index sur le ballast) | **0,0098** | 0,78 | 5,7 → 6,5 ms |
| **mongo-wildcard** (index `$**`, capacité appariée à HCD) | **0,0176** | 0,88 | 5,5 → 7,6 ms |
| **hcd** (indexation automatique, défaut) | **0,7775** | 0,997 | 40,9 → 130,8 ms |

Rapports de pente : **HCD = 79× mongo-default, 44× mongo-wildcard**. Le r² faible côté MongoDB (0,78 / 0,88) traduit la platitude : la pente est si proche de zéro que le bruit domine — ce qui *est* le résultat (le coût de mutation de MongoDB ne suit pas les octets indexés).

**La paire est le résultat, pas l'un des deux bras.** `mongo-default` (ce qu'une équipe déploie vraiment) contre HCD surestime l'avantage de MongoDB ; `mongo-wildcard` seul (MongoDB faisant le travail de HCD) sous-estime son usage réel. Les deux sont rapportés. Même à capacité appariée, MongoDB reste ~44× moins cher par Kio indexé.

## Pourquoi

MongoDB `$set` modifie le champ visé sans réécrire le document, et ne maintient que les index déclarés ; même avec un index wildcard, son coût de mutation par octet reste quasi nul. HCD lit le document, le réécrit entier plus onze colonnes dérivées, maintient neuf index SAI, et garde l'écriture par une ronde Paxos — tout cela croissant avec les octets indexés (mesures M2, M3, M11, M12).

## Ce qui a été apparié, et ce qui ne peut pas l'être

- **Durabilité appariée** : MongoDB `w:"majority"` + `j:true` (2 sur 3 réplicas réels) ↔ HCD `LOCAL_QUORUM` + `LOCAL_SERIAL` (2 sur 3). La correspondance **est un jugement, pas un fait** ; elle est inscrite dans la sortie et accompagne tout chiffre. MongoDB à `w:1` contre HCD au quorum aurait été le truquage classique — évité.
- **Ressources appariées** : chaque `mongod` et chaque nœud HCD à **8 Gio / 4 vCPU**. Réserve : HCD porte en plus un niveau Data API (2 Gio, sans plafond CPU) que MongoDB n'a pas.
- **Asymétrie non couverte par la correspondance, nommée** : chaque mutation HCD porte une transaction légère (une ronde Paxos, `LOCAL_SERIAL`) ; MongoDB n'en paie aucune, l'atomicité y étant garantie au document. **Ce n'est pas un réglage à aligner, c'est une différence de conception** — et elle fait partie de ce qui est mesuré.
- **Replica set 3 membres**, pas un nœud isolé : `w:"majority"` est une vraie majorité 2/3, pas le cas trivial d'un membre unique (l'équivalent du piège RF=1/`LOCAL_QUORUM` de la campagne 1).

## Correctifs du diptyque

La limitation qui affirme qu'aucune mesure n'a été prise du côté MongoDB **tombe** : l'axe de la mutation d'un champ est désormais mesuré, sur le même hôte, MongoDB gagnant nettement. Phrases exactes et remplacements dans `wording_insertions.md` (items II.17–II.19, annexe M13), appliqués au volet I. **Je n'ai qu'un volet HTML** ; si un volet II porte la même limitation, le même correctif s'y applique.

## Ce que cette campagne n'établit pas

Section longue, à dessein.

- **Un seul axe : la mutation d'un champ.** Elle ne dit **rien** de la lecture, de la recherche, de l'agrégation, ni de la **fraîcheur d'index** — l'axe où HCD a son avantage structurel (index maintenu sur le chemin d'écriture, document cherchable à l'acquittement, §4 et M7). Le résultat ci-dessus est vrai *et* étroit.
- **Un seul régime** (cache apparié), un seul hôte, une seule forme de déploiement, une seule charge (série séquentielle mono-client). Rien sur la concurrence, la contention, ou la mise à l'échelle.
- **Le niveau Data API de HCD est un composant de plus** que MongoDB n'a pas dans ce dispositif : une part du désavantage HCD est le coût de niveau (M12 : ~29 % du taux), qui s'absorbe horizontalement. La comparaison mesure les piles telles que déployées, pas les moteurs de stockage nus l'un contre l'autre.
- **La correspondance de durabilité est un jugement.** Un lecteur qui la conteste conteste le chiffre ; il ne peut pas l'ignorer, elle est déclarée.
- **La ronde Paxos de HCD** n'est pas neutralisable : elle est intrinsèque au chemin conditionnel de la Data API. Une comparaison « à atomicité égale » n'existe pas ici — c'est une différence de conception, pas un curseur.
- **MongoDB 8.0.32, une version, une build** ; HCD 2.0.6, une build. Rien ne se transpose à d'autres versions.

## État de l'anneau et des ressources

MongoDB entièrement démonté (3 conteneurs + réseau `cmpnet` supprimés). Anneau HCD rendu à l'identique : keyspace `cmp` supprimé, snapshots purgés (6 nœuds), 20 index `supply_chain_hcd` recréés (101 au total), Data API retirée, tracing 0.0 (non activé cette campagne). Reliquat inchangé des campagnes 3-4 : `system.paxos` ~13 Gio/nœud dc1 (cette campagne n'a ajouté que ~600 LWT, négligeable).
