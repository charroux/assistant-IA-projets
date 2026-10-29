from pathlib import Path

import yaml

from assistant_ia_projets.checks import run_checks
from assistant_ia_projets.cli import init_project
from assistant_ia_projets.graph import impact


def project(tmp_path: Path) -> Path:
    root = tmp_path / "projet"
    init_project(root, campus="paris", title="Projet de test")
    return root


def test_template_has_no_deterministic_error(tmp_path: Path) -> None:
    report = run_checks(project(tmp_path))
    assert report.errors == []


def test_duplicate_identifier_is_an_error(tmp_path: Path) -> None:
    root = project(tmp_path)
    path = root / "cadrage" / "exigences.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["exigences"].append(dict(data["exigences"][0]))
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    codes = {item.code for item in run_checks(root).errors}
    assert "ID_DUPLICATE" in codes


def test_missing_reference_is_an_error(tmp_path: Path) -> None:
    root = project(tmp_path)
    path = root / "cadrage" / "exigences.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["exigences"][0]["sources"] = ["BES-999"]
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    codes = {item.code for item in run_checks(root).errors}
    assert "REFERENCE_MISSING" in codes


def test_impact_walks_upstream_and_downstream(tmp_path: Path) -> None:
    root = project(tmp_path)
    result = impact(root, "EXG-001")
    upstream = {item["id"] for item in result["references"]}
    downstream = {item["id"] for item in result["reference_par"]}

    assert "BES-001" in upstream
    assert "PROD-001" in downstream
    assert "CPT-001" in downstream


def test_restricted_ai_needs_adapted_framework(tmp_path: Path) -> None:
    root = project(tmp_path)
    path = root / "confidentialite.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["niveau"] = "restreint"
    data["ia"]["assistance_autorisee"] = True
    data["ia"]["cadre_adapte"] = False
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    codes = {item.code for item in run_checks(root).errors}
    assert "AI_RESTRICTED_WITHOUT_FRAMEWORK" in codes

