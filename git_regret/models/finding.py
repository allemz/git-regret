from dataclasses import dataclass
from typing import Optional
from .pattern import Pattern, Severity


def _mask(text: str) -> str:
    """Mask sensitive value — only the first 4 characters are visible."""
    if len(text) <= 4:
        return "****"
    return text[:4] + "*" * min(len(text) - 4, 20)


@dataclass
class Finding:
    pattern: Pattern
    file_path: str
    line_number: int
    matched_text: str
    commit_hash: Optional[str] = None
    commit_message: Optional[str] = None
    commit_author: Optional[str] = None
    commit_date: Optional[str] = None

    @property
    def severity(self) -> Severity:
        return self.pattern.severity

    @property
    def description(self) -> str:
        return self.pattern.description

    @property
    def masked_match(self) -> str:
        return _mask(self.matched_text)

    @property
    def is_in_history(self) -> bool:
        return self.commit_hash is not None

    @property
    def location(self) -> str:
        base = f"{self.file_path}:{self.line_number}"
        if self.commit_hash:
            return f"{self.commit_hash[:7]} -> {base}"
        return base

    def to_dict(self) -> dict:
        return {
            "pattern_id":     self.pattern.id,
            "description":    self.description,
            "severity":       self.severity.value,
            "file_path":      self.file_path,
            "line_number":    self.line_number,
            "masked_match":   self.masked_match,
            "commit_hash":    self.commit_hash,
            "commit_message": self.commit_message,
            "commit_author":  self.commit_author,
            "commit_date":    self.commit_date,
        }
