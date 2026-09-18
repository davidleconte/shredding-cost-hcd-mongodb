> **English abstract.** This is the dossier under hostile fire, written against itself rather than for itself. It raises fifteen challenges (C1–C15) plus five second-order ones (D1–D5), and — this is the structural point — it does not stop at raising them: four were then **measured**, and the measurements are folded back in as dated resolutions. The three wounds that touched a published conclusion were C1 (the headline 44× mutation gap compares *stacks*, HCD-through-the-Data-API against MongoDB-through-its-native-driver, not storage engine against storage engine), C2 (nowhere in the dossier does a genuinely disk-bound read-modify-write measurement exist — every RMW probe re-reads the row it just wrote, which stays memtable-resident), and C3 (the Paxos cost is measured between three replicas sharing one host, i.e. at sub-millisecond inter-replica latency, which is where consensus hurts least). The measured resolutions reversed two of them: C1 was **partly refuted** — the gap is almost all engine, not tier, so the honest engine-versus-engine figure came out *higher* than the deflation predicted — while C2 was **confirmed**, and confirming it cost the dossier its flagship number, since the per-byte mutation coefficient turned out to be a memtable phenomenon that collapses from ×7.50 to ×1.52 once the read half is forced onto an SSTable. The campaign-6 pass added C10 (the “~1 s mongot lag” is a configuration default, not a floor — later measured and reduced to a ~1.1 s refresh interval with a p50 of 664.3 ms) and C11 (“HCD synchronous, zero lag” is really “lag below 45 ms”, under the HTTP floor, never shown to be zero). D1–D5 then attack the resolution of C10 itself, and D1 — that a sub-second search lag may be moot for the RAG turn latency that motivates caring about it — was measured too. Readers should treat this document, not the campaign reports, as the real boundary of what the numbers may be used for.
>
> *Document body below is in French. It is the working adversarial record, kept in the language it was written in and in chronological order, including the resolutions that overturned earlier verdicts. An English synthesis of the same material, reorganised by severity, is in [LIMITATIONS.md](../LIMITATIONS.md).*

---

# Challenges — le dossier au feu adverse (M1–M13)
18 septembre 2026. Rédigé contre le dossier, pas pour lui.

## Les trois blessures réelles (celles qui touchent une conclusion publiée)

### C1 — M13 compare des PILES, pas des moteurs de stockage. ⭑ la plus forte
Le 44× (et le 79×) oppose **HCD conduit par la Data API** — HTTP + analyse JSON + shredding + **ronde Paxos** — à **MongoDB conduit par son pilote natif**. Or M12 établit que **~29 % du coût HCD est le niveau sans état**. Une comparaison moteur-contre-moteur honnête piloterait HCD en **CQL direct** (le bras B de la campagne 4) contre pymongo direct — pas via la Data API. Retranchez le niveau : le terme stockage HCD est ~0,55 ms/Kio, soit encore **~31× le MongoDB wildcard**. MongoDB gagne toujours largement, **mais le chiffre honnête pour « moteur vs moteur » n'est pas 44×, c'est ~31×**, et le 44× inclut un composant que HCD absorbe horizontalement.
**Verdict : la direction survit, le multiplicateur est gonflé.** Le rapport le dit (« mesure les piles telles que déployées »), mais la première phrase cite 44× sans ce dégonflage. À corriger : donner les deux ratios (pile 44×, moteur ~31×).
**Mesure qui fermerait la plaie** : un troisième bras HCD-CQL-direct dans `probe_comparative.py`.

### C2 — Il n'existe AUCUNE mesure RMW réellement disk-bound dans tout le dossier.
La campagne 3 est titrée « régime disque », et M10 est étiquetée « le coefficient tient sous disque ». Mais la sonde RMW **relit la ligne qu'elle vient d'écrire** — chaude, en memtable, quelle que soit la taille du jeu. Le remplissage de 6 Gio crée une **pression mémoire**, il ne met jamais la ligne sondée sur disque. Donc M10 n'est pas un coefficient disk-bound ; c'est un coefficient **memtable sous pression**. L'action 1 de l'ADR voulait « forcer les lectures depuis le disque » ; elle a obtenu un **jeu de données** sur disque, pas une **lecture** depuis le disque.
**Verdict : « action 1 done » est trop généreux.** Le régime disque est prouvé pour le *dataset*, pas pour le *chemin de lecture de la sonde*. Le dossier le déclare en confondant, mais l'étiquette M10 « does not collapse under disk » surinterprète.
**Mesure qui fermerait la plaie** : `nodetool flush` du keyspace de sonde ENTRE l'insert et les updates, pour forcer le SELECT du cycle à toucher une SSTable ; ou vider le page cache (exige root, indisponible).

