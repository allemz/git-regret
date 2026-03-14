from __future__ import annotations

import pytest
from git_regret.core.scanner import Scanner
from git_regret.models.pattern import Severity


SAMPLE_CONTENT = """
import os

# AWS Key
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# OpenAI
OPENAI_API_KEY = "sk-" + "a" * 48

# Stripe
STRIPE_KEY = "sk_live_" + "a" * 24

# Clean value
normal_variable = "hello world"
"""


def test_scanner_finds_aws_key(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".git" / "hooks").mkdir()
    (repo / "config.py").write_text(SAMPLE_CONTENT)

    scanner = Scanner(repo_path=repo)
    # Sadece content taraması
    from git_regret.models import Report
    report = Report(scanned_path=str(repo), include_history=False)
    scanner._scan_content(SAMPLE_CONTENT, "config.py", report)

    ids = [f.pattern.id for f in report.findings]
    assert "aws_access_key_id" in ids


def test_scanner_finds_stripe_key(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    from git_regret.models import Report
    report = Report(scanned_path=str(repo), include_history=False)
    scanner = Scanner(repo_path=repo)
    scanner._scan_content(SAMPLE_CONTENT, "config.py", report)

    ids = [f.pattern.id for f in report.findings]
    assert "stripe_secret_key_live" in ids


def test_clean_content_has_no_findings(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    clean = "x = 1\nprint('hello')\n"
    from git_regret.models import Report
    report = Report(scanned_path=str(repo), include_history=False)
    scanner = Scanner(repo_path=repo)
    scanner._scan_content(clean, "main.py", report)

    assert report.is_clean


def test_severity_ordering():
    assert Severity.CRITICAL < Severity.HIGH
    assert Severity.HIGH < Severity.MEDIUM
    assert Severity.MEDIUM < Severity.LOW
