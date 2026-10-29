from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CheckReport


LABELS = {"error": "ERREUR", "warning": "ATTENTION", "info": "INFO"}


def check_text(report: CheckReport) -> str:
    lines = [
        f"Projet : {report.root}",
        f"Résultat : {'OK' if report.ok else 'ÉCHEC'}",
        f"Erreurs : {len(report.errors)} — Avertissements : {len(report.warnings)}",
    ]
    for finding in report.findings:
        location = ""
        if finding.path:
            location += f" [{finding.path}]"
        if finding.artifact_id:
            location += f" ({finding.artifact_id})"
        lines.append(
            f"- {LABELS.get(finding.severity, finding.severity.upper())} "
            f"{finding.code}{location} : {finding.message}"
        )
    return "\n".join(lines)


def check_markdown(report: CheckReport) -> str:
    lines = [
        "# Rapport de cohérence",
        "",
        f"- Résultat : **{'conforme aux contrôles' if report.ok else 'erreurs détectées'}**",
        f"- Erreurs : {len(report.errors)}",
        f"- Avertissements : {len(report.warnings)}",
        "",
        "## Constats",
        "",
    ]
    if not report.findings:
        lines.append("Aucun constat.")
    for finding in report.findings:
        location = finding.path or "dépôt"
        identifier = f" — `{finding.artifact_id}`" if finding.artifact_id else ""
        lines.extend(
            [
                f"### {LABELS.get(finding.severity, finding.severity)} — {finding.code}",
                "",
                f"**Emplacement :** `{location}`{identifier}",
                "",
                finding.message,
                "",
            ]
        )
    lines.extend(
        [
            "## Limite",
            "",
            "Ce rapport contrôle la structure et la cohérence documentaire. Il ne "
            "certifie ni la validité métier, ni la qualité scientifique ou technique.",
            "",
        ]
    )
    return "\n".join(lines)


def audit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Audit documentaire indépendant",
        "",
        f"**Périmètre :** {audit.get('perimetre', '')}",
        "",
        f"**Commit :** `{audit.get('commit', '')}`",
        "",
        "## Critères",
        "",
    ]
    for criterion in audit.get("criteres", []):
        score = criterion.get("score")
        maximum = criterion.get("maximum")
        score_text = "non évalué" if score is None else f"{score}/{maximum}"
        lines.extend(
            [
                f"### {criterion.get('id')} — {criterion.get('libelle')}",
                "",
                f"- Statut : {criterion.get('statut')}",
                f"- Score indicatif : {score_text}",
                f"- Confiance : {criterion.get('confiance')}",
                f"- Avis expert requis : {criterion.get('avis_expert_requis')}",
                "- Preuves : " + ", ".join(criterion.get("preuves", [])),
                "",
                criterion.get("constat", ""),
                "",
            ]
        )
    lines.extend(["## Problèmes bloquants", ""])
    lines.extend(f"- {item}" for item in audit.get("problemes_bloquants", []))
    lines.extend(["", "## Limites", ""])
    lines.extend(f"- {item}" for item in audit.get("limites", []))
    lines.extend(
        [
            "",
            "Cet audit est consultatif et ne remplace ni le mentor, ni l'expert, ni le jury.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
