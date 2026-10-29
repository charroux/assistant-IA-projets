from pathlib import Path

import pytest

from assistant_ia_projets.cli import init_project
from assistant_ia_projets.models import CoherenceError


def test_init_sets_title_and_campus(tmp_path: Path) -> None:
    destination = tmp_path / "projet"
    init_project(destination, campus="bordeaux", title="Robot utile")
    text = (destination / "projet.yml").read_text(encoding="utf-8")
    assert "Robot utile" in text
    assert "campus: bordeaux" in text


def test_init_refuses_non_empty_destination(tmp_path: Path) -> None:
    destination = tmp_path / "projet"
    destination.mkdir()
    (destination / "important.txt").write_text("à préserver", encoding="utf-8")
    with pytest.raises(CoherenceError):
        init_project(destination, campus="paris", title="Test")
    assert (destination / "important.txt").read_text(encoding="utf-8") == "à préserver"
