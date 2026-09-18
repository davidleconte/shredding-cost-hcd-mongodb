#!/usr/bin/env python3
"""Every relative Markdown link in every tracked .md file must resolve to a
TRACKED path — not merely to a path that happens to exist on this disk.

The distinction is the whole point. CI runs against a clean checkout, in which
only tracked files exist; a developer runs against a working tree that also
holds everything not yet added. Testing existence alone therefore lets an
untracked *target* hide a link that is already broken for every reader, and the
same commit then reports OK locally and FAIL on the runner. The check is
against `git ls-files` so that a local run predicts the runner instead of
contradicting it.

Scope and deliberate exclusions:
  * only files returned by `git ls-files '*.md'` are read, so a work-in-progress
    document that is not yet in the index cannot break the build — but a link
    from a tracked document to a work-in-progress target DOES break it, and is
    reported as UNTRACKED rather than BROKEN so the two are not confused;
  * membership is tested against the index, not against HEAD. A target that is
    staged but not yet committed passes here and would still fail a clean
    checkout of HEAD; `git add` is treated as the author's commitment to ship it;
  * a target that is a directory (`.github/workflows/`) is accepted when the
    index holds at least one file beneath it, since git tracks files, not
    directories; the repository root itself (`.`, `/`, `../` from a subdirectory)
    is always accepted;
  * fenced code blocks and inline code spans are stripped before scanning, so an
    illustrative link inside an example is not treated as a claim;
  * absolute URLs (http, https, mailto, ftp) are NOT fetched here — an external
    link that rots is the internet's fault, not a defect in this artefact;
  * a bare `#anchor` is skipped; a `file.md#anchor` is checked for the FILE only.
    Heading anchors are not validated, because Markdown renderers disagree about
    how they are generated.

Exit 1 if any relative link points at a path that is absent from the index.
"""
from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

REPO = pathlib.Path(__file__).resolve().parents[2]

FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`[^`\n]*`")
# [text](target) and ![alt](target), tolerating a "title" and <angle brackets>.
LINK = re.compile(r"!?\[(?:[^\]\\]|\\.)*\]\(\s*(<[^>]*>|[^()\s]+)(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)")
ABSOLUTE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def ls_files(*pathspec: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", *pathspec],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout
    return [name for name in out.split("\0") if name]


def tracked_markdown() -> list[pathlib.Path]:
    return [REPO / name for name in ls_files("*.md")]


def tracked_index() -> tuple[set[str], set[str]]:
    """The whole index as repo-relative POSIX paths, plus every ancestor directory.

    git tracks files, not directories, so a link to `.github/workflows/` can only
    be validated by asking whether the index holds anything beneath it — hence
    the second set.
    """
    files = set(ls_files())
    dirs: set[str] = set()
    for name in files:
        for parent in pathlib.PurePosixPath(name).parents:
            # "." — the repository root — is kept deliberately. It is the target
            # a link such as `../` from a subdirectory resolves to, and every
            # checkout has it; dropping it reports the root as an untracked 404.
            dirs.add(str(parent))
    return files, dirs


def strip_code(text: str) -> str:
    """Blank out fenced blocks; drop inline code spans. Line count is preserved."""
    lines = text.splitlines()
    kept, fence = [], None
    for line in lines:
        marker = FENCE.match(line)
        if fence is None and marker:
            fence = marker.group(1)[0] * 3
            kept.append("")
            continue
        if fence is not None:
            if marker and marker.group(1).startswith(fence):
                fence = None
            kept.append("")
            continue
        kept.append(INLINE_CODE.sub("", line))
    return "\n".join(kept)


def main() -> int:
    files = tracked_markdown()
    if not files:
        print("FAIL: git ls-files returned no Markdown files", file=sys.stderr)
        return 1

    tracked_files, tracked_dirs = tracked_index()

    checked = 0
    broken: list[str] = []
    untracked: list[str] = []

    for md in files:
        body = strip_code(md.read_text(encoding="utf-8"))
        for lineno, line in enumerate(body.splitlines(), 1):
            for match in LINK.finditer(line):
                target = match.group(1).strip()
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1].strip()
                if not target or target.startswith("#") or ABSOLUTE.match(target):
                    continue
                path_part = unquote(urlsplit(target).path)
                if not path_part:
                    continue
                base = REPO if path_part.startswith("/") else md.parent
                # normpath, not resolve(): the index spells paths literally, and a
                # link is judged as the index would hold it.
                joined = os.path.normpath(os.path.join(base, path_part.lstrip("/")))
                rel = os.path.relpath(joined, REPO).replace(os.sep, "/")
                checked += 1

                # "." is the repository root itself — always present.
                if rel == "." or rel in tracked_files or rel in tracked_dirs:
                    continue

                where = f"{md.relative_to(REPO)}:{lineno}: -> {target}"
                if rel != target.split("#")[0].rstrip("/"):
                    where += f"  [{rel}]"
                if rel == ".." or rel.startswith("../"):
                    broken.append(f"{where}  (points outside the repository)")
                elif (REPO / rel).exists():
                    untracked.append(
                        f"{where}  (present in the working tree, absent from the "
                        f"index — a 404 in any clean checkout)"
                    )
                else:
                    broken.append(f"{where}  (no such path)")

    for item in broken:
        print(f"BROKEN {item}")
    for item in untracked:
        print(f"UNTRACKED {item}")

    if broken or untracked:
        sys.stdout.flush()   # keep the listing above the summary when 2>&1
        print(
            f"\nFAIL: {len(broken) + len(untracked)} of {checked} relative Markdown "
            f"links do not resolve against the git index "
            f"({len(broken)} absent, {len(untracked)} untracked).",
            file=sys.stderr,
        )
        if untracked:
            print(
                "      `git add` an untracked target in the same commit as the "
                "document that links to it, or drop the link.",
                file=sys.stderr,
            )
        return 1

    print(
        f"OK: {checked} relative Markdown links resolve to tracked paths, "
        f"across {len(files)} tracked files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
