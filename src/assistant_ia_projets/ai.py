from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from .models import CoherenceError
from .security import ai_settings, collect_context, detect_secret, safe_change_path


ASSISTANT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "resume": {"type": "string"},
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "gravite": {
                        "type": "string",
                        "enum": ["information", "mineure", "majeure", "bloquante"],
                    },
                    "titre": {"type": "string"},
                    "constat": {"type": "string"},
                    "preuves": {"type": "array", "items": {"type": "string"}},
                    "avis_expert_requis": {"type": "boolean"},
                },
                "required": [
                    "gravite",
                    "titre",
                    "constat",
                    "preuves",
                    "avis_expert_requis",
                ],
            },
        },
        "questions": {"type": "array", "items": {"type": "string"}},
        "changements": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "chemin": {"type": "string"},
                    "action": {"type": "string", "enum": ["aucune", "creer", "modifier"]},
                    "contenu": {"type": "string"},
                    "justification": {"type": "string"},
                    "artefacts_affectes": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "chemin",
                    "action",
                    "contenu",
                    "justification",
                    "artefacts_affectes",
                ],
            },
        },
        "decisions_humaines_requises": {
            "type": "array",
            "items": {"type": "string"},
        },
        "synthese_monday": {"type": "string"},
    },
    "required": [
        "resume",
        "observations",
        "questions",
        "changements",
        "decisions_humaines_requises",
        "synthese_monday",
    ],
}


AUDIT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "perimetre": {"type": "string"},
        "commit": {"type": "string"},
        "criteres": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "libelle": {"type": "string"},
                    "statut": {
                        "type": "string",
                        "enum": ["observable", "partiel", "non_evaluable"],
                    },
                    "score": {"anyOf": [{"type": "number"}, {"type": "null"}]},
                    "maximum": {"type": "number"},
                    "confiance": {
                        "type": "string",
                        "enum": ["faible", "moyenne", "forte"],
                    },
                    "preuves": {"type": "array", "items": {"type": "string"}},
                    "constat": {"type": "string"},
                    "avis_expert_requis": {"type": "boolean"},
                },
                "required": [
                    "id",
                    "libelle",
                    "statut",
                    "score",
                    "maximum",
                    "confiance",
                    "preuves",
                    "constat",
                    "avis_expert_requis",
                ],
            },
        },
        "score_indicatif": {"anyOf": [{"type": "number"}, {"type": "null"}]},
        "problemes_bloquants": {"type": "array", "items": {"type": "string"}},
        "limites": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "perimetre",
        "commit",
        "criteres",
        "score_indicatif",
        "problemes_bloquants",
        "limites",
    ],
}


@dataclass
class AppliedChanges:
    paths: list[Path]
    originals: dict[Path, str | None]


def _prompt(name: str) -> str:
    return (
        resources.files("assistant_ia_projets")
        .joinpath("prompts", name)
        .read_text(encoding="utf-8")
    )


def _model(root: Path, mode: str, override: str | None) -> str:
    settings = ai_settings(root, mode)
    return override or os.getenv("OPENAI_MODEL") or str(settings.get("modele") or "gpt-6-astra")


def _request(
    *,
    model: str,
    instructions: str,
    user_input: str,
    schema: dict[str, Any],
    schema_name: str,
) -> dict[str, Any]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise CoherenceError("Installer la dépendance `openai` pour utiliser l'IA.") from exc
    try:
        client = OpenAI()
        response = client.responses.create(
            model=model,
            instructions=instructions,
            input=user_input,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                }
            },
            store=False,
        )
        payload = json.loads(response.output_text)
    except Exception as exc:  # SDK errors vary across versions.
        raise CoherenceError(f"Appel IA impossible : {exc}") from exc
    if not isinstance(payload, dict):
        raise CoherenceError("Réponse IA structurée invalide.")
    return payload


def assist(root: Path, question: str, *, model: str | None = None) -> dict[str, Any]:
    context = collect_context(root, "assistance")
    user_input = (
        "DEMANDE DE L'ÉQUIPE\n"
        f"{question}\n\n"
        "CONTENU AUTORISÉ DU DÉPÔT\n"
        f"{context}"
    )
    return _request(
        model=_model(root, "assistance", model),
        instructions=_prompt("assistant.md"),
        user_input=user_input,
        schema=ASSISTANT_SCHEMA,
        schema_name="assistant_coherence",
    )


def audit(
    root: Path,
    *,
    commit: str,
    model: str | None = None,
) -> dict[str, Any]:
    context = collect_context(root, "evaluation")
    user_input = (
        f"COMMIT À AUDITER\n{commit}\n\n"
        "CONTENU AUTORISÉ DU DÉPÔT\n"
        f"{context}"
    )
    return _request(
        model=_model(root, "evaluation", model),
        instructions=_prompt("evaluator.md"),
        user_input=user_input,
        schema=AUDIT_SCHEMA,
        schema_name="audit_documentaire",
    )


def apply_proposal(root: Path, proposal: dict[str, Any]) -> AppliedChanges:
    settings = ai_settings(root, "assistance")
    originals: dict[Path, str | None] = {}
    paths: list[Path] = []
    seen: set[Path] = set()
    for change in proposal.get("changements", []):
        if change.get("action") == "aucune":
            continue
        target = safe_change_path(root, str(change.get("chemin", "")), settings)
        if target in seen:
            raise CoherenceError(f"Le modèle propose plusieurs changements pour {target}.")
        seen.add(target)
        action = change.get("action")
        if action == "creer" and target.exists():
            raise CoherenceError(f"Création impossible, le fichier existe : {target}")
        if action == "modifier" and not target.exists():
            raise CoherenceError(f"Modification impossible, fichier absent : {target}")
        content = str(change.get("contenu", ""))
        secret = detect_secret(content)
        if secret:
            raise CoherenceError(f"Secret potentiel dans la proposition pour {target}.")
        original = target.read_text(encoding="utf-8") if target.exists() else None
        if _validation_count(content) > _validation_count(original or ""):
            raise CoherenceError(
                f"L'IA ne peut pas promouvoir un statut vers `valide` : {target}"
            )
        originals[target] = original
        paths.append(target)

    try:
        for change in proposal.get("changements", []):
            if change.get("action") == "aucune":
                continue
            target = safe_change_path(root, str(change.get("chemin", "")), settings)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(change.get("contenu", "")), encoding="utf-8")
    except Exception:
        rollback(AppliedChanges(paths=paths, originals=originals))
        raise
    return AppliedChanges(paths=paths, originals=originals)


def rollback(changes: AppliedChanges) -> None:
    for path, original in changes.originals.items():
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(original, encoding="utf-8")


def _validation_count(text: str) -> int:
    return len(re.findall(r"(?mi)^\s*statut\s*:\s*valide\s*$", text))

