> **English abstract.** Campaign 3 measured a mutation cost of about 0.77 ms per indexed kilobyte on HCD 2.0.6; this campaign asks where that rate is charged — in the stateless Data API tier, which scales out by adding instances, or in the stateful storage engine, which does not. In the same proven disk regime (6.05 GiB on disk, 40 SSTables, 76 compactions crossed, `disk_state_c4.json`), the identical mutation was run as arm A through the Data API `updateOne` and as arm B through the identical CQL statement pair against the same row, with the shredded values read back rather than recomputed so that the storage work is the same and no JSON is parsed; the difference is the tier term, and a second, independent method subtracted the coordinator-side trace duration from the client latency. Method 1 splits the rate into a storage term of 0.547 ms/KiB (r² 0.997) and a tier term of 0.219 ms/KiB (r² 0.98), summing to 0.766 and so reproducing campaign 3's rate: the majority (~71 %) sits in the stateful storage engine, a substantial minority (~29 %, or ~19 % by the trace method, whose tier slope is 0.145 ms/KiB) in the stateless tier. The scope limit that must travel with those figures, without exception: the two methods agree within 25 % at 8, 16 and 32 KiB but diverge by 34 % at 64 KiB and 28 % at 125 KiB, and their tier slopes differ by about 50 %, so no single precise split is published — only the direction and a range — and the run was measured against a CPU-unconstrained, co-located Data API container, so the slope answers the location question while the absolute latency does not transfer to a tier sized for production. The tier share is contested downstream in this same dossier: an HCD-CQL-direct arm in a matched cache regime put it at ~9 % (`comparison_v2.json`, 0.7775 → 0.7037 ms/KiB), the adversarial audit therefore records the share as an unpinned 9–29 % range, and the underlying 0.77 ms/KiB is itself shown to be a memtable/cache coefficient that collapses to ×1.52 growth once the read is forced onto SSTables (`rmw_postflush.json`). The net effect on the author's own article is that its criticism is partially softened, not overturned — the tier term is real and elastic, but it does not dominate, so no existing claim was replaced and an additive [M] note was written instead.
>
> *Report body below is in French. Raw evidence: `data/raw/findings_tier.json`, `data/raw/findings_tier_method2.json`, `data/raw/tier_comparison.json`, `data/raw/disk_state_c4.json`.*

---

# Campagne 4 — niveau Data API vs moteur de stockage — 17 septembre 2026

## Où réside le taux (première phrase)

**Le taux de ~0,77 ms par kilo-octet indexé réside majoritairement dans le moteur de stockage avec état (~71 %), mais une minorité substantielle — de l'ordre d'un quart à un tiers — réside dans le niveau Data API sans état, qui s'absorbe horizontalement.** La critique du diptyque est donc **partiellement atténuée, pas renversée** : une part réelle du coût est portée par un composant qui scale en ajoutant des instances, mais la majorité reste dans le composant avec état, qui ne scale pas ainsi.

## Le chiffre, et sa réserve la plus importante

Méthode 1 (contournement), régime disque prouvé, deux passes :

| Terme | Pente (ms / Kio indexé) | r² |
|---|---|---|
| **Niveau** (méthode 1) | **0,219** | 0,98 |
| **Stockage** (méthode 1) | **0,547** | 0,997 |
| Somme | **0,766** | — reproduit le 0,77 de la campagne 3 |
| **Niveau** (méthode 2, trace) | **0,145** | 0,99 |

Part du niveau dans le taux : **29 % (méthode 1), 19 % (méthode 2)**. Part du niveau dans la latence absolue : **~30–40 %** (plus haute aux petites tailles, où le coût fixe HTTP/parse pèse davantage).

**Réserve cardinale, appliquée telle qu'écrite dans le brief.** Les deux méthodes **s'accordent à moins de 25 % aux tailles 8, 16 et 32 Kio, mais divergent au-delà : 34 % à 64 Kio, 28 % à 125 Kio**, et les pentes du terme niveau diffèrent de ~50 % (0,219 contre 0,145). **Aucun chiffre de partage unique et précis n'est donc publié** ; je rapporte une fourchette et la divergence. La divergence vient de ce que les deux instruments ne soustraient pas le même « stockage » : la méthode 1 retranche une exécution CQL cliente complète (pilote + réseau + coordinateur), la méthode 2 retranche la seule durée interne du coordinateur — plus grande, car elle inclut le tour Paxos serveur. Ce que les deux méthodes établissent **en commun et robustement** : le niveau est une minorité substantielle et réelle, le stockage est la majorité.

## Tableau — taille par taille

