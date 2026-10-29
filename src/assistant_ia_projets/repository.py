from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

from .config import load_yaml
from .models import Artifact, CoherenceError


ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]{1,11}-\d{3}$")

COLLECTIONS: tuple[tuple[str, str, str], ...] = (
    ("cadrage/exigences.yml", "exigences", "exigence"),
    ("cadrage/risques.yml", "risques", "risque"),
    ("cadrage/criteres_acceptation.yml", "criteres", "critere"),
    ("conception/composants.yml", "composants", "composant"),
    ("preuves/index.yml", "preuves", "preuve"),
    ("ecarts/index.yml", "ecarts", "ecart"),
)

MARKDOWN_GLOBS: tuple[str, ...] = (
    "cadrage/*.md",
    "conception/*.md",
    "decisions/*.md",
    "productions/*.qmd",
)


def parse_front_matter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise CoherenceError(f"Impossible de lire {path} : {exc}") from exc
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        raise CoherenceError(f"Front matter non fermé dans {path}")
    try:
        value = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError as exc:
        raise CoherenceError(f"Front matter YAML invalide dans {path} : {exc}") from exc
    if not isinstance(value, dict):
        raise CoherenceError(f"Front matter invalide dans {path}")
    return value


def load_artifacts(root: Path) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for relative, key, kind in COLLECTIONS:
        path = root / relative
        if not path.exists():
            continue
        document = load_yaml(path)
        items = document.get(key, [])
        if not isinstance(items, list):
            raise CoherenceError(f"{relative}: `{key}` doit être une liste.")
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise CoherenceError(f"{relative}: entrée {index + 1} invalide.")
            identifier = str(item.get("id", "")).strip()
            artifacts.append(
                Artifact(
                    identifier=identifier,
                    kind=kind,
                    status=str(item.get("statut", "brouillon")),
                    path=path,
                    data=item,
                )
            )

    seen_paths: set[Path] = set()
    for pattern in MARKDOWN_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path in seen_paths or not path.is_file():
                continue
            seen_paths.add(path)
            metadata = parse_front_matter(path)
            identifier = str(metadata.get("id", "")).strip()
            if not identifier:
                continue
            artifacts.append(
                Artifact(
                    identifier=identifier,
                    kind=str(metadata.get("type", "document")),
                    status=str(metadata.get("statut", "brouillon")),
                    path=path,
                    data=metadata,
                )
            )
    return artifacts


def iter_id_references(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "id":
                continue
            yield from iter_id_references(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_id_references(nested)
    elif isinstance(value, str) and ID_PATTERN.fullmatch(value.strip()):
        yield value.strip()


def artifact_map(artifacts: list[Artifact]) -> dict[str, Artifact]:
    return {artifact.identifier: artifact for artifact in artifacts if artifact.identifier}


def relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()