### C3 — Le coût Paxos est mesuré sans latence réseau.
M5 observe la ronde Paxos tri-réplicas — vrai gain sur la campagne 1 (RF=1 trivial). Mais les trois réplicas dc1 **partagent un hôte** : latence inter-réplicas sub-milliseconde. Le coût du consensus est donc mesuré là où il fait le **moins** mal. Sur un vrai déploiement multi-hôte/WAN, la ronde Paxos coûte des dizaines de ms — l'axe où HCD souffre le plus, et où l'écart M13 se **creuserait** encore.
**Verdict : structure établie, magnitude non représentative.** Cela joue *contre* HCD en production, donc ne flatte pas le dossier — mais aucun chiffre du dossier ne vaut pour un multi-hôte.

## Les objections de méthode (n'annulent rien, pèsent sur la portée)

### C4 — Tout est un hôte, une build, une VM partagée.
`alphadebunker`, HCD 2.0.6, data-api v1.0.33, MongoDB 8.0.32. Rien ne se transpose. La classe de stockage physique n'a **jamais** pu être établie (QEMU virtuel). Un banc sur un NVMe dédié ou un disque réseau lent donnerait d'autres absolus. **Déclaré partout ; reste la limite-mère.**

### C5 — Le mesureur a écrit et corrigé des instruments.
La garantie « instrument que je n'ai pas écrit, donc que je ne peux pas truquer » est **entamée** là où j'ai codé (`method2_trace.py`, campagne 4) ou patché les scripts fournis (astrapy `Environment.HCD` ; `indexing.deny` ; driver disque `docker exec` + payload incompressible ; clé tuple en instructions préparées). **Chaque correctif est déclaré et justifié mécaniquement**, mais un sceptique les compte : les verdicts reposant sur un script fourni **non modifié** (M11 champ/octet, M13 via `probe_comparative` intact) sont plus solides que ceux reposant sur mon code (M2 trace, M12 méthode 2).

### C6 — La correspondance de durabilité de M13 favorise HCD, pas MongoDB.
MongoDB `j:true` attend le fsync du journal **avant** d'acquitter ; HCD `commitlog_sync periodic 10 s` acquitte **avant** le fsync (jusqu'à 10 s d'écritures acquittées perdables). Donc dans l'appariement, **HCD a acquitté sans attendre le disque et MongoDB a attendu** — un avantage de latence donné à HCD. Il perd quand même 44×. **Cette objection se retourne : elle renforce la conclusion « MongoDB gagne ».** À dire explicitement dans le rapport, car elle transforme une faiblesse apparente en robustesse.

### C7 — M12 ne publie pas de partage précis, et son bras B est artificiel.
Les deux méthodes divergent > 25 % aux grandes tailles ; le 29 %/19 % est une fourchette, pas un point. Le bras B **réutilise des valeurs déjà décomposées** — il n'exerce jamais le code de shredding, donc son « stockage » est un plancher optimiste et le « niveau » peut être sur- ou sous-estimé. Le terme niveau **agrège** parse+shred+sérialisation sans les séparer. **Le 70/30 est une direction, pas un chiffre.** C1 en dépend : si le vrai niveau est plus proche de 40 %, le ratio moteur-vs-moteur de C1 (~31×) descend encore.

### C8 — Le reliquat Paxos contamine peut-être ses propres mesures.
Les campagnes 4 et 5 ont tourné sur un anneau portant déjà **6–13 Gio/nœud de `system.paxos`** non purgé. Cette masse crée une pression mémoire/compaction de fond qui a pu **ralentir HCD** dans M12 et M13. Effet probablement petit, **non contrôlé**, jamais quantifié. Un banc propre relancerait sur un anneau à paxos vide.

