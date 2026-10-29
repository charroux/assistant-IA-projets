from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from .models import CoherenceError
from .repository import artifact_map, iter_id_references, load_artifacts, relative_path


def build_graph(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], dict[str, Any]]:
    artifacts = load_artifacts(root)
    by_id = artifact_map(artifacts)
    outgoing: dict[str, set[str]] = defaultdict(set)
    incoming: dict[str, set[str]] = defaultdict(set)
    for artifact in artifacts:
        if not artifact.identifier:
            continue
        for target in iter_id_references(artifact.data):
            if target in by_id:
                outgoing[artifact.identifier].add(target)
                incoming[target].add(artifact.identifier)
    metadata = {
        identifier: {
            "type": artifact.kind,
            "statut": artifact.status,
            "fichier": relative_path(root, artifact.path),
        }
        for identifier, artifact in by_id.items()
    }
    return outgoing, incoming, metadata


def impact(root: Path, identifier: str, *, max_depth: int = 5) -> dict[str, Any]:
    outgoing, incoming, metadata = build_graph(root)
    if identifier not in metadata:
        raise CoherenceError(f"Identifiant inconnu : {identifier}")

    def walk(edges: dict[str, set[str]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        queue: deque[tuple[str, int]] = deque([(identifier, 0)])
        visited = {identifier}
        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue
            for neighbor in sorted(edges.get(current, set())):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                next_depth = depth + 1
                result.append(
                    {
                        "id": neighbor,
                        "profondeur": next_depth,
                        **metadata[neighbor],
                    }
                )
                queue.append((neighbor, next_depth))
        return result

    return {
        "artefact": {"id": identifier, **metadata[identifier]},
        "references": walk(outgoing),
        "reference_par": walk(incoming),
    }

