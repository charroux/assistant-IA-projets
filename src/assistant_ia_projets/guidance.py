from __future__ import annotations

from pathlib import Path
from typing import Any

from .checks import run_checks
from .config import privacy_config, project_config
from .repository import load_artifacts


PHASE_STEPS: dict[str, list[str]] = {
    "cadrage": [
        "Vérifier avec l'équipe les règles de confidentialité et les outils autorisés.",
        "Reformuler le problème concret, les bénéficiaires, le périmètre et les non-objectifs.",
        "Documenter les exigences principales, risques et critères d'acceptation.",
        "Faire examiner le cadrage par les interlocuteurs humains compétents avant la réalisation.",
    ],
    "realisation": [
        "Relier chaque composant et décision aux exigences concernées.",
        "Référencer les essais, résultats et retours dans l'index des preuves.",
        "Analyser l'impact de chaque changement de périmètre ou d'exigence.",
        "Conserver les limites observées et les écarts non résolus.",
    ],
    "finalisation": [
        "Vérifier la couverture des exigences par les preuves autorisées.",
        "Aligner le rapport et la soutenance sur les décisions et résultats documentés.",
        "Rendre visibles les limites et les éléments qui nécessitent un avis expert.",
        "Figer un commit propre avant l'audit documentaire.",
    ],
    "termine": [
        "Conserver le commit remis, le rapport final et les décisions importantes.",
        "Vérifier que les données confidentielles restent dans les espaces autorisés.",
        "Consigner les actions de clôture dans l'outil institutionnel.",
    ],
}


def start_summary(root: Path) -> dict[str, Any]:
    project = project_config(root)
    privacy = privacy_config(root)
    artifacts = load_artifacts(root)
    report = run_checks(root)
    phase = str(project.get("phase", "cadrage"))
    statuses: dict[str, int] = {}
    for artifact in artifacts:
        statuses[artifact.status] = statuses.get(artifact.status, 0) + 1
    ai = privacy.get("ia", {}) if isinstance(privacy.get("ia"), dict) else {}
    return {
        "titre": project.get("titre", "Projet sans titre"),
        "campus": project.get("campus", "non renseigné"),
        "phase": phase,
        "artefacts": len(artifacts),
        "statuts": statuses,
        "erreurs": len(report.errors),
        "avertissements": len(report.warnings),
        "assistance_ia_autorisee": ai.get("assistance_autorisee") is True,
        "evaluation_ia_autorisee": ai.get("evaluation_autorisee") is True,
        "prochaines_etapes": PHASE_STEPS.get(phase, PHASE_STEPS["cadrage"]),
    }


def start_text(root: Path) -> str:
    summary = start_summary(root)
    lines = [
        f"Projet : {summary['titre']}",
        f"Campus : {summary['campus']} — Phase : {summary['phase']}",
        f"Artefacts : {summary['artefacts']} — Erreurs : {summary['erreurs']} — "
        f"Avertissements : {summary['avertissements']}",
        "",
        "Par où commencer :",
    ]
    lines.extend(
        f"{index}. {step}"
        for index, step in enumerate(summary["prochaines_etapes"], start=1)
    )
    lines.extend(
        [
            "",
            "Commandes utiles sans IA :",
            "- coherence check",
            "- coherence impact EXG-001",
            "- coherence report",
            "",
            "Assistance IA : "
            + ("autorisée" if summary["assistance_ia_autorisee"] else "désactivée"),
            "Évaluation IA : "
            + ("autorisée" if summary["evaluation_ia_autorisee"] else "désactivée"),
        ]
    )
    if not summary["assistance_ia_autorisee"]:
        lines.append(
            "Aucun appel IA ne sera possible tant que confidentialite.yml ne l'autorise pas."
        )
    return "\n".join(lines)