### C9 — Un seul axe, et c'est l'axe où HCD est censé perdre.
M13 mesure la mutation d'un champ — précisément là où la décomposition de HCD coûte cher **par conception**. Le dossier ne mesure **rien** de la lecture filtrée, de la recherche vectorielle, de l'agrégation, ni de la **fraîcheur d'index à l'acquittement** — l'axe où HCD a son avantage structurel (M7 n'a pu que le borner sous le plancher HTTP). **Un dossier qui ne mesure que l'axe défavorable à HCD serait aussi biaisé qu'un dossier complaisant.** Le rapport le déclare ; il n'y remédie pas. C'est la plus grande lacune de couverture.

## Ce qui résiste sans une égratignure
- **M1** (12 colonnes, 9 SAI) : lecture directe du schéma, deux passes identiques. Inattaquable.
- **M2** (cycle SELECT→UPDATE IF, 11 affectations) : trace CQL, 10/10. La build peut changer, l'observation non.
- **M11** (les octets dominent le nombre de champs) : r² 0,9999 sur la série octets ; script fourni non modifié. La plus robuste des mesures dérivées.
- **M13, direction** (MongoDB gagne nettement sur la mutation) : robuste à C1 (~31× après dégonflage), à C6 (l'appariement favorisait HCD), au régime. Le **multiplicateur** est discutable, pas le **sens**.

## Verdict global
Le dossier **survit comme récit qualitatif** et se **vindique** sur sa thèse centrale : la décomposition rend la mutation d'un champ chère, mesurablement, et MongoDB est structurellement moins cher sur cet axe. Il est **fragile sur trois points chiffrés** : le multiplicateur 44× confond pile et moteur (C1) ; « disk-bound » n'a jamais touché la lecture sondée (C2) ; le coût Paxos est sans réseau (C3). Il est **muet** sur l'axe favorable à HCD (C9). Aucun de ces points n'inverse une conclusion ; tous rétrécissent ce qu'elle a le droit d'affirmer. Le correctif le plus rentable : ajouter le bras **HCD-CQL-direct** à la comparaison (ferme C1 et éclaire C7), et une passe RMW **post-flush** (ferme C2).

---

# Résolution mesurée — C1 et C2 (18 septembre 2026)

Les deux plaies chiffrées ont été rejouées sur le dispositif. Résultat : **une de mes objections était trop généreuse, l'autre tenait mais avec sa propre réserve.** Un red-team qui ne se corrige que dans un sens ne vaut pas mieux qu'un dossier complaisant.

## C1 — RÉFUTÉE en partie : le 44× est presque tout du moteur, pas de la pile.
Bras **HCD-CQL-direct** ajouté (`hcd_cql_arm.py`), même hôte, même série, régime cache apparié, gate `--compare` = permitted.

| Bras | Pente (ms/Kio) | r² |
|---|---|---|
| mongo-wildcard | 0,0176 | 0,88 |
| **hcd-cql-direct** (moteur nu, niveau retiré) | **0,7037** | 0,996 |
| hcd via Data API (pile) | 0,7775 | 0,997 |

Retirer le niveau ne baisse la pente que de **9 %** (0,777 → 0,704), pas les 29 % que j'avais extrapolés de M12 (régime disque, bras entrelacés). **Ratio moteur-contre-moteur : 40× wildcard, 72× default** — contre 44×/79× pour la pile. **Mon estimation de ~31× était fausse : le désavantage de HCD est presque entièrement dans le moteur de stockage, pas dans le niveau.** La victoire de MongoDB est un résultat de moteur, pas un artefact de pile. (Note : le partage niveau/stockage reste instable entre régimes — 9 % ici en cache cross-run, 29 % en M12 disque entrelacé ; c'est la même imprécision que M12 déclarait, et elle ne change pas le fait que ~90 % de la pente est du stockage.)

## C2 — CONFIRMÉE, avec une réserve neuve : le coefficient par-octet est un phénomène memtable.
Passe **RMW post-flush** (`rmw_postflush.py`) : `nodetool flush` avant chaque update, pour que le SELECT interne touche une SSTable au lieu de la memtable. Variante B, comparable à M10.

| Taille | memtable (M10, disque) | **post-flush (SSTable)** |
|---|---|---|
| 1 Ko | 20,4 ms | **107,8 ms** |
| 128 Ko | 121,2 ms | **163,4 ms** |
| **croissance** | **×5,94** | **×1,52** |

