from __future__ import annotations

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from git_regret.models import Report
from git_regret.models.pattern import Severity

console = Console()


class Formatter:
    """Formats scan results for terminal output using Rich."""

    def print_report(self, report: Report) -> None:
        self._print_header(report)

        if report.is_clean:
            self._print_clean()
            return

        self._print_findings_table(report)
        self._print_summary(report)
        self._print_footer()

    def _print_header(self, report: Report) -> None:
        console.print()
        console.print(Panel.fit(
            "[bold red]🔍 git-regret[/bold red]  [dim]Secret Scanner[/dim]",
            border_style="dim",
        ))
        console.print(f"[dim]Repo:[/dim] {report.scanned_path}")
        if report.include_history:
            console.print(f"[dim]Git history:[/dim] {report.scanned_commits} commits scanned")
        console.print(f"[dim]Files:[/dim] {report.scanned_files} files scanned")
        console.print()

    def _print_clean(self) -> None:
        console.print(Panel(
            "[bold green]✅  Clean! No secrets found.[/bold green]",
            border_style="green",
        ))

    def _print_findings_table(self, report: Report) -> None:
        console.print(f"[bold red]⚠️  {report.total} issue(s) found![/bold red]\n")

        table = Table(
            box=box.ROUNDED,
            show_lines=True,
            border_style="dim",
            header_style="bold",
        )
        table.add_column("Severity",    width=10)
        table.add_column("Type",        width=28)
        table.add_column("File",        width=32)
        table.add_column("Line",        width=6, justify="right")
        table.add_column("Commit",      width=10)
        table.add_column("Masked",      width=20)

        for severity, findings in report.iter_by_severity():
            color = severity.color
            for f in findings:
                table.add_row(
                    f"[{color}]{severity.value.upper()}[/{color}]",
                    f.description,
                    f.file_path,
                    str(f.line_number) if f.line_number else "-",
                    f.commit_hash or "[dim]working dir[/dim]",
                    f"[dim]{f.masked_match}[/dim]",
                )

        console.print(table)

    def _print_summary(self, report: Report) -> None:
        console.print()
        summary = report.summary()
        parts = []
        for severity in Severity:
            count = summary.get(severity.value, 0)
            if count:
                color = severity.color
                parts.append(f"[{color}]{severity.value}: {count}[/{color}]")

        console.print("  ".join(parts))
        console.print(f"[dim]Duration: {report.duration_seconds:.2f}s[/dim]")

    def _print_footer(self) -> None:
        console.print()
        console.print("[dim]To clean:[/dim] [bold]git-regret clean[/bold]")
        console.print("[dim]To protect:[/dim] [bold]git-regret protect install[/bold]")
        console.print()
