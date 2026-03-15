from __future__ import annotations

import stat
from pathlib import Path

from rich.console import Console

console = Console()

HOOK_SCRIPT = """\
#!/bin/sh
# git-regret pre-commit hook
# Auto-generated. Do not delete!

echo "🔍 git-regret: Scanning staged files..."

git-regret scan --staged --fail-on-findings

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ git-regret: Secret detected! Commit aborted."
    echo "   Fix the issue and try again."
    exit 1
fi

echo "✅ git-regret: Clean, proceeding with commit."
exit 0
"""


class HookManager:
    """Manages git pre-commit hooks."""

    def __init__(self, repo_path: str | Path = ".") -> None:
        self.repo_path = Path(repo_path).resolve()
        self.hooks_dir = self.repo_path / ".git" / "hooks"
        self.hook_path = self.hooks_dir / "pre-commit"

    @property
    def is_installed(self) -> bool:
        return self.hook_path.exists()

    def install(self) -> None:
        if not self.hooks_dir.exists():
            console.print("[red]❌ .git/hooks directory not found. Is this a git repo?[/red]")
            return

        if self.is_installed:
            console.print("[yellow]⚠️  Pre-commit hook already exists. Overwriting...[/yellow]")

        self.hook_path.write_text(HOOK_SCRIPT)
        self.hook_path.chmod(self.hook_path.stat().st_mode | stat.S_IEXEC)
        console.print("[green]✅ Pre-commit hook installed.[/green]")
        console.print(f"[dim]Location: {self.hook_path}[/dim]")

    def uninstall(self) -> None:
        if not self.is_installed:
            console.print("[yellow]Hook is not installed.[/yellow]")
            return

        self.hook_path.unlink()
        console.print("[green]✅ Pre-commit hook removed.[/green]")

    def status(self) -> None:
        if self.is_installed:
            console.print("[green]✅ Pre-commit hook is active.[/green]")
        else:
            console.print("[red]❌ Pre-commit hook is not installed.[/red]")
            console.print("[dim]To install: git-regret protect install[/dim]")
