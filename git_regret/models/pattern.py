from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"

    @property
    def color(self) -> str:
        return {
            Severity.CRITICAL: "red",
            Severity.HIGH:     "orange3",
            Severity.MEDIUM:   "yellow",
            Severity.LOW:      "green",
        }[self]

    @property
    def priority(self) -> int:
        return {
            Severity.CRITICAL: 0,
            Severity.HIGH:     1,
            Severity.MEDIUM:   2,
            Severity.LOW:      3,
        }[self]

    def __lt__(self, other: "Severity") -> bool:
        return self.priority < other.priority


@dataclass(frozen=True)
class Pattern:
    id: str
    regex: str
    description: str
    severity: Severity
    tags: tuple[str, ...] = field(default_factory=tuple)
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_compiled", re.compile(self.regex) if self.regex else None)

    @property
    def compiled(self) -> Optional[re.Pattern]:
        return self._compiled

    def matches(self, text: str) -> list[re.Match]:
        if not self._compiled:
            return []
        return list(self._compiled.finditer(text))

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags
