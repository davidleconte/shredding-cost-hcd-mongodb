> **English abstract.** The four aggregation measurements (M20–M23) were the only figures in this
> repository published without an adversarial pass, and `LIMITATIONS.md` says so. This document
> supplies that pass: nine challenges, D6–D14. **No conclusion is reversed.** Two challenges
> *strengthen* the headline. D7 decomposes the 134-second client scan, but not the way the first
> draft of this document did: the per-page cost is recoverable from the measurement alone —
> 133 984.229 ms over 10 000 pages of 20 documents is **13.398 ms per page**, with no residue left
> to explain, so the 602× is a documented page-size limit multiplied by a measured per-call cost,
> and the claim upgrades from [U] to [M]. D8 reclassifies the 1 000-document count ceiling from
> measured discovery to documented behaviour — while noting that the measurement *contradicts* the
> documentation's phrasing: the probe set `upper_bound = 400 000` and the server ignored it, so the
> user control the documentation implies does not exist on this build. One challenge *narrows*:
> D9 bounds `estimatedDocumentCount() = 0` to the pre-flush cold start, which was the only state
> measured. One is *resolved against the challenger*: D10 asked which index state the MongoDB
> `$group` ran under — the probe source answers it (`cat_idx` was present) and the data shows the
> index was irrelevant, since `$sum: "$amt"` cannot be served by an index on `cat` alone.
> Three challenges are new and were missed by the first pass: **D12**, the native-CQL reference arm
> was never itself challenged — and challenging it partly *refutes* how the campaign labelled it;
> **D13**, a 46× ingest asymmetry reported by the campaign and never interrogated, which confounds
> a documented batch ceiling with per-document shredding cost; **D14**, "aggregation" was
> operationalised as exactly one query shape, which is a construct-validity limit nobody raised.
> What changes overall is the framing: on this axis the durable finding is not a multiplier but an
> **absence of function**, statable in three sentences that contain no percentile.
>
> *Document body below is in French. Raw evidence: `data/raw/findings_agg_hcd.json`,
> `data/raw/findings_agg_mongodb.json`, `data/raw/findings_agg_cqlref.json`. Probes:
> `probes/probe_aggregation.py`, `probes/agg_cql_arm.py`. Campaign report:
> `docs/campaigns/07-aggregation.fr.md`. Statistical treatment: `docs/STATISTICS.md`.*

---

# Challenges — campagne 7 (M20–M23), au même feu adverse

18 septembre 2026. Contre les quatre mesures d'agrégation, qui n'en avaient reçu aucun.

`LIMITATIONS.md` déclare que M20–M23 sont les seuls chiffres du dépôt jamais passés au feu adverse :
`challenges.fr.md` couvre M1–M13, `audit-adversarial.fr.md` couvre M1–M17. Ce document ferme cette
lacune. Il est écrit contre la campagne 7, pas pour elle.

## Les objections qui changent le statut d'une mesure

### D7 — Le 134 s se décompose, mais pas avec la constante qu'on croyait. ⭑

Le rapport de campagne écrit que « la décomposition du 134 s en un terme allers-retours et un terme
moteur n'a pas été mesurée ». Une première version de ce challenge a voulu la fournir en important le
p50 de lecture ponctuelle de M16 — 10,382 ms — et concluait : dix mille allers-retours à 10,382 ms
font 103,8 s, soit 77 % du total, le reste étant transfert et sommation.

**Cette dérivation est fausse, et son résidu de 30 s est un artefact de la mauvaise constante.**
M16 mesure `findOne({_id})` : **un** document, sur la collection `rs_probe` de 1 M documents, en
**campagne 6**. Le bras C2 pagine `agg` — 200 k documents, campagne 7 — par pages de vingt. Trois
différences simultanées : l'opération, la collection, la campagne. On ne substitue pas l'une à
l'autre.

La décomposition n'a besoin d'aucune importation. Elle se lit dans la mesure elle-même :

