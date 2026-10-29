import json
import sys
import types
from pathlib import Path

import pytest
import yaml

import assistant_ia_projets.ai as ai_module
from assistant_ia_projets.ai import _request, apply_proposal
from assistant_ia_projets.cli import init_project
from assistant_ia_projets.models import CoherenceError
from assistant_ia_projets.security import collect_context, safe_change_path


def authorized_project(tmp_path: Path) -> Path:
    root = tmp_path / "projet"
    init_project(root, campus="bordeaux", title="Projet autorisé")
    policy_path = root / "confidentialite.yml"
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    policy["ia"]["assistance_autorisee"] = True
    policy["ia"]["evaluation_autorisee"] = True
    policy_path.write_text(yaml.safe_dump(policy, allow_unicode=True), encoding="utf-8")
    return root


def proposal(path: str, action: str, content: str) -> dict:
    return {
        "changements": [
            {
                "chemin": path,
                "action": action,
                "contenu": content,
                "justification": "test",
                "artefacts_affectes": [],
            }
        ]
    }


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    root = authorized_project(tmp_path)
    settings = yaml.safe_load((root / "confidentialite.yml").read_text(encoding="utf-8"))["ia"]
    with pytest.raises(CoherenceError):
        safe_change_path(root, "../hors-projet.md", settings)


def test_model_cannot_promote_status_to_validated(tmp_path: Path) -> None:
    root = authorized_project(tmp_path)
    target = root / "cadrage" / "nouveau.md"
    with pytest.raises(CoherenceError):
        apply_proposal(
            root,
            proposal(
                "cadrage/nouveau.md",
                "creer",
                "---\nid: DOC-099\nstatut: valide\n---\n",
            ),
        )
    assert not target.exists()


def test_authorized_change_is_applied(tmp_path: Path) -> None:
    root = authorized_project(tmp_path)
    changes = apply_proposal(
        root,
        proposal("cadrage/note.md", "creer", "# Note proposée\n"),
    )
    assert (root / "cadrage" / "note.md").read_text(encoding="utf-8") == "# Note proposée\n"
    assert len(changes.paths) == 1


def test_potential_secret_stops_context_collection(tmp_path: Path) -> None:
    root = authorized_project(tmp_path)
    (root / "cadrage" / "secret.md").write_text(
        "api_key = 'abcdefghijklmnopqrstuv'\n", encoding="utf-8"
    )
    with pytest.raises(CoherenceError):
        collect_context(root, "assistance")


def test_openai_request_is_structured_and_not_stored(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    class FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(output_text=json.dumps({"ok": True}))

    class FakeOpenAI:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    payload = _request(
        model="modele-test",
        instructions="instructions",
        user_input="entrée",
        schema={"type": "object", "properties": {}, "additionalProperties": False},
        schema_name="test_schema",
    )

    assert payload == {"ok": True}
    assert captured["store"] is False
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["strict"] is True


def test_read_only_question_uses_dedicated_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = authorized_project(tmp_path)
    captured = {}

    def fake_request(**kwargs):
        captured.update(kwargs)
        return {
            "reponse": "Commencer par le besoin.",
            "sources": ["cadrage/besoin.md"],
            "questions": [],
            "avis_expert_requis": False,
        }

    monkeypatch.setattr(ai_module, "_request", fake_request)
    result = ai_module.ask(root, "Par où commencer ?", model="modele-test")

    assert result["reponse"] == "Commencer par le besoin."
    assert captured["schema_name"] == "lecture_projet"
    assert "strictement non modifiant" in captured["instructions"]

