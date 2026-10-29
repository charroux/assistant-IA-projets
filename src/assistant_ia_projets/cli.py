from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

from . import __version__
from .ai import apply_proposal, ask as ask_ai, audit, propose as propose_ai, rollback
from .checks import run_checks
from .config import dump_yaml, load_yaml
from .gitops import commit_files, current_commit, dirty_paths, is_repository
from .graph import impact
from .guidance import start_text
from .models import CoherenceError
from .reports import audit_markdown, check_markdown, check_text, write_json


def _root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coherence",
        description="Cohérence documentaire des projets étudiants.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Créer un projet depuis le modèle.")
    init.add_argument("destination")
    init.add_argument("--campus", choices=["paris", "bordeaux"], required=True)
    init.add_argument("--title", default="Engineering Project")

    start = sub.add_parser("start", help="Expliquer les prochaines étapes sans IA.")
    start.add_argument("--root", default=".")

    check = sub.add_parser("check", help="Exécuter les contrôles déterministes.")
    check.add_argument("--root", default=".")
    check.add_argument("--json", action="store_true")
    check.add_argument("--strict", action="store_true", help="Échouer aussi sur les avertissements.")

    impact_cmd = sub.add_parser("impact", help="Analyser les dépendances d'un artefact.")
    impact_cmd.add_argument("identifier")
    impact_cmd.add_argument("--root", default=".")
    impact_cmd.add_argument("--depth", type=int, default=5)
    impact_cmd.add_argument("--json", action="store_true")

    report = sub.add_parser("report", help="Générer le rapport déterministe Markdown.")
    report.add_argument("--root", default=".")
    report.add_argument("--output", default="evaluation/rapport-coherence.md")

    ask = sub.add_parser("ask", help="Poser une question à l'IA en lecture seule.")
    ask.add_argument("question")
    ask.add_argument("--root", default=".")
    ask.add_argument("--model")

    proposal = sub.add_parser("propose", help="Créer une proposition IA sans l'appliquer.")
    proposal.add_argument("question")
    proposal.add_argument("--root", default=".")
    proposal.add_argument("--model")
    proposal.add_argument("--output")

    apply_cmd = sub.add_parser("apply", help="Appliquer une proposition IA déjà examinée.")
    apply_cmd.add_argument("proposal")
    apply_cmd.add_argument("--root", default=".")
    apply_cmd.add_argument("--commit", action="store_true")

    evaluator = sub.add_parser("audit", help="Lancer l'audit IA indépendant.")
    evaluator.add_argument("--root", default=".")
    evaluator.add_argument("--model")
    evaluator.add_argument("--save", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    try:
        code = _dispatch(args)
    except CoherenceError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        code = 2
    raise SystemExit(code)


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "init":
        init_project(_root(args.destination), campus=args.campus, title=args.title)
        print(f"Projet créé dans {Path(args.destination).resolve()}")
        print("Prochaine étape : vérifier confidentialite.yml puis lancer `coherence check`.")
        return 0
    if args.command == "start":
        print(start_text(_root(args.root)))
        return 0
    if args.command == "check":
        report = run_checks(_root(args.root))
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) if args.json else check_text(report))
        return 1 if report.errors or (args.strict and report.warnings) else 0
    if args.command == "impact":
        data = impact(_root(args.root), args.identifier, max_depth=args.depth)
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else _impact_text(data))
        return 0
    if args.command == "report":
        root = _root(args.root)
        output = _output_path(root, args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(check_markdown(run_checks(root)), encoding="utf-8")
        print(f"Rapport écrit : {output}")
        return 0
    if args.command == "ask":
        return _ask_command(args)
    if args.command == "propose":
        return _propose_command(args)
    if args.command == "apply":
        return _apply_command(args)
    if args.command == "audit":
        return _audit_command(args)
    raise CoherenceError(f"Commande inconnue : {args.command}")


def init_project(destination: Path, *, campus: str, title: str) -> None:
    if destination.exists():
        unexpected = [item for item in destination.iterdir() if item.name != ".git"]
        if unexpected:
            raise CoherenceError("La destination doit être vide ou ne contenir que `.git`.")
    else:
        destination.mkdir(parents=True)
    template = resources.files("assistant_ia_projets").joinpath("templates", "projet")
    with resources.as_file(template) as template_path:
        for child in template_path.iterdir():
            target = destination / child.name
            if child.is_dir():
                shutil.copytree(child, target, dirs_exist_ok=True)
            else:
                shutil.copy2(child, target)
    project_path = destination / "projet.yml"
    project = load_yaml(project_path)
    project["titre"] = title
    project["campus"] = campus
    dump_yaml(project_path, project)


def _ask_command(args: argparse.Namespace) -> int:
    root = _root(args.root)
    result = ask_ai(root, args.question, model=args.model)
    print(_ask_text(result))
    print("\nLecture seule : aucun fichier n'a été modifié.")
    print("Pensez à déclarer cet usage dans usage_ia.yml.")
    return 0


def _propose_command(args: argparse.Namespace) -> int:
    root = _root(args.root)
    proposal = propose_ai(root, args.question, model=args.model)
    print(_assistant_text(proposal))
    relative = args.output or f"ecarts/propositions/proposition-{_stamp()}.json"
    output = _output_path(root, relative)
    write_json(output, proposal)
    print(f"\nProposition enregistrée : {output}")
    print(f"Après examen : coherence apply \"{relative}\"")
    print("Aucun fichier du projet n'a encore été modifié.")
    print("Pensez à déclarer cet usage dans usage_ia.yml.")
    return 0


def _apply_command(args: argparse.Namespace) -> int:
    root = _root(args.root)
    proposal_path = _output_path(root, args.proposal)
    if not proposal_path.exists():
        raise CoherenceError(f"Proposition introuvable : {proposal_path}")
    try:
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CoherenceError(f"Proposition JSON illisible : {exc}") from exc
    if not isinstance(proposal, dict) or not isinstance(proposal.get("changements"), list):
        raise CoherenceError("Le fichier ne contient pas une proposition valide.")
    before = dirty_paths(root) if args.commit else []
    if before:
        raise CoherenceError(
            "Le dépôt contient déjà des modifications ; commit automatique refusé : "
            + ", ".join(before)
        )

    changes = apply_proposal(root, proposal)
    if not changes.paths:
        print("La proposition ne contient aucun changement applicable.")
        return 0
    verification = run_checks(root)
    if verification.errors:
        rollback(changes)
        raise CoherenceError(
            "Les changements ont été annulés car les contrôles ont détecté des erreurs.\n"
            + check_text(verification)
        )
    print(f"{len(changes.paths)} fichier(s) modifié(s).")
    print("Vérifiez maintenant le diff avant toute validation humaine.")
    if args.commit:
        commit = commit_files(
            root,
            changes.paths,
            "assistant: appliquer une proposition de cohérence",
        )
        print(f"Commit créé : {commit}")
    return 0


def _audit_command(args: argparse.Namespace) -> int:
    root = _root(args.root)
    if is_repository(root):
        dirty = dirty_paths(root)
        if dirty:
            raise CoherenceError(
                "L'audit exige un dépôt propre et figé : " + ", ".join(dirty)
            )
    commit = current_commit(root)
    result = audit(root, commit=commit, model=args.model)
    print(audit_markdown(result))
    if args.save:
        output_dir = root / "evaluation" / "rapports"
        name = f"audit-{_stamp()}-{commit[:8]}"
        json_path = output_dir / f"{name}.json"
        md_path = output_dir / f"{name}.md"
        write_json(json_path, result)
        md_path.write_text(audit_markdown(result), encoding="utf-8")
        print(f"Audit écrit : {md_path}")
        print(f"Données structurées : {json_path}")
    return 0


def _output_path(root: Path, value: str) -> Path:
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise CoherenceError("Le fichier de sortie doit rester dans le projet.") from exc
    return candidate


def _impact_text(data: dict[str, Any]) -> str:
    head = data["artefact"]
    lines = [
        f"{head['id']} — {head['type']} — {head['statut']}",
        "",
        "Référence :",
    ]
    lines.extend(
        f"  {'  ' * (item['profondeur'] - 1)}- {item['id']} ({item['type']})"
        for item in data["references"]
    )
    if not data["references"]:
        lines.append("  - aucun artefact")
    lines.append("\nEst référencé par :")
    lines.extend(
        f"  {'  ' * (item['profondeur'] - 1)}- {item['id']} ({item['type']})"
        for item in data["reference_par"]
    )
    if not data["reference_par"]:
        lines.append("  - aucun artefact")
    return "\n".join(lines)


def _assistant_text(data: dict[str, Any]) -> str:
    lines = [data.get("resume", ""), "", "Observations :"]
    for item in data.get("observations", []):
        expert = " — avis expert requis" if item.get("avis_expert_requis") else ""
        lines.append(f"- [{item.get('gravite')}] {item.get('titre')}{expert}")
        lines.append(f"  {item.get('constat')}")
    lines.append("\nQuestions :")
    lines.extend(f"- {item}" for item in data.get("questions", []))
    lines.append("\nChangements proposés :")
    for item in data.get("changements", []):
        lines.append(
            f"- {item.get('action')} {item.get('chemin')} — {item.get('justification')}"
        )
    lines.append("\nDécisions humaines requises :")
    lines.extend(f"- {item}" for item in data.get("decisions_humaines_requises", []))
    if data.get("synthese_monday"):
        lines.extend(["", "Synthèse proposée pour Monday :", data["synthese_monday"]])
    return "\n".join(lines)


def _ask_text(data: dict[str, Any]) -> str:
    lines = [data.get("reponse", "")]
    sources = data.get("sources", [])
    if sources:
        lines.extend(["", "Sources consultées :"])
        lines.extend(f"- {item}" for item in sources)
    questions = data.get("questions", [])
    if questions:
        lines.extend(["", "Questions à clarifier :"])
        lines.extend(f"- {item}" for item in questions)
    if data.get("avis_expert_requis"):
        lines.extend(["", "Un avis expert est nécessaire pour une partie de la réponse."])
    return "\n".join(lines)


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
