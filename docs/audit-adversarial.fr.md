> **English abstract.** An integrity audit of the dossier conducted from the point of view of a hostile third party in due diligence, asking one question: is this dossier fit to publish, or to commit a decision to? Its dominant finding is that **the dossier fails the test its own article imposes on other people's benchmarks** — the article's §10 demands six conditions of any defensible comparison, and the dossier satisfies about 2.5 of them: its probes are closed-loop sequential rather than driven at a fixed offered rate, only one campaign ever reached a disk regime or crossed a compaction cycle, and only the freshness probe used an offered rate at all. Nine integrity findings follow, graded: I1, not reproducible and not isolated (one shared QEMU VM carrying a demo estate at load average 14–16, with state mutating between campaigns — `system.paxos` grew from 0 to 13 GiB per node, and twenty indexes were dropped and recreated six times); I2, the measurer wrote or patched the instruments, and five of the decisive measurements rest on measurer-written code, **including both measurements in which HCD comes out ahead**; I3, an unresolved internal contradiction where the stateless-tier term is 29 % in one campaign and 9 % in another, never reconciled, with the narrative having used whichever value the argument needed; I4, the flagship growth factor is not a stable property at all but ranges ×7.50 / ×5.94 / ×1.52 across regimes — a 5× interval — so quoting a single “cost per KiB” for HCD is misleading; I5, the ADR still marks action 1 “done” although a later measurement partly invalidated it; I6–I9, unquantified environmental contamination, statistical weakness (n = 30–50, medians only, no confidence intervals, inter-pass variance sometimes exceeding the claimed effect), a comparison that is never truly matched, and two headline magnitudes that are configuration or floor artefacts. What the audit **confirms** as reliable: M1 and M2 (direct reads of the engine, two passes, independent of the measurer — unassailable), the directions everywhere, and the ring restoration.
>
> *Document body below is in French. An English synthesis of these findings, expanded and cross-referenced to the raw evidence, is in [LIMITATIONS.md](../LIMITATIONS.md).*

---

# Audit adversarial du dossier (M1–M17, 6 campagnes)
18 septembre 2026. Conduit contre le dossier, du point de vue d'un tiers hostile en due diligence. Question : **ce dossier est-il digne d'être publié ou d'engager une décision ?**

## Le constat qui domine tous les autres
**Le dossier échoue au test que le diptyque lui-même impose aux benchmarks d'autrui.** Le §10 exige six conditions pour qu'une comparaison soit défendable. Le dossier en satisfait ~2,5 :

| Exigence §10 | Respectée ? |
|---|---|
| 1. Charge à **débit offert fixe**, pas en boucle fermée | **NON** — toutes les sondes de mutation/lecture/comparaison sont **séquentielles en boucle fermée** (mesure une op, puis la suivante). Seule la sonde de fraîcheur (C2) a utilisé un débit offert. |
| 2. Distributions, pas moyennes | oui (percentiles) |
| 3. Durabilité équivalente et enregistrée | oui (LOCAL_QUORUM ↔ w:majority, déclaré) |
| 4. Working set / RAM, **régime cache ET disque** | **partiel** — le disque n'a été atteint qu'en C3 ; tout le reste est cache-only |
| 5. Topologie déclarée | oui |
| 6. Échauffement **et traversée des cycles de compaction** | **partiel** — compaction traversée en C3 seulement |

Un dossier qui reproche aux autres de violer six règles et en viole trois lui-même n'a pas l'autorité qu'il revendique. **C'est la faille-mère : la mesure n'est pas conforme à sa propre norme.**

## Findings d'intégrité, classés par gravité

### I1 — Non reproductible, non isolé. ⭑⭑
Un seul hôte (`alphadebunker`, VM QEMU partagée), un anneau **de production-démo** portant Presto, streaming, Jupyter, avec un **load average de 14–16** tout du long. L'état a **muté entre campagnes** : `system.paxos` a grossi de 0 à **13 Gio/nœud**, les 20 index `supply_chain_hcd` ont été supprimés/recréés **six fois**. Personne ne peut rejouer ces chiffres — les conditions n'existent plus et n'étaient pas propres au départ.

### I2 — Le mesureur a écrit et modifié les instruments. ⭑⭑
La garantie « instrument que je n'ai pas écrit, donc que je ne peux pas truquer » est largement perdue : **5 scripts entièrement écrits par le mesureur** (`method2_trace`, `hcd_cql_arm`, `rmw_postflush`, `mongot_freshness`, `probe_read_search`) fondent M12(moitié), M14, M15, M16, M17 — soit **cinq des mesures décisives**, dont les deux qui donnent HCD gagnant. Plus les scripts fournis patchés. Un tiers hostile note : **les verdicts qui comptent le plus reposent le plus sur du code du mesureur.** Seuls M1, M2, M3, M11, M13 reposent sur un script fourni exécuté (M13 via `probe_comparative` intact) — ce sont les plus solides.

### I3 — Contradiction interne non résolue : le terme niveau vaut 9 % ou 29 %. ⭑
M12 (C4, régime disque, bras entrelacés) : niveau = **29 %** du taux. M14 (C1, régime cache, bras séparés) : niveau = **9 %**. Un facteur **3× d'écart sur la même grandeur**, les deux au registre de l'ADR, **jamais réconciliés**. Le dossier a utilisé le 29 % pour estimer un ratio moteur (~31×) puis le 9 % pour le corriger (40×) — donc le narratif a **changé de valeur selon le besoin**, même si chaque usage était déclaré.

