from __future__ import annotations

from typing import Iterator, Optional

from git_regret.models.pattern import Pattern, Severity
from .definitions import RAW_PATTERNS, DANGEROUS_FILES


class PatternRegistry:
    """
    Loads, indexes and queries all detection patterns.
    Designed to be used as a singleton.
    """

    def __init__(self) -> None:
        self._patterns: dict[str, Pattern] = {}
        self._load()

    def _load(self) -> None:
        for raw in RAW_PATTERNS:
            pattern = Pattern(
                id=raw["id"],
                regex=raw["regex"],
                description=raw["description"],
                severity=Severity(raw["severity"]),
                tags=tuple(raw.get("tags", [])),
            )
            self._patterns[pattern.id] = pattern

    def all(self) -> list[Pattern]:
        return list(self._patterns.values())

    def get(self, pattern_id: str) -> Optional[Pattern]:
        return self._patterns.get(pattern_id)

    def by_severity(self, severity: Severity) -> list[Pattern]:
        return [p for p in self._patterns.values() if p.severity == severity]

    def by_tag(self, tag: str) -> list[Pattern]:
        return [p for p in self._patterns.values() if p.has_tag(tag)]

    def iter(self) -> Iterator[Pattern]:
        yield from self._patterns.values()

    @property
    def dangerous_files(self) -> list[str]:
        return DANGEROUS_FILES

    def __len__(self) -> int:
        return len(self._patterns)

    def __repr__(self) -> str:
        return f"<PatternRegistry patterns={len(self)}>"


# Module-level singleton
registry = PatternRegistry()
