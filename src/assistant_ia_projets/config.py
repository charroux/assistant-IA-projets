from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import CoherenceError


def load_yaml(path: Path, *, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise CoherenceError(f"Fichier requis absent : {path}")
        return {}
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise CoherenceError(f"Impossible de lire {path} : {exc}") from exc
    if content is None:
        return {}
    if not isinstance(content, dict):
        raise CoherenceError(f"La racine YAML de {path} doit être un objet.")
    return content


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def project_config(root: Path) -> dict[str, Any]:
    return load_yaml(root / "projet.yml")


def privacy_config(root: Path) -> dict[str, Any]:
    return load_yaml(root / "confidentialite.yml")

