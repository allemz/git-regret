from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

from git_regret.models import Report

console = Console()


class Reporter:
    """Serializes reports to JSON or other output formats."""

    def to_json(self, report: Report, output_path: str | Path | None = None) -> str:
        data = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)

        if output_path:
            path = Path(output_path)
            path.write_text(data, encoding="utf-8")
            console.print(f"[green]✅ Report written to: {path}[/green]")

        return data

    def to_stdout_json(self, report: Report) -> None:
        import json
        console.print_json(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
