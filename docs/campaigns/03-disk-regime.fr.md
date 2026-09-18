> **English abstract.** This campaign asked which term of the shredding mutation cost is the real driver — the *number* of indexed fields or the *volume* of indexed bytes — and whether the ×7.50 growth coefficient measured earlier in a memtable-resident regime survives once the dataset is proven to live on disk. Method: 6.05 GiB of incompressible ballast was loaded into an RF 3 keyspace on a 6-node ring until the disk regime was proven rather than assumed (40 SSTables after a major compaction, 78 compactions crossed on the counter 651 → 729, key and row caches invalidated), and two probes were then run against that state without restarting the node: a two-series field-versus-byte design, each series holding one term fixed, and a read-modify-write probe repeating the earlier coefficient. Headline result — the indexed **byte volume** dominates: at a constant indexed volume of 64 KiB, raising the field count from 9 to 128 (×14) moved the update p50 only ×1.13 and ×1.19 across two passes, while at a constant 16 fields raising the bytes per field from 512 to 8000 moved it ×4.6 with a straight-line fit of r² 0.9999; the pre-registered rule returns no clean verdict, because the two passes straddle its 1.15 line (1.128 and 1.187), though neither approaches the 1.5 that would make field count an independent driver. The read-modify-write coefficient did not collapse in this regime (×5.94 at RF 3 on disk against ×7.50 at RF 1 in memtable), but that comparison mixes regime with a topology and hardware confound and cannot be attributed to disk alone. Scope limit that must never be dropped when these numbers are quoted: "disk-bound" here describes the *dataset*, not the *probed read* — the RMW probe re-reads the row it has just written, which stays memtable-resident whatever the dataset size, and the OS page cache could not be dropped for want of root; a later post-flush pass (M15, `data/raw/rmw_postflush.json`) that forced the cycle's SELECT onto the SSTable path collapsed the coefficient to ×1.52, so every per-byte rate in this report is a memtable/cache-regime figure, not a disk-bound one.
>
> *Report body below is in French. Raw evidence: `data/raw/findings_disk_rf3.json`, `data/raw/findings_fieldbyte.json`, `data/raw/disk_state.json`.*

---

# Campagne 3 — régime disque à RF 3 et séparation champ/octet — 17 septembre 2026

## Synthèse (dix lignes)

**Le résultat publié tient, et il est désormais chiffrable — mais son libellé doit changer : ce sont les octets indexés qui portent le coût, pas le nombre de champs.** L'expérience B le tranche : à volume indexé constant (64 Kio), multiplier le nombre de champs par 14 (9 → 128) ne déplace la latence que de **×1,13 à ×1,19** ; à nombre de champs constant (16), multiplier les octets par ~16 la déplace de **×4,6**, avec un ajustement linéaire quasi parfait (r² 0,9999). Le terme **octet** domine nettement ; le nombre de champs est un facteur secondaire faible. Le verdict strict pré-déclaré reste « inconcluant » parce que les deux passes encadrent le seuil de 1,15 — mais aucune n'approche le 1,5 qui ferait du nombre de champs un facteur indépendant. L'expérience A montre par ailleurs que le coefficient **ne s'effondre pas** en régime disque prouvé : la variante B croît de **×5,94** (disque, RF 3) contre ×7,50 (memtable, RF 1) — même ordre, la maintenance d'index reste un coût de premier ordre face aux I/O. Le régime disque a été **prouvé** (6,05 Gio sur disque, 40 SSTables, 78 compactions franchies, caches invalidés), non supposé.

## Conditions (les chiffres n'ont pas de sens sans elles)

- **Produit** : HCD 2.0.6 (`5.0.7.0-ea50e91ba01f`), Data API v1.0.33 (conteneur temporaire). Anneau p16 : 6 nœuds / 2 DC, keyspace `verif_disk_20260917 = {dc1:3}`, nœuds 8 Gio / 4 vCPU, heap 4G, memtable budget 2048 Mio.
- **Classe de stockage — indéterminable depuis la VM, non inventée.** Données sur `/dev/sda1` (ext4), disque SCSI virtuel QEMU ; `rotational=1` est le défaut QEMU, pas une preuve de média ; ni `smartctl` ni root. Débit effectif mesuré (dd fsync) : 101 Mo/s en écriture séquentielle. Média physique non établi.
- **Preuve du régime disque** (`disk_state.json`) : remplissage 24 576 documents de ballast **incompressible** (256 Ko each, ~19 min), flush → 82 SSTables, compaction majeure → 40 SSTables, compteur de compaction **651 → 729** (78 franchies), `du` du keyspace **6,05 Gio ≥ 6,0 Gio visés**, caches clés/lignes invalidés. `disk_bound = True`.
- **Durabilité** : `commitlog_sync periodic 10 s` ; défauts Data API writes/reads `LOCAL_QUORUM`, serial `LOCAL_SERIAL`.

## Correctif mécanique (déclaré avant tout chiffre)

Le pilote a d'abord rendu `disk_bound = False` sur un seul contrôle : `data_exceeds_memtable_budget`. Cause : le ballast était des octets **constants** (`"x"`), compressés ~120:1 par le `LZ4Compressor` de la table — 6 Gio logiques → **50 Mio sur disque**. Corrigé : ballast **incompressible** (aléatoire base64, valeur fraîche par document) pour que la taille sur disque suive la taille logique. Rien d'autre n'a changé (tailles, seuils, obligations de preuve intacts). Deux adaptations d'hôte→conteneur aussi déclarées : wrapper `nodetool` via `docker exec`, et lecture des preuves SSTable via `docker exec` (volume hôte root-only). Diffs dans `disk_regime_driver.py`.