Deux enseignements. **(a) Ma plaie tenait** : la lecture RMW n'avait jamais quitté la memtable ; l'y forcer ajoute un coût fixe massif (~90–100 ms). M10 « le coefficient tient sous disque » **surinterprétait** — M10 n'avait jamais mesuré une lecture disque. **(b) Le coefficient par-octet s'effondre** (×5,94 → ×1,52) quand la lecture est disk-bound : un gros coût fixe de chemin SSTable domine, et la croissance par octet indexé — le taux de 0,77 ms/Kio, le cœur du §3 — devient un **phénomène de régime memtable**. Hors memtable, c'est le chemin de lecture qui décide, pas le volume indexé.

**Réserve neuve, déclarée** : flusher avant *chaque* update crée une SSTable par flush → jusqu'à ~35 petites SSTables à fusionner par SELECT, une fragmentation qu'une compaction normale n'aurait pas. L'absolu ~100 ms est donc **gonflé** par cette fragmentation ; le vrai disk-bound (avec compaction) se situe **entre** le memtable (12–91 ms) et ce pire cas fragmenté. Le page cache n'est toujours pas vidable (pas de root), donc « SSTable » ≠ « plateau froid ».

## Ce que ces deux mesures changent au dossier
- **Le multiplicateur MongoDB est un fait de moteur** (40×), pas un artefact de la Data API. Plus fort pour MongoDB que ne le laissait croire mon challenge.
- **Le coefficient de 0,77 ms/Kio doit être re-qualifié** : c'est un taux **memtable**. Le §3 du diptyque reste juste sur le mécanisme (lecture-modification-réécriture, coût qui suit le contenu indexé) mais le *taux chiffré* ne se transpose pas à un régime où la lecture touche le disque — là, un coût fixe de chemin SSTable domine. M10/M11/M12/M13 sont tous des taux memtable/cache.
- **Aucune conclusion n'est inversée** ; deux sont resserrées, une de mes objections est corrigée. C'est le sens que doit avoir un feu adverse honnête.

---

# Challenges — campagne 6 (axes favorables à HCD), au même feu adverse
18 septembre 2026. Contre les résultats HCD-favorables, avec la même dureté que contre les résultats MongoDB.

## Les deux blessures réelles

### C10 — Le « ~1 s de lag mongot » est très probablement un DÉFAUT de configuration, pas un plancher. ⭑ la plus forte
mongot ingère via change stream et commit son index à un **intervalle configurable**. Le ~1015 ms mesuré est remarquablement **stable** (écart-type 35 ms, médiane 34 tentatives ≈ 34 × 20 ms de poll + un intervalle de commit fixe) — la signature d'un **intervalle périodique**, pas d'un coût de travail. Sur Atlas en production ou avec un mongot réglé, ce délai peut descendre à quelques centaines de ms. **Ce qui survit : la direction (async vs sync), robuste.** **Ce qui tombe : le chiffre « 1 seconde »**, qui est le défaut d'`atlas-local` au repos, pas une propriété fondamentale de MongoDB Search. Le rapport le dit à demi-mot (« ~1 s au repos, une charge le creuserait ») mais met le 1 s au tableau sans le qualifier de défaut.
**Mesure qui fermerait la plaie** : faire varier l'intervalle de commit de mongot et re-mesurer ; ou lire la config d'`atlas-local`.

### C11 — Le « HCD synchrone, zéro lag » est en réalité « lag < 45 ms », sous le plancher HTTP.
attempts=1 signifie « trouvé à la première requête » — mais cette requête arrive ~45 ms après l'écriture (aller-retour HTTP). Un lag d'index HCD entre 0 et 45 ms serait **indétectable**, exactement la limite de M7. Donc « synchrone/zéro » **surinterprète** : l'honnête est « lag HCD < 45 ms (sous le plancher de mesure) contre ~1015 ms pour MongoDB » — un écart d'au moins 22×, direction robuste, mais **je ne prouve pas que HCD est exactement zéro**.

## Les objections de portée (rétrécissent, n'annulent pas)

