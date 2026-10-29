from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any

from .config import privacy_config
from .models import CoherenceError


TEXT_SUFFIXES = {".md", ".qmd", ".yml", ".yaml", ".json", ".txt"}
BLOCKED_PARTS = {".git", ".venv", "__pycache__", ".quarto", "_site"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|password|secret)\s*[:=]\s*['\"]?[^\s'\"]{12,}"),
)


def ai_settings(root: Path, mode: str) -> dict[str, Any]:
    privacy = privacy_config(root)
    ai = privacy.get("ia", {})
    if not isinstance(ai, dict):
        raise CoherenceError("La section `ia` de confidentialite.yml est invalide.")
    field = "assistance_autorisee" if mode == "assistance" else "evaluation_autorisee"
    if ai.get(field) is not True:
        raise CoherenceError(
            f"L'IA de {mode} n'est pas autorisée dans confidentialite.yml."
        )
    if privacy.get("niveau") == "restreint" and ai.get("cadre_adapte") is not True:
        raise CoherenceError("Projet restreint sans cadre IA adapté déclaré.")
    if not ai.get("contenu_autorise"):
        raise CoherenceError("Aucune liste de contenu autorisé pour l'IA.")
    return ai


def _matches(relative: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def collect_context(root: Path, mode: str, *, max_characters: int = 180_000) -> str:
    settings = ai_settings(root, mode)
    patterns = [str(item) for item in settings.get("contenu_autorise", [])]
    chunks: list[str] = []
    total = 0
    root_resolved = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in BLOCKED_PARTS for part in path.parts):
            continue
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root_resolved).as_posix()
        except ValueError as exc:
            raise CoherenceError(f"Lien sortant du projet refusé : {path}") from exc
        if not _matches(relative, patterns):
            continue
        text = path.read_text(encoding="utf-8")
        secret = detect_secret(text)
        if secret:
            raise CoherenceError(
                f"Secret potentiel détecté dans {relative} ({secret}). Envoi interrompu."
            )
        chunk = f"\n===== {relative} =====\n{text}\n"
        if total + len(chunk) > max_characters:
            remaining = max_characters - total
            if remaining > 200:
                chunks.append(chunk[:remaining])
            chunks.append("\n[CONTEXTE TRONQUÉ PAR LA LIMITE LOCALE]\n")
            break
        chunks.append(chunk)
        total += len(chunk)
    if not chunks:
        raise CoherenceError("Aucun fichier autorisé n'a pu être chargé pour l'IA.")
    return "".join(chunks)


def detect_secret(text: str) -> str | None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return None


def safe_change_path(root: Path, relative: str, settings: dict[str, Any]) -> Path:
    normalized = relative.replace("\\", "/").lstrip("/")
    if not normalized or normalized.startswith(".") or ":" in normalized:
        raise CoherenceError(f"Chemin de modification refusé : {relative}")
    target = (root / normalized).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise CoherenceError(f"Chemin hors projet refusé : {relative}") from exc
    if target.suffix.lower() not in TEXT_SUFFIXES:
        raise CoherenceError(f"Type de fichier non autorisé : {relative}")
    patterns = [str(item) for item in settings.get("modifications_autorisees", [])]
    if not patterns or not _matches(normalized, patterns):
        raise CoherenceError(f"Modification non autorisée par la politique : {relative}")
    if ".git" in target.parts:
        raise CoherenceError("Modification de .git refusée.")
    return target

