#!/usr/bin/env python3
"""
sync_artefacts.py — copies artefacts from a download folder into this repository,
verifies the result, and commits only if every check passes.

WHY A SCRIPT RATHER THAN cp
---------------------------
Three of these files change name on the way in — `synthese-8-axes.html` is
published as `docs/synthesis/huit-axes.fr.html`, and the arXiv sources land under
`docs/arxiv/`. Copying by hand has already put a file in the wrong place once in
this project's history. The mapping below is the authority; edit it here rather
than remembering it.

And the ordering matters: the repository's integrity checks must run AFTER the
copy and BEFORE the commit. A commit that fails CI is worse than no commit,
because the failure surfaces minutes later on a machine you are not watching.

SAFETY
------
Dry run by default. Nothing is written without --apply, and nothing is pushed
without --push. Before touching anything it refuses to proceed if:

  * the working tree is dirty      — your uncommitted work would be mixed in
  * HEAD differs from origin/main  — you would build on a stale base, and this
                                     repository's history has been rewritten once

USAGE
-----
  python3 .github/scripts/sync_artefacts.py                  # show what would change
  python3 .github/scripts/sync_artefacts.py --apply          # copy, check, commit
  python3 .github/scripts/sync_artefacts.py --apply --push   # and push
  python3 .github/scripts/sync_artefacts.py --from ~/Desktop # another source folder
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# The mapping. Source name in the download folder -> destination in the repo.
# A source that is absent is skipped with a note, not an error: you will rarely
# have all of them at once.
# --------------------------------------------------------------------------- #
MAPPING: dict[str, str] = {
    # the diptych
    "article-part1-what-a-mutation-costs.html":     "docs/article/article-part1-what-a-mutation-costs.html",
    "article-part2-when-the-index-is-current.html": "docs/article/article-part2-when-the-index-is-current.html",

    # the one-screen synthesis — NOTE THE RENAME
    "synthese-8-axes.html":                         "docs/synthesis/huit-axes.fr.html",
    "huit-axes.fr.html":                            "docs/synthesis/huit-axes.fr.html",

    # the front page
    "README.md":                                    "README.md",

    # the arXiv note, sources and built PDF
    "main.tex":                                     "docs/arxiv/main.tex",
    "refs.bib":                                     "docs/arxiv/refs.bib",
    "main.bbl":                                     "docs/arxiv/main.bbl",
    "main.pdf":                                     "docs/arxiv/main.pdf",
    "SUBMISSION.md":                                "docs/arxiv/SUBMISSION.md",

    # print-ready renderings of the diptych
    "Part-I-what-a-mutation-costs.pdf":             "docs/article/Part-I-what-a-mutation-costs.pdf",
    "Part-II-when-the-index-is-current.pdf":        "docs/article/Part-II-when-the-index-is-current.pdf",

    # probes
    "disk_regime_rerun.py":                         "probes/disk_regime_rerun.py",
    "mongo_regime_rerun.py":                        "probes/mongo_regime_rerun.py",
}

# Checks run after the copy, before the commit. The article checker takes
# arguments, so it is listed separately.
CHECKS = ["check_evidence_manifest", "check_links", "check_raw_json",
          "check_probe_syntax", "check_probe_citations", "check_artifact_table",
          "check_inference", "check_figure_traceability"]
ARTICLE_CHECK_ARGS = ["docs/article/article-part1-what-a-mutation-costs.html",
                      "docs/article/article-part2-when-the-index-is-current.html"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def refuse(msg: str) -> None:
    print(f"\n  REFUS — {msg}\n", file=sys.stderr)
    sys.exit(1)


def preflight(repo: Path) -> None:
    """Two conditions, both of which have gone wrong in this project before."""
    dirty = run(["git", "-C", str(repo), "status", "--porcelain"]).stdout.strip()
    if dirty:
        print(dirty, file=sys.stderr)
        refuse("l'arbre de travail n'est pas propre. Committez ou remisez d'abord : "
               "sinon votre travail non committé partirait dans le même commit.")

    run(["git", "-C", str(repo), "fetch", "-q", "origin"])
    here = run(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()
    there = run(["git", "-C", str(repo), "rev-parse", "origin/main"]).stdout.strip()
    if here != there:
        behind = run(["git", "-C", str(repo), "rev-list", "--count", "HEAD..origin/main"]).stdout.strip()
        ahead = run(["git", "-C", str(repo), "rev-list", "--count", "origin/main..HEAD"]).stdout.strip()
        refuse(f"HEAD et origin/main divergent ({ahead} en avance, {behind} en retard). "
               f"L'historique de ce dépôt a déjà été réécrit une fois : ne construisez pas "
               f"sur une base périmée. Faites `git pull --ff-only` ou poussez d'abord.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", default="~/Downloads",
                    help="dossier source (défaut : ~/Downloads)")
    ap.add_argument("--apply", action="store_true", help="copier, vérifier et committer")
    ap.add_argument("--push", action="store_true", help="pousser après un commit réussi")
    ap.add_argument("-m", "--message", default=None, help="message de commit")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    src = Path(args.src).expanduser()
    if not src.is_dir():
        refuse(f"dossier source introuvable : {src}")

    print(f"  dépôt  : {repo}")
    print(f"  source : {src}")
    print(f"  mode   : {'APPLIQUER' if args.apply else 'essai (rien ne sera écrit)'}\n")

    if args.apply:
        preflight(repo)

    planned: list[tuple[Path, Path, str]] = []
    seen_dest: dict[str, str] = {}
    for name, dest_rel in MAPPING.items():
        s = src / name
        if not s.exists():
            continue
        d = repo / dest_rel
        if dest_rel in seen_dest:
            refuse(f"deux sources visent {dest_rel} : {seen_dest[dest_rel]} et {name}. "
                   f"Retirez-en une du dossier source.")
        seen_dest[dest_rel] = name
        if not d.exists():
            state = "NOUVEAU"
        elif sha(s) == sha(d):
            state = "identique"
        else:
            state = "MODIFIÉ"
        planned.append((s, d, state))

    if not planned:
        print("  Aucun fichier du mapping n'est présent dans le dossier source.")
        print("  Rien à faire.\n")
        return 0

    width = max(len(p[0].name) for p in planned)
    for s, d, state in sorted(planned, key=lambda x: x[2]):
        mark = {"NOUVEAU": "+", "MODIFIÉ": "~", "identique": " "}[state]
        print(f"  {mark} {s.name:<{width}}  ->  {d.relative_to(repo)}   [{state}]")

    changed = [p for p in planned if p[2] != "identique"]
    print(f"\n  {len(changed)} fichier(s) à écrire, {len(planned) - len(changed)} déjà à jour.")

    if not args.apply:
        print("\n  Essai terminé. Relancez avec --apply pour écrire.\n")
        return 0
    if not changed:
        print("  Rien à committer.\n")
        return 0

    for s, d, _ in changed:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, d)
    print(f"\n  {len(changed)} fichier(s) copié(s).")

    # ---- vérifier AVANT de committer ---------------------------------------
    print("\n  Vérifications :")
    failed: list[str] = []
    for c in CHECKS:
        script = repo / ".github" / "scripts" / f"{c}.py"
        if not script.exists():
            continue
        r = run([sys.executable, str(script)], cwd=repo)
        ok = r.returncode == 0
        print(f"    {c:<28}{'OK' if ok else 'ÉCHEC'}")
        if not ok:
            failed.append(c)
    art = repo / ".github" / "scripts" / "check_article_refs.py"
    if art.exists():
        r = run([sys.executable, str(art), *ARTICLE_CHECK_ARGS], cwd=repo)
        ok = r.returncode == 0
        print(f"    {'check_article_refs':<28}{'OK' if ok else 'ÉCHEC'}")
        if not ok:
            failed.append("check_article_refs")
            print("      " + (r.stdout or r.stderr).strip()[:400])

    if failed:
        print(f"\n  {len(failed)} vérification(s) en échec : {', '.join(failed)}")
        print("  Les fichiers sont copiés mais RIEN n'a été committé.")
        print("  Corrigez le texte — pas le script — puis relancez.")
        if "check_artifact_table" in failed:
            print("\n  check_artifact_table se répare seul si l'arbre a bougé légitimement :")
            print("    python3 .github/scripts/check_artifact_table.py --write")
        return 1

    # ---- committer ----------------------------------------------------------
    msg = args.message or (
        "Synchronise les artefacts publies\n\n"
        + "\n".join(f"  {d.relative_to(repo)}  [{state.lower()}]" for _, d, state in changed)
        + "\n\nCopie par .github/scripts/sync_artefacts.py, qui refuse de committer\n"
          "tant que les neuf controles d'integrite ne passent pas."
    )
    run(["git", "-C", str(repo), "add", *[str(d.relative_to(repo)) for _, d, _ in changed]])
    # check_artifact_table may have rewritten ARTIFACT.md as a side effect
    if run(["git", "-C", str(repo), "status", "--porcelain", "ARTIFACT.md"]).stdout.strip():
        run(["git", "-C", str(repo), "add", "ARTIFACT.md"])
    r = run(["git", "-C", str(repo), "commit", "-m", msg])
    if r.returncode != 0:
        refuse(f"le commit a échoué :\n{r.stdout}{r.stderr}")
    print(f"\n  Commit : {run(['git', '-C', str(repo), 'log', '--format=%h %s', '-1']).stdout.strip()}")

    if not args.push:
        print("\n  Non poussé. Relancez avec --push, ou poussez à la main.\n")
        return 0

    r = run(["git", "-C", str(repo), "push", "origin", "HEAD:main"])
    if r.returncode != 0:
        refuse(f"la poussée a échoué :\n{r.stdout}{r.stderr}")
    print("  Poussé sur origin/main.")
    print("\n  Vérifiez que la CI passe au vert SUR LE COMMIT DISTANT, pas en local :")
    print("  trois défauts de ce dépôt sont passés en local avant d'échouer en CI.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