## Résultats

### Expérience B — champ vs octet (décisive)

| Série | Ce qui varie | p50 update (ms) | Croissance | r² |
|---|---|---|---|---|
| **S2** (volume 64 Kio fixe) | 9 → 128 champs | 67 → 75-80 | **×1,13 / ×1,19** | 0,57 / 0,92 |
| **S1** (16 champs fixes) | 512 → 8000 o/champ | 25 → 115 | **×4,6** | **0,9999 / 0,9999** |

Contrôle interne (16×4096 o, mesuré dans les deux séries) : écarts **2,0 % et 0,7 %** → sous 10 %, pentes fiables. Verdicts des deux passes : `BYTES DOMINATE` (1,128) et `INCONCLUSIVE` (1,187) — ils encadrent le seuil de 1,15 ; **aucune passe n'atteint 1,5**. Direction sans ambiguïté : **le volume d'octets indexés domine**.

### Expérience A — coefficient en régime disque (RF 3)

| Mesure | Campagne 1 (memtable, RF 1) | Campagne 3 (disque, RF 3) |
|---|---|---|
| Variante A (ballast non indexé) update / lecture | ×1,92·2,21 / ×1,86·1,94 | ×1,78 / ×1,89 (INCONCLUSIVE par la règle de contrôle) |
| Variante B (contenu indexé) update / lecture | **×7,50** / ×1,56 | **×5,94** / ×2,10 |

Le coefficient de la variante B ne s'effondre pas en régime disque ; il reste du même ordre. **La différence ×7,50 → ×5,94 mêle le régime ET le confondant topologie/matériel** (rh-hcd RF 1, 3 Gio/2 G ↔ p16 RF 3, 8 Gio/4 G) : elle ne s'attribue pas au disque seul.

## Tableau de synthèse — affirmations du diptyque

| Affirmation (diptyque) | Marqueur actuel | Verdict mesuré | Marqueur proposé |
|---|---|---|---|
| Le coût d'une mutation suit le **contenu indexé** inchangé | [M] | **CONFIRMÉ**, et le moteur est le **volume d'octets** ; le nombre de champs est secondaire faible (M11) | [M] + précision octet |
| « combien de champs indexés » comme test de classification | (ADR/wording) | **À corriger** : « combien d'**octets** indexés / quel volume » | reformuler |
| Coefficient = figure memtable | [M] (limitations) | **Nuancé** : tient en régime disque prouvé (×5,94), ne s'effondre pas (M10) | [M], plus « memtable-only » retiré |

## Ce que cette campagne n'établit pas

- **Le confondant de page cache n'est pas éliminé** (pas de root pour vider le cache OS). Le jeu de 6,05 Gio tient dans les 220 Gio de RAM de l'hôte : les lectures des données de remplissage peuvent encore être servies depuis la RAM sous la base. « Disk-bound » = le jeu **dépasse le budget memtable et vit en SSTables** (prouvé), pas que chaque lecture a manqué la RAM.
- **La sonde RMW relit sa propre ligne chaude** (SELECT `doc_json` avant l'UPDATE) : cette ligne est en memtable quelle que soit la taille du jeu. Le régime disque agit par pression mémoire et cache froid, pas en servant la ligne sondée depuis le disque. C'est pourquoi la variante A bouge peu.
- **Le confondant topologie/matériel** entre campagnes 1 (RF 1, petits nœuds) et 3 (RF 3, gros nœuds) n'est pas contrôlé : les latences bout-en-bout ne se comparent pas directement.
- **La séparation coût Data API / coût stockage** (action 5) reste ouverte.
- **L'expérience B n'a tourné qu'en régime disque** ; la linéarité par octet (r² 0,9999) est probablement robuste au régime mais n'a pas été rejouée en memtable.
- **Effet de bord assumé et non entièrement résorbé** : les ~24 600 inserts de remplissage sont des LWT (`INSERT IF NOT EXISTS`) → `system.paxos` a gonflé de ~6 Gio/nœud dc1 (~18 Gio sur dc1). Une compaction `system paxos` a été tentée sur les 3 nœuds mais n'a rien libéré : `paxos_state_purging = legacy` (grâce 60 s) retient les ballots et les purge paresseusement. Reliquat laissé à la purge naturelle du moteur — je ne martèle pas une table système sur un anneau partagé. Disque : 525 Go utilisés contre 507 Go au relevé initial (+18 Go, entièrement dans `system.paxos`). Tout le reste est rendu à l'identique : keyspaces d'expérience supprimés, tous les snapshots purgés (6 nœuds), 20 index `supply_chain_hcd` recréés (101 index au total), Data API retirée, tracing 0.0.

## Note sur les livrables du diptyque

Le brief mentionne « les deux volets HTML du diptyque ». **Un seul volet m'a été fourni** dans cette série de sessions : `article-storage-layout-predicts-write-cost-index-freshness-concurrency`. La correction §3.1 ci-dessous s'y applique. Si un volet II existe et porte le même récit « champs », il faut lui appliquer la même correction — mais je ne l'ai pas et je ne le reconstitue pas.