### C12 — L'avantage auto-index (A, 22×) est une victoire contre un MongoDB PAR DÉFAUT, pas contre un MongoDB compétent.
Une équipe qui interroge régulièrement un champ **déclare un index dessus** — elle ne subit pas le scan de 377 ms. Contre un MongoDB **correctement indexé sur ce champ**, MongoDB gagne (0,7 ms contre 17 ms). L'avantage réel de HCD n'est donc pas la vitesse mais la **dispense de conception d'index** : on ne paie jamais l'oubli. C'est une commodité opérationnelle réelle (§4), pas une supériorité de moteur. Le 22× compare HCD à un MongoDB mal configuré.

### C13 — La victoire de fraîcheur est bornée au chemin de RECHERCHE, pas « la fraîcheur » en général.
Sur un **index secondaire ordinaire**, la fraîcheur est un **match nul** (axe C : les deux synchrones). Le lag async de MongoDB ne mord que `$search`/`$vectorSearch` — donc les charges qui écrivent puis **cherchent en plein texte/vecteur immédiatement** (RAG). Un « read-your-writes » ordinaire sur MongoDB passe par un index b-tree synchrone, sans lag. La victoire HCD est **réelle et scopée au RAG**, pas globale.

### C14 — Texte contre vecteur : les deux moitiés ne mesurent pas le même chemin.
J'ai mesuré HCD **vecteur** (JVector) contre MongoDB **texte** (`$search`). L'architecture sync-vs-async est la même, mais un puriste exige du like-for-like : HCD lexical (BM25) contre MongoDB `$search` texte, ou HCD vecteur contre MongoDB `$vectorSearch`. La fraîcheur du lexical HCD et du `$vectorSearch` mongot **n'a pas été mesurée** ; je généralise sur l'architecture, pas sur quatre mesures.

### C15 — Deux déploiements MongoDB différents dans une même campagne, et l'impôt de niveau non retranché.
La fraîcheur vient d'`atlas-local` (mongot, **un membre**) ; la lecture/recherche du replica set **3 membres** de la campagne 5-6. Ce ne sont pas le même MongoDB. Et comme pour C1, le désavantage HCD en lecture ponctuelle (B, ~20×) est en grande partie le **saut de niveau Data API** — un HCD-CQL-direct réduirait l'écart ; non mesuré ici.

## Ce qui résiste
- **La direction de M17** : HCD synchrone (< 45 ms) contre MongoDB `$search` asynchrone (≥ des centaines de ms, ici ~1015). Robuste à C10 (même à 200 ms le sens tient), à C11 (l'écart reste ≥ 4×), à C14 (l'architecture est la même). **HCD a bien un avantage de fraîcheur de recherche que MongoDB n'a pas** — c'est le fait, pas la magnitude.
- **La parité de fraîcheur sur index ordinaire** (axe C) : les deux synchrones, mesuré des deux côtés.
- **Le scan de 377 ms sur champ non déclaré** : fait mesuré, quelle qu'en soit l'interprétation opérationnelle.

## Verdict campagne 6
La victoire HCD sur la fraîcheur de recherche **tient en direction** et **s'effrite en magnitude** : le « 1 s » est un défaut mongot (C10), le « zéro » HCD est « < 45 ms » (C11), et l'avantage est **scopé au RAG** (C13), contre un MongoDB **par défaut** pour l'auto-index (C12). Symétrie avec la campagne 5 : là MongoDB gagnait la mutation, mais le 44× était un peu de pile (C1) ; ici HCD gagne la fraîcheur de recherche, mais le 22×/1 s est un peu de configuration et de plancher de mesure. **Aucun des deux camps ne sort du dossier avec un avantage aussi net que son premier chiffre le suggère** — et c'est le seul résultat que six campagnes autorisent à publier.

---

# Résolution mesurée — C10 (18 septembre 2026)

**C10 CONFIRMÉE, et elle corrige ma propre mesure M17.** En désynchronisant l'insertion du cycle de commit (délai aléatoire 0–1200 ms avant chaque écriture, puis poll à 5 ms), le lag de `$search` de mongot se révèle **large, pas serré** :

| | min | p10 | **moyenne** | médiane | p90 | max | écart-type |
|---|---|---|---|---|---|---|---|
| lag `$search` désynchronisé (ms) | **89** | 255 | **646** | 664 | 989 | 1170 | 291 |

