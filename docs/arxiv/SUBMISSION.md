# Dépôt arXiv — ce qu'il reste à faire

Catégorie principale suggérée : **cs.DB**. Secondaire : **cs.PF**.

## Avant compilation chez arXiv

`main.tex` porte deux aménagements locaux, à défaire avant soumission — la chaîne TeX de ce
conteneur n'avait pas `lmodern` :

1. décommenter `\usepackage{lmodern}` ;
2. retirer l'option : `\usepackage[expansion=false]{microtype}` → `\usepackage{microtype}`.

arXiv compile avec TeX Live complet ; les deux fonctionneront.

## Ce qu'arXiv exige et que le fichier fournit déjà

- source LaTeX, pas de PDF seul — joindre `main.tex` **et** `refs.bib` ;
- aucune figure externe : la note n'en a aucune ;
- la bibliographie est compilée par BibTeX ; arXiv accepte soit `refs.bib`, soit le `main.bbl` généré. Joindre les deux est le plus sûr ;
- abstract en texte brut pour le formulaire — copier le contenu de `\begin{abstract}`, en
  remplaçant les commandes mathématiques par leur forme texte ;
- déclaration de conflit d'intérêts : présente en tête, comme le demandent les usages du domaine ;
- déclaration d'usage de modèles de langage : section *Acknowledgements*, conforme à la politique
  arXiv en vigueur.

## Trois points à régler hors du fichier

0. **Épingler l'artefact — impératif, et à faire avant le dépôt.** La note dit que toute
   affirmation renvoie à l'état du dépôt publié sous le tag `v1.0-arxiv`. Ce tag n'existe pas
   encore. L'historique du dépôt a été réécrit pendant son développement : un lien vers la branche
   par défaut n'est pas une référence stable, et une note arXiv est permanente.

   ```bash
   git tag -a v1.0-arxiv -m "Etat cite par la note arXiv du 19 septembre 2026"
   git push origin v1.0-arxiv
   ```

   Puis archiver ce tag sur Zenodo (connexion GitHub → Zenodo, la release déclenche le dépôt) et
   **remplacer dans `main.tex` la mention « archived with a DOI » par le DOI obtenu**. Tant que le
   DOI n'est pas là, cette phrase promet ce qui n'existe pas.


1. **Parrainage.** Une première soumission dans `cs.DB` peut demander un endorsement. Une adresse
   institutionnelle le confère souvent automatiquement ; sinon, il faut solliciter un auteur déjà
   publié dans la catégorie.

2. **Accord interne.** La note est signée d'un salarié IBM et porte sur deux produits qu'IBM
   revend. Un accord préalable est prudent, et la déclaration de conflit d'intérêts en tête ne le
   remplace pas.

## Licence

Le dépôt est en CC-BY-4.0. arXiv propose la même — la choisir garde les deux cohérents.
