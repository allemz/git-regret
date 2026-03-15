from __future__ import annotations

import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

import questionary
from rich.console import Console
from rich.align import Align
from rich import box
from rich.table import Table

from git_regret.core import Scanner, Cleaner, HookManager
from git_regret.output import Formatter, Reporter

console = Console()

BANNER = """[bold red] ██████╗ ██╗████████╗      ██████╗ ███████╗ ██████╗ ██████╗ ███████╗████████╗
██╔════╝ ██║╚══██╔══╝      ██╔══██╗██╔════╝██╔════╝ ██╔══██╗██╔════╝╚══██╔══╝
██║  ███╗██║   ██║   █████╗██████╔╝█████╗  ██║  ███╗██████╔╝█████╗     ██║   
██║   ██║██║   ██║   ╚════╝██╔══██╗██╔══╝  ██║   ██║██╔══██╗██╔══╝     ██║   
╚██████╔╝██║   ██║         ██║  ██║███████╗╚██████╔╝██║  ██║███████╗   ██║   
 ╚═════╝ ╚═╝   ╚═╝         ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝   ╚═╝[/bold red]
[dim]                     Secret Scanner for Git Repositories[/dim]"""

STYLE = questionary.Style([
    ("qmark",       "fg:#ff0000 bold"),
    ("question",    "bold"),
    ("answer",      "fg:#ff6c6b bold"),
    ("pointer",     "fg:#ff0000 bold"),
    ("highlighted", "fg:#ff6c6b bold"),
    ("selected",    "fg:#cc5454"),
    ("separator",   "fg:#6c6c6c"),
    ("instruction", "fg:#6c6c6c"),
])


def header():
    console.clear()
    console.print(BANNER)
    console.print(Align.center("[dim]v0.1.0  •  github.com/allemz/git-regret[/dim]\n"))


def pause():
    input("\nPress Enter to continue...")


def clone_repo(url):
    tmp = Path(tempfile.mkdtemp(prefix="git-regret-"))
    console.print(f"\n[dim]Cloning: {url}[/dim]")
    result = subprocess.run(
        ["git", "clone", url, str(tmp)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]Clone failed:\n{result.stderr}[/red]")
        shutil.rmtree(tmp, ignore_errors=True)
        return None
    console.print("[green]Clone complete.[/green]")
    return tmp


def main_menu():
    header()
    action = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("  Scan a Repository",  value="scan"),
            questionary.Choice("  Pattern List",        value="patterns"),
            questionary.Choice("  Hook Management",     value="hooks"),
            questionary.Choice("  Exit",                value="exit"),
        ],
        style=STYLE,
    ).ask()

    if action is None or action == "exit":
        header()
        console.print(Align.center("\n[dim]Goodbye 👋[/dim]\n"))
        sys.exit(0)
    elif action == "scan":
        scan_menu()
    elif action == "patterns":
        patterns_menu()
    elif action == "hooks":
        hooks_menu()


