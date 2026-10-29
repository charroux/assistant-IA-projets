from __future__ import annotations

import subprocess
from pathlib import Path

from .models import CoherenceError


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise CoherenceError("Git est introuvable.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "erreur Git").strip()
        raise CoherenceError(detail) from exc
    return result.stdout.strip()


def is_repository(root: Path) -> bool:
    try:
        return _git(root, "rev-parse", "--is-inside-work-tree") == "true"
    except CoherenceError:
        return False


def dirty_paths(root: Path) -> list[str]:
    if not is_repository(root):
        return []
    output = _git(root, "status", "--porcelain")
    return [line[3:] for line in output.splitlines() if len(line) > 3]


def current_commit(root: Path) -> str:
    if not is_repository(root):
        return "sans-git"
    try:
        return _git(root, "rev-parse", "HEAD")
    except CoherenceError:
        return "sans-commit"


def commit_files(root: Path, files: list[Path], message: str) -> str:
    if not is_repository(root):
        raise CoherenceError("Le projet n'est pas un dépôt Git.")
    relative = [str(path.resolve().relative_to(root.resolve())) for path in files]
    if not relative:
        raise CoherenceError("Aucun fichier à committer.")
    _git(root, "add", "--", *relative)
    _git(root, "commit", "-m", message)
    return current_commit(root)