**Verdict : intervalle de refresh (~1,1 s, style Lucene), pas un délai fixe.** Le ~1015 ms de M17 était la **pire phase** du cycle, amplifiée par l'auto-synchronisation de ma sonde (chaque cycle attendait le commit suivant, donc chaque insert tombait juste après un commit). Le vrai comportement : un document devient cherchable après un lag **uniforme ~90–1170 ms**, **moyenne ~646 ms**. Le plancher (meilleur cas) est ~90 ms — une petite composante d'ingestion fixe. L'intervalle n'est **pas réglable** dans `atlas-local` (aucun fichier de config ni flag exposé ; c'est un défaut interne du binaire mongot).

**Ce que ça change à M17 :**
- La magnitude tombe de **~1015 ms à une moyenne ~646 ms** — ma mesure initiale était sur-estimée ~1,6× par un défaut de méthode (auto-synchronisation). Mon challenge C10 avait raison.
- **La direction tient** : HCD reste synchrone (attempts=1, < 45 ms, aucun lag d'index) ; MongoDB `$search` a un lag de refresh dont le **plancher (~90 ms) dépasse déjà** le plancher HTTP de HCD, et dont la **moyenne (~646 ms)** vaut ~14× celle de HCD. Même au meilleur cas, MongoDB a une fenêtre là où HCD n'en a pas.
- Ce qui reste indéterminé : Atlas en production peut avoir un intervalle différent ; ce ~1,1 s est le défaut d'`atlas-local`. Mais il n'est pas réglable **par l'utilisateur** sur ce déploiement — donc pour qui déploie MongoDB Search local, ~646 ms de lag moyen est ce qu'il obtient.

**Net : l'avantage de fraîcheur de recherche de HCD est réel (direction robuste), sa magnitude est un lag de refresh moyen ~646 ms côté MongoDB, pas ~1 s — et c'est ma propre mesure que la désynchronisation corrige, pas celle d'un adversaire.**

---

# Challenge — la résolution C10 (M18) elle-même
18 septembre 2026. Contre ma propre mesure de fermeture.

### D1 — La plus forte : les ~646 ms sont probablement MOOT pour le RAG qui est censé s'en soucier. ⭑⭑
Le §4.1 invoque le RAG pour justifier l'importance de la fraîcheur : « écrire un fait, le chercher au tour suivant ». Mais **un tour de RAG dure des secondes** — la génération du LLM à elle seule prend 1 à 10 s. Or le lag de recherche de MongoDB est en **moyenne ~646 ms, au pire ~1170 ms**. Donc au moment où l'application relit (après que le LLM a répondu), **l'intervalle de refresh a expiré et le document EST cherchable**. La fenêtre ne mord que si l'écriture-puis-recherche se produit en **moins de ~1,1 s**, ce qui est inhabituel pour un RAG piloté par LLM. **L'avantage de fraîcheur synchrone de HCD est réel et mesuré, mais possiblement sans conséquence opérationnelle pour le cas d'usage même qui le motive.** Il ne compte que pour les charges write-then-search **sub-seconde et automatisées** (pipelines d'ingestion serrés, pas RAG conversationnel). Je n'ai jamais testé si le seuil de ~1,1 s est franchi ou non par une charge réelle — je l'ai supposé important.

### D2 — atlas-local n'est pas Atlas de production ; le nombre ne transfère pas.
Le diptyque cite « MongoDB 8.x » — c'est-à-dire Atlas en production, pas `atlas-local`. L'intervalle de refresh de ~1,1 s est le **défaut d'un conteneur de développement mono-nœud**. Atlas production (multi-nœud, mongot dédié, tuning) peut être **plus rapide ou plus lent** — je n'en sais rien. Le chiffre ~646 ms caractérise un déploiement que **personne ne met en production**.

### D3 — Le plancher ~90 ms est un composant FIXE que j'ai passé sous silence.
La distribution n'est pas un intervalle de refresh pur (0..T) : le minimum est **89 ms, pas ~0**. Le modèle honnête est **~90 ms d'ingestion fixe + une phase de refresh** par-dessus. Donc mongot n'est **jamais** instantané — même au meilleur cas il y a ~90 ms. Cela *renforce* la direction HCD (qui n'a ni l'un ni l'autre), mais mon verdict « intervalle de refresh, plancher ~0 » était imprécis : le plancher est ~90 ms.

### D4 — Toujours texte contre vecteur (C14 non résolu).
M18 mesure MongoDB **`$search` texte** ; HCD M17 était **vecteur JVector**. Le `$vectorSearch` de mongot (même pipeline async, même intervalle) et le lexical de HCD n'ont pas été mesurés. Je continue de comparer deux chemins différents et de généraliser sur l'architecture.

### D5 — n=60, une passe, verdict par une heuristique que j'ai écrite.
Aucune répétition ; la moyenne peut bouger de ±50 ms sur un rejeu. Et la classification « refresh interval vs délai fixe » est un seuil **de mon propre code** (`near_zero and spread>0.5*max`), pas un test statistique. La forme (min 89, max 1170, σ 291) le soutient, mais c'est mon jugement, pas une preuve formelle.

### Ce qui résiste
La **direction** : mongot a un lag de recherche (fixe ~90 ms + refresh), HCD n'en a pas (attempts=1). Robuste. Et le fait mesuré : sur `atlas-local`, la fraîcheur de `$search` est un intervalle moyen ~646 ms non réglable.

### Verdict
La mesure M18 est solide en direction et honnête sur la magnitude. **Mais je n'ai jamais attaqué la prémisse : cet axe compte-t-il ?** D1 est la vraie faille — pour le RAG conversationnel, un lag de ~646 ms est probablement **noyé dans la latence du LLM**, donc l'avantage de HCD, réel en laboratoire, pourrait être **sans effet en production**. Le seul cas où il mord est le write-then-search sub-seconde automatisé — que le dossier n'a pas mesuré et n'a pas identifié comme la vraie portée de la revendication. **La fraîcheur de recherche est l'axe favorable à HCD, et même lui, quand on le presse, se réduit à « un avantage réel pour une classe de charges plus étroite que celle que l'article invoque ».**

---

# Résolution mesurée — D1 (18 septembre 2026)

**D1 CONFIRMÉE et quantifiée précisément.** Taux d'échec d'une recherche émise τ ms après l'écriture (le « temps de tour »), 30 cycles par point :

| Délai écriture→recherche τ | **MongoDB `$search`** | **HCD** |
|---|---|---|
| 0 ms | **100 %** | 0 % |
| 100 ms | 93 % | 0 % |
| 250 ms | 83 % | 0 % |
| 500 ms | 50 % | 0 % |
| 750 ms | 33 % | 0 % |
| **1000 ms** | **0 %** | 0 % |
| 1500–3000 ms | 0 % | 0 % |

**HCD : 0 % d'échec à tous les délais, y compris 0 ms** — synchrone, renvoie toujours le document frais. **MongoDB : le point de bascule est ~1 seconde** (l'intervalle de refresh de mongot).

**Ce que D1 établit, exactement :**
- **Pour le RAG conversationnel, l'avantage de HCD est MOOT.** Un tour piloté par LLM dure 1–10 s ; à τ ≥ 1000 ms, MongoDB **ne manque jamais** le document. La latence de génération noyait bien le lag de fraîcheur, comme D1 le soupçonnait. L'argument « propriété de correction » du §4.1, appliqué au RAG conversationnel, est **surévalué** : au moment où le LLM a fini de répondre, le refresh a eu lieu.
- **Pour le write-then-search sub-seconde, l'avantage de HCD est RÉEL et DÉCISIF.** À τ = 0–500 ms, MongoDB manque **50–100 %** des documents ; HCD, **0 %**. Les charges qui écrivent puis relisent immédiatement — chaînes d'outils agentiques, boucles d'ingestion serrées, pipelines automatisés — obtiennent de HCD une correction que MongoDB `$search` ne donne pas.
- **La portée est bornée à ~1 s.** L'avantage de HCD n'est ni universel ni nul : il vaut exactement pour l'écriture-puis-recherche en dessous de la seconde, et le dossier peut désormais le dire au lieu de le supposer.

**Net final de tout le dossier sur cet axe** : HCD a un avantage de fraîcheur de recherche **mesuré, réel, et étroit** — décisif sous ~1 s, moot au-delà. Le §4.1 a raison sur le mécanisme et sur les pipelines serrés, et tort d'invoquer le RAG conversationnel, où la latence du LLM efface la différence. C'est la conclusion la plus précise que sept campagnes autorisent : **le seul axe clairement favorable à HCD l'est pour une classe de charges plus étroite que celle que l'article revendique — mais pour cette classe, il l'est totalement (0 % contre 100 %).**