```
133 984,229 ms  ÷  (200 000 / 20)  =  133 984,229 ÷ 10 000  =  13,398 ms par page
```

Contre 10,382 ms pour une lecture ponctuelle : **+3,016 ms, soit +29 %** — exactement ce qu'on
attend du surcoût de charge utile de vingt documents contre un. Ce surcoût est *dans* l'aller-retour,
il n'est pas à côté.

Il n'y a donc pas « 104 s d'allers-retours plus 30 s d'autre chose ». Il y a **dix mille
allers-retours séquentiels à 13,4 ms, et rien d'autre**. Le produit rend le total, sans reliquat.

**Conséquence, et elle renforce M23 :** le 602× n'est ni un mystère de moteur ni un artefact de
sonde. C'est **une limite de pagination documentée multipliée par un coût par appel mesuré**, et un
lecteur ne peut pas s'en défaire en réglant la taille de page, puisqu'elle est plafonnée par le
produit. Le marqueur passe de **[U]** à **[M]** : 13,398 ms/page est une division sur une grandeur
mesurée, pas une dérivation croisant deux campagnes.

**Réserve qui doit voyager avec D7.** Tout repose sur la taille de page à vingt. Elle a été établie
empiriquement dans cette session par sonde brute sur l'API (20 documents rendus par page, plus un
`nextPageState`), et non seulement lue dans la documentation de l'éditeur. C'est à cette sonde qu'il
faut la citer. Si une version ultérieure change ce défaut, D7 ne vaut plus.

### D8 — Le plafond de comptage est documenté — et la mesure contredit la documentation. ⭑

Le rapport traite `TooManyDocumentsToCountException` à 1 000 comme une découverte. La documentation
de l'éditeur, sur la page `countDocuments`, décrit le mécanisme : le comptage exact est présenté
comme une opération lente et coûteuse, et lorsque le nombre de documents dépasse la limite haute,
c'est une indication de cette limite qui est rendue à la place du compte. La référence Astra du même
point d'API est plus nette : le comptage exact d'un nombre arbitraire de documents n'y est pas
supporté. Le **mécanisme** passe donc de **[M]** à **[D]** ; seule la **valeur** 1 000 reste mesurée.

Deux précisions que la première version de ce challenge laissait sur la table, et la première joue
**en faveur du dossier** :

1. **La documentation évoque une limite « fixée par vous ou par l'API ». Sur ce build, « par vous »
   ne relève rien.** La sonde a explicitement demandé `upper_bound = max(n × 2, 1000) = 400 000`
   (`probes/probe_aggregation.py`). Le serveur l'a ignoré et a appliqué son propre plafond de 1 000.
   Le contrôle utilisateur que la formulation suggère n'existe pas ici. C'est une **mesure qui borne
   la documentation**, et elle mérite d'être dite.
2. **La page consultée est celle de HCD 1.2, pas 2.0.6.** Même réserve d'édition que l'article
   applique partout. Le reclassement [M] → [D] est donc lui-même conditionnel.

Cela ne rend pas HCD meilleur : une API qui ne compte pas au-delà d'un seuil reste une API qui ne
compte pas. Mais cela **déplace la critique**, et c'est le meilleur geste de ce document : le vrai
problème n'est pas le plafond, qui est déclaré, c'est le **substitut recommandé par l'éditeur**, qui
a répondu zéro (M22).

### D9 — M22 est une propriété du démarrage à froid, présentée comme une propriété tout court.

`estimatedDocumentCount() = 0` a été lu quelques minutes après un chargement de 185,3 s, sans qu'aucun
flush n'ait eu lieu — le zéro lui-même le prouve, et le rapport en tire justement que toute la
campagne est en régime cache.

Mais alors la lecture correcte est bornée : **avant le premier flush, l'estimation est nulle.** Ce
que vaut l'estimation en régime permanent, après flush et compaction, **n'a pas été mesuré**. « Pas
approximatif, faux » est vrai de la condition mesurée et doit lui être restreint.