| Taille | Total (ms) | Niveau m1 (ms) | Stockage m1 (ms) | Part niveau | Niveau m2 (ms) | Écart | Accord ≤25 % |
|---|---|---|---|---|---|---|---|
| 8 Kio | 27,6 | 10,98 | 16,67 | 40 % | 11,03 | 0 % | oui |
| 16 Kio | 33,7 | 10,06 | 23,63 | 30 % | 10,86 | 8 % | oui |
| 32 Kio | 47,0 | 14,59 | 32,39 | 31 % | 13,10 | 11 % | oui |
| 64 Kio | 70,9 | 23,93 | 46,94 | 34 % | 17,86 | **34 %** | **non** |
| 125 Kio | 117,4 | 34,95 | 82,42 | 30 % | 27,37 | **28 %** | **non** |

## Troisième indice — CPU du conteneur

Échantillonné pendant la méthode 1, le CPU du conteneur Data API **alterne entre ~0,5 % (bras B, Data API au repos pendant le CQL direct) et 40–230 % (bras A, Data API actif)**. Indice faible mais indépendant : le niveau dépense un CPU réel proportionné au travail — il ne s'agit pas d'un simple surcoût réseau.

## Conditions (les chiffres n'ont pas de sens sans elles)

- **Produit** : HCD 2.0.6 (`5.0.7.0-ea50e91ba01f`), Data API v1.0.33. Anneau p16, keyspace `verif_tier_20260917 = {dc1:3}`.
- **Ressources du conteneur Data API** : `mem_limit` 2 Gio, **aucune limite CPU** (nanocpus=0, 80 vCPU hôte disponibles), non épinglé, **co-localisé** avec les nœuds. C'est précisément parce qu'un conteneur non contraint rend la valeur absolue non représentative que la question est répondue par la **pente**, robuste à l'absence de plafond CPU.
- **Régime disque prouvé** (`disk_state_c4.json`) : 6,05 Gio sur disque (≥ 3× le budget memtable de 2 Gio), 40 SSTables post-compaction, 76 compactions franchies, caches invalidés. Même régime que la campagne 3, comme l'exige le brief.
- **Durabilité** : `commitlog_sync periodic 10 s`, défauts `LOCAL_QUORUM` / `LOCAL_SERIAL`.
- **Correctif mécanique déclaré** : le bras B liait la clé `frozen<tuple<tinyint,text>>` en instruction simple `%s`, rejetée par le serveur ; passé aux **instructions préparées** (`?`), qui portent le type de colonne — vérifié, et c'est la façon correcte de lier une clé typée. Aucun seuil/taille/répétition modifié.

## Tableau de synthèse — diptyque

| Affirmation (volet I) | Marqueur | Verdict mesuré | Proposition |
|---|---|---|---|
| Le coût de la mutation est attribué, en prose, à la maintenance d'index (stockage) | [M] | **Majoritairement juste** (~71 % stockage) **mais incomplet** : ~un quart à un tiers est du niveau sans état | ajouter la distinction sans état / avec état (M12) |

**Le terme niveau ne domine pas.** Le déclencheur du brief pour un remplacement (« si le terme niveau domine ») n'est donc **pas** rempli, et je n'invente pas une correction que la mesure n'appelle pas. La nuance à introduire est **additive** : une fraction réelle du taux vit dans un composant qui scale horizontalement. Elle est proposée en note pour le volet I et en révision de la section « Pourquoi ceci est une décision d'architecture » de l'ADR.

## Ce que cette campagne n'établit pas

- **La décomposition interne du terme niveau.** Le bras B saute l'analyse JSON **et** la décomposition **et** la sérialisation de la réponse ; le terme niveau est les trois ensemble, non séparés.
- **Le bras B n'est un étalon de rien.** Il réutilise des valeurs déjà décomposées et n'exerce jamais le code qui les calcule — c'est un instrument de soustraction, pas une mesure de performance CQL.
- **Une part du terme niveau est du coût de bibliothèque cliente** (client Data API vs pilote CQL diffèrent en gestion de connexions et sérialisation) ; elle n'est pas isolée.
- **Un partage absolu précis** : les deux méthodes divergent de plus de 25 % aux deux plus grandes tailles ; seule la conclusion qualitative (minorité niveau, majorité stockage) est robuste.
- **Un niveau dimensionné pour la production** : mesuré contre un conteneur **non contraint en CPU**. La pente répond à la question de localisation ; l'absolu ne se transpose pas à un niveau sizé.
- **Le confondant page cache** de la campagne 3 subsiste (pas de root).
- **Effet de bord durable qui s'accumule** : les remplissages disque (campagnes 3 puis 4, chacun ~24 600 inserts LWT) ont porté `system.paxos` à **13 Gio/nœud dc1** (~+36 Gio disque). `paxos_state_purging = legacy` ne libère pas à la compaction ; laissé à la purge naturelle. **Ce reliquat croît d'une campagne disque à l'autre** — à surveiller si d'autres campagnes disque suivent.

## État de l'anneau

Keyspace supprimé, tous les snapshots purgés (6 nœuds), 20 index `supply_chain_hcd` recréés (101 au total), Data API retirée, **tracing 0.0 vérifié** sur les 3 nœuds dc1. Seul reliquat : `system.paxos` ci-dessus.
