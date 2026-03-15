from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from git_regret.models import Report, Finding

console = Console()


class Cleaner:
    """
    Removes discovered secrets from git history.
    Uses git-filter-repo under the hood.
    """

    def __init__(self, repo_path: str | Path = ".") -> None:
        self.repo_path = Path(repo_path).resolve()

    def clean(self, report: Report, dry_run: bool = False) -> None:
        if report.is_clean:
            console.print("[green]✅ Nothing to clean.[/green]")
            return

        history_findings = [f for f in report.findings if f.is_in_history]
        working_findings  = [f for f in report.findings if not f.is_in_history]

        if working_findings:
            self._handle_working_dir(working_findings, dry_run)

        if history_findings:
            self._handle_history(history_findings, dry_run)

    def _handle_working_dir(self, findings: list[Finding], dry_run: bool) -> None:
        console.print(f"\n[yellow]⚠️  {len(findings)} issue(s) found in the working directory.[/yellow]")
        console.print("[dim]Remember to add these files to .gitignore and remove their contents.[/dim]")

        files = {f.file_path for f in findings}
        for file in files:
            console.print(f"  [red]•[/red] {file}")

    def _handle_history(self, findings: list[Finding], dry_run: bool) -> None:
        if not self._check_filter_repo():
            console.print(
                "[red]❌ git-filter-repo is not installed.\n"
                "  pip install git-filter-repo[/red]"
            )
            return

        files_to_clean = {f.file_path for f in findings}
        console.print(f"\n[bold red]🧹 {len(files_to_clean)} file(s) will be removed from git history.[/bold red]")

        if dry_run:
            console.print("[yellow]Dry-run mode: nothing was changed.[/yellow]")
            for f in files_to_clean:
                console.print(f"  [dim]• {f}[/dim]")
            return

        for file_path in files_to_clean:
            self._remove_file_from_history(file_path)

    def _remove_file_from_history(self, file_path: str) -> None:
        console.print(f"[dim]Removing: {file_path}[/dim]")
        result = subprocess.run(
            ["git", "filter-repo", "--path", file_path, "--invert-paths", "--force"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(f"[green]✅ {file_path} removed from history.[/green]")
        else:
            console.print(f"[red]❌ Failed to remove {file_path}: {result.stderr}[/red]")

    @staticmethod
    def _check_filter_repo() -> bool:
        result = subprocess.run(
            ["git", "filter-repo", "--version"],
            capture_output=True,
        )
        return result.returncode == 0