Le danger applicatif décrit reste entier et reste le point — un applicatif qui teste `if count == 0`
sur une collection fraîchement chargée conclut qu'elle est vide — mais il concerne une **fenêtre de
temps**, pas un état durable. La mesure qui fermerait D9 est triviale : `nodetool flush`, puis relire.
Elle n'a pas été faite.

## Les objections de portée

### D6 — `n = 3` sur le bras HCD, et l'argument est plus fort quantifié.

La première version disait : écart-type 567,7 ms sur 133 984 ms, soit 0,42 % ; à un effet de 602×,
une erreur d'un facteur deux laisserait encore 300× ; la direction est inattaquable. Vrai, mais mou.
La version quantifiée, calculée depuis les JSON bruts et détaillée dans `docs/STATISTICS.md` :

| | |
|---|---|
| Supports | **disjoints** — HCD min 133 827,164 ms, MongoDB max 293,734 ms |
| p exacte de permutation | `1 / C(18,15)` = **1,23 × 10⁻³** |
| Rapport des médianes | 601,6× |
| Intervalle honnête du rapport | **[455,6× ; 625,6×]** |

Le point qui compte n'est pas que l'effet résiste. C'est que **le plancher de la p-valeur est fixé
par `n = 3`, pas par l'effet**. L'effet est astronomique ; la preuve vaut p ≈ 0,001, parce que trois
répétitions ne permettent pas mieux, quelle que soit l'ampleur. Trois exécutions de plus la portaient
sous 10⁻⁵. C'est le seul endroit du dossier où la parcimonie a coûté cher pour rien — le bras
coûtait 134 s l'unité.

Les p95 et p99 du bras HCD sont sans information : avec `n = 3`, le 95ᵉ percentile est une
interpolation entre la deuxième et la troisième observation. Le rapport le dit déjà.

### D10 — RÉSOLU. La question se ferme dans la source, et l'index était sans effet.

Le challenge demandait sous quel état d'index le `$group` de MongoDB à 222,711 ms avait tourné, le
rapport ne le disant pas explicitement.

`probes/probe_aggregation.py` répond : `coll.create_index([("cat",1)], name="cat_idx")` est appelé
**avant** la mesure de C1. Le bras a donc tourné **avec** l'index.

Mais l'index est **inopérant pour cette requête**. Il porte sur `cat` ; l'agrégation demande
`$sum: "$amt"`. Un index sur `cat` seul ne couvre pas `amt`, donc MongoDB doit aller chercher chaque
document pour lire la valeur à sommer. Les données le corroborent sans ambiguïté :

| Opération | p50 | Ce que ça implique |
|---|---|---|
| `count({cat:"c3"})` **servi par `cat_idx`** | 12,659 ms | lecture d'index seule |
| `$group` + `$sum: "$amt"` | 222,711 ms | **17,6× plus** — signature d'un balayage complet |

Verdict : **index présent, index inopérant, le chiffre est bien un balayage de collection.** Le 602×
ne bouge pas. La recommandation de fond du challenge reste juste et doit être retenue pour les
campagnes futures : **l'état d'index de chaque bras doit figurer dans le JSON de résultat**, pas
seulement dans le code de la sonde.

### D11 — Ce que HCD sait faire ailleurs n'a pas été essayé.

