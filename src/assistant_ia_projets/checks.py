from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .config import load_yaml, privacy_config, project_config
from .models import CheckReport, CoherenceError
from .repository import ID_PATTERN, artifact_map, iter_id_references, load_artifacts, relative_path


REQUIRED_FILES = (
    ".gitignore",
    "projet.yml",
    "confidentialite.yml",
    "usage_ia.yml",
    "PROMPT_DEMARRAGE.md",
    "cadrage/besoin.md",
    "cadrage/exigences.yml",
    "cadrage/risques.yml",
    "cadrage/criteres_acceptation.yml",
    "conception/composants.yml",
    "preuves/index.yml",
    "ecarts/index.yml",
    "evaluation/grille.yml",
)

ALLOWED_STATUSES = {
    "brouillon",
    "propose",
    "valide",
    "remplace",
    "suspendu",
    "ouvert",
    "resolu",
    "accepte",
}

LATE_PHASES = {"realisation", "finalisation", "termine"}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def run_checks(root: Path) -> CheckReport:
    root = root.resolve()
    report = CheckReport(root=root)
    for relative in REQUIRED_FILES:
        if not (root / relative).exists():
            report.add("FILE_MISSING", "error", "Fichier requis absent.", relative)

    try:
        project = project_config(root)
    except CoherenceError as exc:
        report.add("PROJECT_INVALID", "error", str(exc), "projet.yml")
        project = {}

    campus = project.get("campus")
    if campus not in {"paris", "bordeaux"}:
        report.add(
            "CAMPUS_INVALID",
            "error",
            "Le campus doit être `paris` ou `bordeaux`.",
            "projet.yml",
        )
    elif not (root / "calendriers" / f"{campus}.yml").exists():
        report.add(
            "CALENDAR_MISSING",
            "error",
            f"Calendrier du campus {campus} absent.",
            f"calendriers/{campus}.yml",
        )

    try:
        privacy = privacy_config(root)
        _check_privacy(report, privacy)
    except CoherenceError as exc:
        report.add("PRIVACY_INVALID", "error", str(exc), "confidentialite.yml")

    try:
        artifacts = load_artifacts(root)
    except CoherenceError as exc:
        report.add("ARTIFACT_READ", "error", str(exc))
        return report

    identifiers = [item.identifier for item in artifacts]
    counts = Counter(identifiers)
    for identifier, count in counts.items():
        if not identifier:
            report.add("ID_MISSING", "error", "Un artefact ne possède pas d'identifiant.")
        elif not ID_PATTERN.fullmatch(identifier):
            report.add(
                "ID_INVALID",
                "error",
                f"Identifiant invalide : {identifier}",
                artifact_id=identifier,
            )
        elif count > 1:
            report.add(
                "ID_DUPLICATE",
                "error",
                f"Identifiant utilisé {count} fois.",
                artifact_id=identifier,
            )

    by_id = artifact_map(artifacts)
    for artifact in artifacts:
        rel = relative_path(root, artifact.path)
        if artifact.status not in ALLOWED_STATUSES:
            report.add(
                "STATUS_INVALID",
                "error",
                f"Statut inconnu : {artifact.status}",
                rel,
                artifact.identifier,
            )
        for reference in set(iter_id_references(artifact.data)):
            if reference not in by_id:
                report.add(
                    "REFERENCE_MISSING",
                    "error",
                    f"Référence introuvable : {reference}",
                    rel,
                    artifact.identifier,
                )
            elif artifact.status == "valide" and by_id[reference].status == "brouillon":
                report.add(
                    "VALIDATED_DEPENDS_ON_DRAFT",
                    "warning",
                    f"L'artefact validé dépend du brouillon {reference}.",
                    rel,
                    artifact.identifier,
                )

    phase = str(project.get("phase", "cadrage"))
    for artifact in artifacts:
        if artifact.kind == "exigence":
            _check_requirement(report, root, artifact, phase)
        elif artifact.kind == "preuve":
            _check_evidence(report, root, artifact)
        elif artifact.kind == "production":
            if not _as_list(artifact.data.get("sources")):
                report.add(
                    "PRODUCTION_WITHOUT_SOURCE",
                    "warning",
                    "La production ne déclare aucune source de projet.",
                    relative_path(root, artifact.path),
                    artifact.identifier,
                )

    try:
        usage = load_yaml(root / "usage_ia.yml", required=False)
        uses = usage.get("usages", [])
        if not isinstance(uses, list):
            report.add(
                "AI_USAGE_INVALID",
                "error",
                "`usages` doit être une liste.",
                "usage_ia.yml",
            )
    except CoherenceError as exc:
        report.add("AI_USAGE_INVALID", "error", str(exc), "usage_ia.yml")

    return report


