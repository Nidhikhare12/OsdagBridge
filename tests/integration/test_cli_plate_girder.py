"""Integration test for OsdagBridge Headless Report CLI.

Verifies complete subprocess execution of `python -m osdagbridge.core.reports.cli`,
covering CLI argument handling, theme override, automated QA linting, and error handling.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.mark.latex
def test_cli_full_workflow_execution(tmp_path):
    """Verify headless CLI execution with custom theme and QA linter checks."""
    fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures" / "reports"
    fixture_path = fixtures_dir / "baseline_default.json"
    assert fixture_path.is_file(), f"Missing test fixture: {fixture_path}"

    stem = "dev_accessible"
    out_dir = str(tmp_path)

    # 1. Positive test: generate report with --theme accessible and --lint
    cmd = [
        sys.executable,
        "-m",
        "osdagbridge.core.reports.cli",
        "--fixture",
        str(fixture_path),
        "--out",
        out_dir,
        "--stem",
        stem,
        "--theme",
        "accessible",
        "--lint",
    ]

    env = os.environ.copy()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

    assert proc.returncode == 0, (
        f"CLI failed with exit code {proc.returncode}.\n"
        f"STDOUT:\n{proc.stdout}\n"
        f"STDERR:\n{proc.stderr}"
    )

    pdf_file = tmp_path / f"{stem}.pdf"
    tex_file = tmp_path / f"{stem}.tex"

    assert pdf_file.is_file(), f"CLI did not produce PDF output at {pdf_file}"
    assert tex_file.is_file(), f"CLI did not produce TeX output at {tex_file}"
    assert pdf_file.stat().st_size > 50 * 1024, "Generated PDF is smaller than 50 KB"

    # 2. Negative test: non-existent fixture must fail with non-zero exit code
    invalid_fixture = tmp_path / "non_existent_fixture.json"
    cmd_invalid = [
        sys.executable,
        "-m",
        "osdagbridge.core.reports.cli",
        "--fixture",
        str(invalid_fixture),
        "--out",
        out_dir,
        "--stem",
        "invalid_run",
    ]

    proc_invalid = subprocess.run(cmd_invalid, capture_output=True, text=True, env=env)
    assert proc_invalid.returncode != 0, "CLI should return non-zero exit code when given a missing fixture"