Les tables Data API (option D de l'ADR, désactivées par défaut) n'ont pas été testées sur
l'agrégation ; un moteur analytique externe branché sur l'anneau — Presto, Spark — non plus. Le
rapport le liste dans ce qu'il n'établit pas.

Le constat porte sur la Data API **telle qu'exposée par défaut**, et c'est le bon périmètre puisque
c'est le produit comparé. Mais un lecteur qui déploie HCD avec un moteur analytique à côté n'a pas ce
problème, et il faut le dire à l'endroit où il le lira, pas seulement en fin de rapport.

## Trois challenges que la première passe a manqués

### D12 — Le bras CQL n'a jamais été challengé — et le challenger se trompe à moitié. ⭑

Le bras de référence CQL est étiqueté pommes-contre-oranges dans son propre fichier de résultat, et
la campagne en tire que l'atteindre « exige d'abandonner le modèle document **et de pré-concevoir
une table partitionnée par la clé de groupe** ». Personne n'a attaqué l'étiquette elle-même.

L'attaque évidente : la table a été créée `cmp.agg_cql(cat, id, amt) PRIMARY KEY(cat, id)` —
pré-partitionnée par exactement la clé que la requête regroupe. C'est le **meilleur cas possible**,
pas un cas représentatif.

**Et les données réfutent en partie cette attaque.** Le bras C3b mesure précisément le cas où la
table n'est *pas* alignée sur la requête — un `GROUP BY cat` inter-partitions, balayage complet côté
coordinateur, l'anti-patron reconnu :

| | p50 | vs le cas idéal |
|---|---|---|
| C3a — balayage par partition, table alignée | 2 011,399 ms | référence |
| C3b — `GROUP BY` inter-partitions, non aligné | 2 568,372 ms | **×1,28 seulement** |

Un écart de 28 %, pas un ordre de grandeur. **À cette échelle et à cette cardinalité, l'affirmation
« le moteur agrège en ~2 s » survit au choix de partitionnement.** La seconde moitié de la phrase de
la campagne — « et de pré-concevoir une table partitionnée par la clé de groupe » — **est
surdimensionnée par ses propres chiffres.**

Ce qui reste vrai de l'étiquette : il faut bel et bien **abandonner le modèle document**. Ça, aucun
chiffre ne l'entame, et c'est l'essentiel de l'argument.

Ce qui reste vrai de l'attaque : 200 000 lignes sur dix partitions est un balayage minuscule. Un
balayage complet côté coordinateur dégrade mal avec le volume et finit par expirer. Le C3b mesuré ne
dit rien de ce qui arrive à 10⁸ lignes. **Donc l'anti-patron est réel et la magnitude mesurée ne le
montre pas** — ce qui est exactement le reproche que le dossier s'adresse ailleurs (I4) à propos du
taux par kio.

### D13 — Une asymétrie d'ingestion de 46×, rapportée et jamais interrogée. ⭑

Les trois bras ont chargé le même corpus de 200 000 documents, et la campagne publie les trois
durées sans les commenter :

| Bras | Chargement | Débit | Taille de lot |
|---|---|---|---|
| MongoDB | **4,0 s** | ~50 000 doc/s | 10 000 (`insert_many`) |
| CQL natif | 68,9 s | ~2 900 doc/s | `execute_concurrent`, 64 en vol |
| HCD Data API | **185,3 s** | ~1 080 doc/s | **100** (`insertMany`) |

**46,3× entre les extrêmes**, sur le même axe que la campagne, jamais challengé.

Mais le chiffre ne peut pas être cité tel quel, parce que la mesure **confond deux causes** :

1. **Le plafond de lot.** La Data API limite `insertMany` à **100 documents par appel** — encore une
   limite produit, même forme que D7. 200 000 ÷ 100 = **2 000 appels** à 92,65 ms. MongoDB fait
   **20 appels** de 10 000 documents à ~200 ms. Cent fois moins d'allers-retours.
2. **Le coût de shredding par document**, qui est le mécanisme central de tout le dossier.

Une seule taille de lot a été essayée par moteur, donc **rien ne sépare les deux termes**. C'est un
défaut de validité de construit dans la mesure de chargement : le 46× est « ce client, à la taille de
lot propre à chaque moteur », pas « HCD ingère 46× moins vite ». La mesure qui séparerait les deux
existe et est simple — faire varier la taille de lot MongoDB jusqu'à 100 pour l'apparier — et elle
n'a pas été faite.

**Ce que D13 établit malgré tout :** la Data API plafonne les écritures groupées à 100 par appel,
c'est documenté, et à 200 000 documents cela impose 2 000 allers-retours là où MongoDB en fait 20.
Comme pour la lecture (D7), la limite est structurelle et le client ne peut pas la contourner.

### D14 — « L'agrégation » a été opérationnalisée par une seule forme de requête.

Aucun challenge de la première passe ne porte sur la **validité de construit** de l'axe. Le construit
est « agréger » ; l'opérationnalisation est : un `GROUP BY` sur une clé à **faible cardinalité**
(dix groupes exactement), un `SUM` d'un `double`, sans filtre, sans tri, sans jointure, sur un
corpus uniforme de 200 000 documents.

Rien n'a été mesuré de : regroupement à **forte cardinalité** (10⁵ groupes — où le coût mémoire de
`$group` de MongoDB devient le facteur dominant et peut le forcer à déborder sur disque) ; pipelines
**multi-étages** ; agrégation **filtrée**, où un index peut réduire l'entrée avant le regroupement ;
`$lookup` ; percentiles ou `$stdDevPop` ; ni agrégation **incrémentale** sur flux.