def _check_privacy(report: CheckReport, privacy: dict[str, Any]) -> None:
    level = privacy.get("niveau")
    if level not in {"public", "interne", "restreint"}:
        report.add(
            "PRIVACY_LEVEL_INVALID",
            "error",
            "Le niveau doit être public, interne ou restreint.",
            "confidentialite.yml",
        )
    git_cfg = privacy.get("git", {})
    ai_cfg = privacy.get("ia", {})
    if not isinstance(git_cfg, dict) or not isinstance(ai_cfg, dict):
        report.add(
            "PRIVACY_STRUCTURE_INVALID",
            "error",
            "Les sections `git` et `ia` doivent être des objets.",
            "confidentialite.yml",
        )
        return
    if git_cfg.get("autorise") is False:
        report.add(
            "GIT_NOT_AUTHORIZED",
            "warning",
            "Git n'est pas autorisé : utiliser le circuit institutionnel convenu.",
            "confidentialite.yml",
        )
    ai_enabled = ai_cfg.get("assistance_autorisee") or ai_cfg.get("evaluation_autorisee")
    if level == "restreint" and ai_enabled and not ai_cfg.get("cadre_adapte"):
        report.add(
            "AI_RESTRICTED_WITHOUT_FRAMEWORK",
            "error",
            "Une IA est autorisée sur un projet restreint sans cadre adapté déclaré.",
            "confidentialite.yml",
        )
    if ai_enabled and not ai_cfg.get("contenu_autorise"):
        report.add(
            "AI_ALLOWLIST_MISSING",
            "error",
            "Une IA est autorisée mais aucun contenu autorisé n'est déclaré.",
            "confidentialite.yml",
        )


def _check_requirement(report: CheckReport, root: Path, artifact: Any, phase: str) -> None:
    rel = relative_path(root, artifact.path)
    if artifact.status == "valide" and not _as_list(artifact.data.get("sources")):
        report.add(
            "REQUIREMENT_WITHOUT_SOURCE",
            "error",
            "Une exigence validée doit référencer sa source.",
            rel,
            artifact.identifier,
        )
    if artifact.status == "valide" and not _as_list(artifact.data.get("criteres")):
        report.add(
            "REQUIREMENT_WITHOUT_CRITERION",
            "error",
            "Une exigence validée doit référencer un critère d'acceptation.",
            rel,
            artifact.identifier,
        )
    if phase in LATE_PHASES and not _as_list(artifact.data.get("conception")):
        report.add(
            "REQUIREMENT_WITHOUT_DESIGN",
            "warning",
            "L'exigence n'est reliée à aucun élément de conception.",
            rel,
            artifact.identifier,
        )
    if phase in LATE_PHASES and not _as_list(artifact.data.get("preuves")):
        report.add(
            "REQUIREMENT_WITHOUT_EVIDENCE",
            "warning",
            "L'exigence ne possède aucune preuve référencée.",
            rel,
            artifact.identifier,
        )


def _check_evidence(report: CheckReport, root: Path, artifact: Any) -> None:
    if not _as_list(artifact.data.get("exigences")):
        report.add(
            "EVIDENCE_ORPHAN",
            "warning",
            "La preuve n'est reliée à aucune exigence.",
            relative_path(root, artifact.path),
            artifact.identifier,
        )
    if not artifact.data.get("limites"):
        report.add(
            "EVIDENCE_WITHOUT_LIMIT",
            "warning",
            "Les limites de la preuve ne sont pas explicitées.",
            relative_path(root, artifact.path),
            artifact.identifier,
        )
