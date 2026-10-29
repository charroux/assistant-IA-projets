from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Artifact:
    identifier: str
    kind: str
    status: str
    path: Path
    data: dict[str, Any]


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    path: str | None = None
    artifact_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
            "artifact_id": self.artifact_id,
        }


@dataclass
class CheckReport:
    root: Path
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(
        self,
        code: str,
        severity: str,
        message: str,
        path: str | None = None,
        artifact_id: str | None = None,
    ) -> None:
        self.findings.append(
            Finding(code, severity, message, path=path, artifact_id=artifact_id)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "ok": self.ok,
            "counts": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "total": len(self.findings),
            },
            "findings": [item.to_dict() for item in self.findings],
        }


class CoherenceError(RuntimeError):
    """Erreur compréhensible par l'utilisateur de la CLI."""