Pour M20 — l'absence de pipeline côté serveur — cela ne change rien : l'absence est totale, elle ne
dépend d'aucune forme de requête. **Pour M23, cela borne le chiffre à une forme de requête**, et c'est
plausiblement la forme la plus favorable à MongoDB qu'on puisse choisir, puisque dix groupes tiennent
dans un espace de travail trivial. Un regroupement à forte cardinalité pourrait réduire l'écart. Il
pourrait aussi le creuser — le scan client de HCD, lui, ne dépend pas du nombre de groupes. **Rien
dans le dossier ne permet de trancher**, et c'est la lacune qu'un examinateur relèverait avant D6.

## Ce qui résiste sans une égratignure

**M20 — il n'y a pas d'agrégation côté serveur dans la Data API.** Dix-neuf commandes dans la liste
d'autorisation ; `aggregate`, `$group` et `distinct` répondent `COMMAND_UNKNOWN`. C'est une lecture
de l'API, indépendante du matériel, de la charge, du régime, de la taille du corpus et de la forme
de la requête. Ni D6, ni D12, ni D14 ne l'entament. C'est le fait le plus solide de la campagne, et
il ne porte aucun percentile.

**M23, en direction.** MongoDB agrège côté serveur, la Data API ne le peut pas, et le seul chemin
restant fait traverser le réseau à la collection entière. Supports disjoints, expliqué par D7,
robuste à D6.

## Verdict

Neuf challenges, **aucune conclusion inversée**.

Deux mesures ressortent **plus fortes** : le 602× a maintenant une décomposition exacte et sans
reliquat (13,398 ms × 10 000 pages) et une origine documentée, et le plafond de comptage est un
comportement déclaré par l'éditeur — dont la mesure montre au passage qu'il n'est pas relevable par
le client, contrairement à ce que la formulation de la documentation suggère.

Une ressort **bornée** : le zéro de l'estimation est une propriété du démarrage à froid.

Une est **résolue contre le challenger** : l'index de MongoDB était bien présent, et sans effet.

Trois sont **neuves**, et deux d'entre elles se retournent en partie contre le dossier : la charge
de pré-conception que la campagne impute au chemin CQL est surdimensionnée par ses propres chiffres
(D12), et l'écart d'ingestion de 46× confond un plafond de lot documenté avec le coût de shredding
(D13). La troisième borne M23 à une seule forme de requête (D14).

**Le déplacement qui compte pour le diptyque** : sur cet axe, le fait à retenir n'est pas un
multiplicateur mais une **absence de fonction**. La Data API n'agrège pas, ne compte pas au-delà d'un
seuil, et son estimateur rend zéro avant le premier flush. Ce sont trois phrases sans percentile, et
elles survivent à tout ce que ce dossier a appris à casser.