### I4 — Le chiffre-vedette n'est pas une propriété stable. ⭑⭑
Le facteur de croissance de la variante B : **×7,50** (C1 memtable RF1), **×5,94** (C3 disque RF3), **×1,52** (post-flush lecture SSTable). Un **intervalle de 5×**. Le « 0,77 ms/Kio » et le « ×7,50 » sont des **artefacts de régime memtable** ; C2/M15 l'a prouvé. Citer un taux unique comme *le* coût de mutation de HCD est **trompeur** — il dépend du régime et du matériel, et s'effondre quand la lecture touche le disque. Or ce taux est le socle de M3/M10/M11/M12/M13 et de la première ligne de trois rapports.

### I5 — L'ADR déclare l'action 1 « done » alors qu'une mesure ultérieure la sape. ⭑
Action 1 = « reproduire le ×7,50 en régime disque prouvé » → cochée `[x]` (M10). Mais **M15 a établi qu'aucune lecture disk-bound n'a jamais été mesurée** : M10 a mis un *jeu de données* sur disque, pas la *lecture sondée*, qui restait en memtable. Quand on force la lecture sur disque (M15), le coefficient s'effondre à ×1,52. **L'action reste cochée** — le dossier porte une action « fermée » qu'une mesure postérieure a partiellement invalidée sans rouvrir.

### I6 — Contamination environnementale jamais quantifiée. ⭑
Les campagnes 4–6 ont tourné sur un anneau portant **6–13 Gio de `system.paxos`** et une charge tierce (load 14–16). Cette pression mémoire/CPU a pu **ralentir HCD** dans M12/M13/M16 — jamais mesurée, jamais soustraite. Les absolus HCD sont donc un **plafond bruité**, pas une mesure propre.

### I7 — Faiblesse statistique. ⭑
n = 30–50 par point, 2 passes, **médianes seules, aucun intervalle de confiance**, aucun test de significativité. Variance inter-passes ~10–15 % (×1,92 vs ×2,21) **supérieure à certains effets revendiqués**. r² faibles côté MongoDB (0,78 ; 0,88) — pentes quasi nulles noyées dans le bruit. Client unique séquentiel : **rien sur la concurrence**, qui est le régime de production.

### I8 — La comparaison n'est jamais vraiment appariée. ⭑
HCD (anneau 3 nœuds + niveau Data API + ronde Paxos) contre MongoDB (tantôt RS 3 membres, tantôt `atlas-local` 1 membre pour la fraîcheur). **Deux déploiements MongoDB différents** dans les campagnes 5–6. Le niveau et le Paxos sont inhérents à HCD mais font que c'est **pile-contre-pile, pas moteur-contre-moteur** — partiellement corrigé par M14 (mutation) mais **pas** pour la lecture (I15 des challenges).

### I9 — Des magnitudes qui sont des artefacts de configuration ou de plancher. ⭑
Le « ~1 s de lag mongot » (M17) est le **défaut d'`atlas-local` au repos** (intervalle de commit), pas une propriété de MongoDB Search (C10). Le « HCD synchrone, zéro lag » est « **< 45 ms**, sous le plancher HTTP » (C11), pas prouvé zéro. Les deux magnitudes-vedettes de l'axe favorable à HCD sont des artefacts.

## Ce que l'audit CONFIRME comme fiable
- **M1** (schéma, 12 colonnes/9 SAI) et **M2** (cycle SELECT→UPDATE IF, 11 affectations) : lectures directes du moteur, deux passes, indépendantes du mesureur. **Inattaquables.**
- **Les directions**, partout : HCD plus cher sur la mutation ; MongoDB plus cher sur la fraîcheur de recherche ; les octets dominent le nombre de champs (M11, r² 0,9999, script fourni). Robustes aux challenges.
- **La restauration de l'anneau** : 20 index recréés == 20 définitions capturées, keyspaces supprimés, snapshots purgés, tracing 0. Vérifié à chaque campagne.

## Bilan de l'audit
**Le dossier est fiable comme récit qualitatif et comme vérification de mécanisme ; il ne l'est PAS comme source de chiffres publiables.** Les *directions* survivent l'audit ; les *magnitudes* (44×, 0,77 ms/Kio, ×7,50, 1 s, 40×, 22×) sont chacune entachées d'un régime, d'une pile, d'une configuration ou d'un plancher — et le dossier viole la norme en six points qu'il impose aux autres. 

Ironie utile : c'est **exactement ce que la Disclosure du diptyque affirmait** — « aucun chiffre de benchmark dans le corps de l'article ». L'audit valide ce choix *a posteriori* : ces chiffres n'auraient jamais dû être présentés autrement qu'en annexe, avec toutes leurs conditions, comme mesures d'**un build sur une machine un jour** — ce que le marqueur [M] dit déjà.

**Trois corrections que l'audit exige avant toute publication :**
1. **Rouvrir l'action 1** de l'ADR (I5) : le régime disque du chemin de lecture n'a pas été mesuré proprement ; M15 est le vrai résultat, et il change le coefficient.
2. **Réconcilier ou étiqueter le terme niveau** (I3) : 9 % ou 29 %, pas les deux sans explication.
3. **Re-qualifier tout taux « par Kio » comme memtable** (I4) : le nombre ne se transpose pas ; seul le mécanisme le fait.

Aucune de ces corrections n'exige une nouvelle mesure — seulement de cesser de présenter des artefacts de régime comme des propriétés de moteur.
