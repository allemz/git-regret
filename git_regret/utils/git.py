from __future__ import annotations

from pathlib import Path
from typing import Iterator, Optional

import git


class GitRepo:
    """Helper class for git repository operations."""

    # Tarama için gereksiz dizinler
    IGNORED_DIRS = frozenset({
        ".git",
        "node_modules",
        ".venv", "venv", "env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "dist", "build",
        ".next", ".nuxt", ".svelte-kit",
        "vendor",
        ".idea", ".vscode",
        "coverage", ".nyc_output",
        "target",
        "Pods",
        ".gradle",
    })

    # Tarama için gereksiz dosya uzantıları 
    IGNORED_EXTENSIONS = frozenset({
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
        ".mp4", ".mp3", ".wav", ".avi", ".mov",
        ".zip", ".tar", ".gz", ".rar", ".7z",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".woff", ".woff2", ".ttf", ".eot",
        ".pyc", ".pyo",
        ".map",
    })

    def __init__(self, path: str | Path = ".") -> None:
        self.path = Path(path).resolve()
        self._repo: Optional[git.Repo] = None

    @property
    def repo(self) -> git.Repo:
        if self._repo is None:
            self._repo = git.Repo(self.path)
        return self._repo

    @property
    def is_valid(self) -> bool:
        try:
            _ = self.repo
            return True
        except git.InvalidGitRepositoryError:
            return False

    @property
    def commit_count(self) -> int:
        try:
            return sum(1 for _ in self.repo.iter_commits())
        except Exception:
            return 0

    def _is_ignored(self, file_path: Path) -> bool:
        """Return True if this file should be skipped."""
        for part in file_path.parts:
            if part in self.IGNORED_DIRS:
                return True
        if file_path.suffix.lower() in self.IGNORED_EXTENSIONS:
            return True
        return False

    def iter_commits(self) -> Iterator[git.Commit]:
        try:
            yield from self.repo.iter_commits()
        except Exception:
            return

    def iter_blobs(self, commit: git.Commit) -> Iterator[tuple[str, bytes]]:
        """
        Yield all blobs (file contents) in a commit.
        Yields: (file_path, raw_content)
        """
        try:
            for item in commit.tree.traverse():
                if item.type == "blob":
                    # Skip ignored paths in history too
                    p = Path(item.path)
                    if self._is_ignored(p):
                        continue
                    try:
                        yield item.path, item.data_stream.read()
                    except Exception:
                        continue
        except Exception:
            return

    def iter_working_files(self) -> Iterator[tuple[str, Path]]:
        """
        Yield all scannable files in the working directory.
        Skips ignored directories and binary/irrelevant file types.
        Yields: (relative_path, absolute_path)
        """
        for file_path in self.path.rglob("*"):
            if not file_path.is_file():
                continue
            if self._is_ignored(file_path):
                continue
            try:
                rel = str(file_path.relative_to(self.path))
                yield rel, file_path
            except ValueError:
                continue

    def commit_info(self, commit: git.Commit) -> dict:
        return {
            "hash":    commit.hexsha[:7],
            "message": commit.message.strip()[:80],
            "author":  str(commit.author),
            "date":    commit.committed_datetime.isoformat(),
        }
