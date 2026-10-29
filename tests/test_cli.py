import json
from pathlib import Path

import pytest

from assistant_ia_projets.cli import _dispatch, _parser, init_project
from assistant_ia_projets.guidance import start_summary, start_text
from assistant_ia_projets.models import CoherenceError


def test_init_sets_title_and_campus(tmp_path: Path) -> None:
    destination = tmp_path / "projet"
    init_project(destination, campus="bordeaux", title="Robot utile")
    text = (destination / "projet.yml").read_text(encoding="utf-8")
    assert "Robot utile" in text
    assert "campus: bordeaux" in text
    assert (destination / ".gitignore").exists()
    assert (destination / "PROMPT_DEMARRAGE.md").exists()


def test_init_refuses_non_empty_destination(tmp_path: Path) -> None:
    destination = tmp_path / "projet"
    destination.mkdir()
    (destination / "important.txt").write_text("à préserver", encoding="utf-8")
    with pytest.raises(CoherenceError):
        init_project(destination, campus="paris", title="Test")
    assert (destination / "important.txt").read_text(encoding="utf-8") == "à préserver"


def test_start_orients_without_ai(tmp_path: Path) -> None:
    destination = tmp_path / "projet"
    init_project(destination, campus="paris", title="Projet guidé")

    summary = start_summary(destination)
    text = start_text(destination)

    assert summary["phase"] == "cadrage"
    assert summary["assistance_ia_autorisee"] is False
    assert "Par où commencer" in text
    assert "coherence check" in text


def test_cli_separates_read_propose_and_apply() -> None:
    parser = _parser()
    assert parser.parse_args(["start"]).command == "start"
    assert parser.parse_args(["ask", "Par où commencer ?"]).command == "ask"
    assert parser.parse_args(["propose", "Structure le besoin"]).command == "propose"
    assert parser.parse_args(["apply", "proposition.json"]).command == "apply"


def test_apply_uses_local_proposal_without_ai_authorization(tmp_path: Path) -> None:
    destination = tmp_path / "projet"
    init_project(destination, campus="paris", title="Application locale")
    proposal_path = destination / "ecarts" / "proposition-test.json"
    proposal_path.write_text(
        json.dumps(
            {
                "changements": [
                    {
                        "chemin": "cadrage/note-locale.md",
                        "action": "creer",
                        "contenu": "# Note locale\n",
                        "justification": "test",
                        "artefacts_affectes": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    args = _parser().parse_args(
        ["apply", "ecarts/proposition-test.json", "--root", str(destination)]
    )

    assert _dispatch(args) == 0
    assert (destination / "cadrage" / "note-locale.md").exists()
