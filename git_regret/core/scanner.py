from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from git_regret.models import Finding, Report
from git_regret.models.pattern import Pattern
from git_regret.patterns import registry
from git_regret.utils.entropy import find_high_entropy_strings
from git_regret.utils.git import GitRepo

console = Console()


class Scanner:
    """
    Scans a repository and produces Finding objects.
    Working directory and git history are scanned via separate methods.
    """

    def __init__(self, repo_path: str | Path = ".") -> None:
        self.repo_path = Path(repo_path).resolve()
        self._git = GitRepo(self.repo_path)

    # 
    # Public API
    # 

    def scan(self, include_history: bool = False) -> Report:
        report = Report(
            scanned_path=str(self.repo_path),
            include_history=include_history,
        )
        self._scan_working_directory(report)
        if include_history:
            self._scan_git_history(report)
        report.finish()
        return report

    # 
    # Working Directory
    # 

    def _scan_working_directory(self, report: Report) -> None:
        files = list(self._git.iter_working_files())

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Scanning working directory..."),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("scan", total=len(files))
            for rel_path, abs_path in files:
                self._scan_file(abs_path, rel_path, report)
                report.scanned_files += 1
                progress.advance(task)

    def _scan_file(self, abs_path: Path, rel_path: str, report: Report) -> None:
        # Check for dangerous file names
        if abs_path.name in registry.dangerous_files:
            report.add(Finding(
                pattern=self._dangerous_file_pattern(abs_path.name),
                file_path=rel_path,
                line_number=0,
                matched_text=abs_path.name,
            ))

        try:
            content = abs_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return

        self._scan_content(content, rel_path, report)

    # 
    # Git History
    # 

    def _scan_git_history(self, report: Report) -> None:
        if not self._git.is_valid:
            console.print("[red]❌ No valid git repository found.[/red]")
            return

        commits = list(self._git.iter_commits())

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Scanning git history..."),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("history", total=len(commits))
            for commit in commits:
                info = self._git.commit_info(commit)
                for file_path, raw in self._git.iter_blobs(commit):
                    try:
                        content = raw.decode("utf-8", errors="ignore")
                        self._scan_content(
                            content,
                            file_path,
                            report,
                            commit_hash=info["hash"],
                            commit_message=info["message"],
                            commit_author=info["author"],
                            commit_date=info["date"],
                        )
                    except Exception:
                        continue
                report.scanned_commits += 1
                progress.advance(task)

    # 
    # Content Scanning
    # 

    def _scan_content(
        self,
        content: str,
        file_path: str,
        report: Report,
        commit_hash: str | None = None,
        commit_message: str | None = None,
        commit_author: str | None = None,
        commit_date: str | None = None,
    ) -> None:
        lines = content.splitlines()

        for line_no, line in enumerate(lines, start=1):
            # Pattern-based scanning
            for pattern in registry.iter():
                for match in pattern.matches(line):
                    report.add(Finding(
                        pattern=pattern,
                        file_path=file_path,
                        line_number=line_no,
                        matched_text=match.group(),
                        commit_hash=commit_hash,
                        commit_message=commit_message,
                        commit_author=commit_author,
                        commit_date=commit_date,
                    ))

            # Entropy-based scanning
            for secret in find_high_entropy_strings(line):
                report.add(Finding(
                    pattern=self._entropy_pattern(),
                    file_path=file_path,
                    line_number=line_no,
                    matched_text=secret,
                    commit_hash=commit_hash,
                    commit_message=commit_message,
                    commit_author=commit_author,
                    commit_date=commit_date,
                ))

    # 
    # Built-in Synthetic Patterns
    #

    @staticmethod
    def _dangerous_file_pattern(filename: str) -> Pattern:
        from git_regret.models.pattern import Severity
        return Pattern(
            id="dangerous_file",
            regex="",
            description=f"Dangerous file: {filename}",
            severity=Severity.HIGH,
            tags=("file",),
        )

    @staticmethod
    def _entropy_pattern() -> Pattern:
        from git_regret.models.pattern import Severity
        return Pattern(
            id="high_entropy_string",
            regex="",
            description="High-entropy string (likely a secret)",
            severity=Severity.MEDIUM,
            tags=("entropy",),
        )
