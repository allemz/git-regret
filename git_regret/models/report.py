from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional

from .finding import Finding
from .pattern import Severity


@dataclass
class Report:
    scanned_path: str
    include_history: bool
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = field(default=None)
    findings: list[Finding] = field(default_factory=list)
    scanned_files: int = 0
    scanned_commits: int = 0

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def finish(self) -> None:
        self.finished_at = datetime.utcnow()

    @property
    def duration_seconds(self) -> float:
        if not self.finished_at:
            return 0.0
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def total(self) -> int:
        return len(self.findings)

    @property
    def is_clean(self) -> bool:
        return self.total == 0

    def by_severity(self, severity: Severity) -> list[Finding]:
        return [f for f in self.findings if f.severity == severity]

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: f.severity)

    def iter_by_severity(self) -> Iterator[tuple[Severity, list[Finding]]]:
        for severity in sorted(Severity, key=lambda s: s.priority):
            group = self.by_severity(severity)
            if group:
                yield severity, group

    def summary(self) -> dict[str, int]:
        return {
            severity.value: len(self.by_severity(severity))
            for severity in Severity
        }

    def to_dict(self) -> dict:
        return {
            "scanned_path": self.scanned_path,
            "include_history": self.include_history,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": self.duration_seconds,
            "scanned_files": self.scanned_files,
            "scanned_commits": self.scanned_commits,
            "total_findings": self.total,
            "summary": self.summary(),
            "findings": [f.to_dict() for f in self.sorted_findings()],
        }
