from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from git_regret.core import Scanner, Cleaner, HookManager
from git_regret.output import Formatter, Reporter

console = Console()


@click.group()
@click.version_option("0.1.0", prog_name="git-regret")
def cli() -> None:
    """🔍 git-regret — Find and remove secrets from your git history."""
    pass


# 
# TARAMA BÖLÜMÜ
#

@cli.command()
@click.option("--history",          is_flag=True, help="Also scan full git commit history.")
@click.option("--path",             default=".", show_default=True, help="Repository directory.")
@click.option("--json", "output_json", is_flag=True, help="Output results as JSON.")
@click.option("--output", "-o",     default=None, help="Write JSON report to file.")
@click.option("--fail-on-findings", is_flag=True, help="Exit with code 1 if findings exist (for CI).")
def scan(
    history: bool,
    path: str,
    output_json: bool,
    output: Optional[str],
    fail_on_findings: bool,
) -> None:
    """Scan a repository for secrets and sensitive data."""
    scanner = Scanner(repo_path=path)
    report  = scanner.scan(include_history=history)

    if output_json or output:
        import json
        reporter = Reporter()
        reporter.to_json(report, output_path=output)
        if output_json and not output:
            console.print_json(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        Formatter().print_report(report)

    if fail_on_findings and not report.is_clean:
        sys.exit(1)


# 
# TEMİZLEME
# 

@cli.command()
@click.option("--path",    default=".", show_default=True, help="Repository directory.")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without making changes.")
def clean(path: str, dry_run: bool) -> None:
    """Remove discovered secrets from git history."""
    scanner = Scanner(repo_path=path)

    console.print("[dim]Running scan first...[/dim]")
    report = scanner.scan(include_history=True)

    if report.is_clean:
        console.print("[green]✅ Clean — nothing to remove.[/green]")
        return

    Formatter().print_report(report)

    if not dry_run:
        click.confirm(
            f"\n{report.total} issue(s) found. Remove from history?",
            abort=True,
        )

    Cleaner(repo_path=path).clean(report, dry_run=dry_run)


# 
# KORUMA
# 

@cli.group()
def protect() -> None:
    """Manage pre-commit hooks."""
    pass


@protect.command("install")
@click.option("--path", default=".", show_default=True, help="Repository directory.")
def protect_install(path: str) -> None:
    """Install a pre-commit hook that scans automatically on every commit."""
    HookManager(repo_path=path).install()


@protect.command("uninstall")
@click.option("--path", default=".", show_default=True, help="Repository directory.")
def protect_uninstall(path: str) -> None:
    """Remove the pre-commit hook."""
    HookManager(repo_path=path).uninstall()


@protect.command("status")
@click.option("--path", default=".", show_default=True, help="Repository directory.")
def protect_status(path: str) -> None:
    """Show hook installation status."""
    HookManager(repo_path=path).status()


# 
# PATTERN LİSTESİ
# 

@cli.command()
@click.option("--tag", default=None, help="Filter by tag.")
def patterns(tag: Optional[str]) -> None:
    """List all loaded detection patterns."""
    from git_regret.patterns import registry
    from rich.table import Table
    from rich import box

    all_patterns = registry.by_tag(tag) if tag else registry.all()

    table = Table(box=box.SIMPLE, header_style="bold")
    table.add_column("ID",          width=35)
    table.add_column("Severity",    width=10)
    table.add_column("Description", width=40)
    table.add_column("Tags",        width=25)

    for p in sorted(all_patterns, key=lambda x: x.severity):
        color = p.severity.color
        table.add_row(
            p.id,
            f"[{color}]{p.severity.value}[/{color}]",
            p.description,
            ", ".join(p.tags),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(all_patterns)} patterns[/dim]")


def main() -> None:
    cli()