def scan_menu():
    header()
    choice = questionary.select(
        "What do you want to scan?",
        choices=[
            questionary.Choice("  Current directory",   value="local"),
            questionary.Choice("  GitHub / Git URL",    value="url"),
            questionary.Choice("  Different directory", value="path"),
            questionary.Choice("  Back",                value="back"),
        ],
        style=STYLE,
    ).ask()

    if choice is None or choice == "back":
        main_menu()
        return

    is_temp = False
    repo_path = Path(".").resolve()

    if choice == "local":
        repo_path = Path(".").resolve()

    elif choice == "url":
        header()
        url = questionary.text(
            "Enter Git URL  (e.g. https://github.com/user/repo.git)",
            style=STYLE,
        ).ask()
        if not url or not url.strip():
            console.print("[red]URL cannot be empty.[/red]")
            pause()
            scan_menu()
            return
        header()
        tmp = clone_repo(url.strip())
        if tmp is None:
            pause()
            scan_menu()
            return
        repo_path = tmp
        is_temp = True

    elif choice == "path":
        header()
        path_str = questionary.path("Directory path:", style=STYLE).ask()
        repo_path = Path(path_str).resolve()

    header()
    # URL taramaları için geçmişi her zaman etkinleştir
    force_history = is_temp
    opts_raw = questionary.checkbox(
        "Scan options:",
        choices=[
            questionary.Choice(
                "  Include full git history" + (" [auto-enabled for URL scans]" if force_history else ""),
                value="history",
                checked=force_history,
            ),
            questionary.Choice("  Save JSON report", value="json", checked=False),
        ],
        style=STYLE,
    ).ask()

    opts = {
        "history": force_history or "history" in (opts_raw or []),
        "json":    "json" in (opts_raw or []),
    }

    header()
    report = None
    try:
        scanner = Scanner(repo_path=repo_path)
        report  = scanner.scan(include_history=opts["history"])
    finally:
        if is_temp:
            shutil.rmtree(repo_path, ignore_errors=True)

    Formatter().print_report(report)

    if opts["json"] and not report.is_clean:
        Reporter().to_json(report, output_path=Path(".") / "git-regret-report.json")

    if report.is_clean:
        pause()
        main_menu()
        return

    action = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice("  Clean findings",         value="clean"),
            questionary.Choice("  Install pre-commit hook", value="hook"),
            questionary.Choice("  Back to main menu",      value="back"),
        ],
        style=STYLE,
    ).ask()

    if action == "clean":
        header()
        dry = questionary.confirm(
            "Run as dry-run first? (shows what would be removed without changing anything)",
            default=True,
            style=STYLE,
        ).ask()
        console.print()
        Cleaner(repo_path=repo_path).clean(report, dry_run=dry)
        pause()
    elif action == "hook":
        header()
        HookManager(repo_path=repo_path).install()
        pause()

    main_menu()


def patterns_menu():
    header()
    from git_regret.patterns import registry

    tag = questionary.select(
        "Filter by category:",
        choices=[
            questionary.Choice("  All",            value=None),
            questionary.Choice("  Cloud",          value="cloud"),
            questionary.Choice("  AI Services",    value="ai"),
            questionary.Choice("  Payment",        value="payment"),
            questionary.Choice("  Social Media",   value="social"),
            questionary.Choice("  Database",       value="database"),
            questionary.Choice("  Crypto / Keys",  value="crypto"),
            questionary.Choice("  Email / SMS",    value="email"),
            questionary.Choice("  PII",            value="pii"),
            questionary.Choice("  Back",           value="back"),
        ],
        style=STYLE,
    ).ask()

    if tag == "back":
        main_menu()
        return

    header()
    patterns = registry.by_tag(tag) if tag else registry.all()
    patterns = sorted(patterns, key=lambda p: p.severity)

    table = Table(box=box.ROUNDED, border_style="dim", show_lines=True)
    table.add_column("ID",          width=32, style="dim")
    table.add_column("Severity",    width=10)
    table.add_column("Description", width=38)
    table.add_column("Tags",        width=22)

    for p in patterns:
        color = p.severity.color
        table.add_row(
            p.id,
            f"[{color}]{p.severity.value.upper()}[/{color}]",
            p.description,
            ", ".join(p.tags),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(patterns)} patterns[/dim]\n")
    pause()
    main_menu()


def hooks_menu():
    header()
    manager = HookManager()

    action = questionary.select(
        "Hook management:",
        choices=[
            questionary.Choice("  Install hook",   value="install"),
            questionary.Choice("  Remove hook",    value="uninstall"),
            questionary.Choice("  Hook status",    value="status"),
            questionary.Choice("  Back",           value="back"),
        ],
        style=STYLE,
    ).ask()

    if action is None or action == "back":
        main_menu()
        return

    header()
    if action == "install":
        manager.install()
    elif action == "uninstall":
        manager.uninstall()
    elif action == "status":
        manager.status()

    pause()
    main_menu()


def run():
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Cancelled.[/dim]\n")
        sys.exit(0)
