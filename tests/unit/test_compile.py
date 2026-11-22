"""Unit tests for LaTeX compilation engine and log diagnostics (T-COMPILE-1)."""

from pathlib import Path
import pytest

from osdagbridge.core.reports.latex.compile import (
    find_compiler,
    parse_log,
    run_latex,
    CompileReport,
)


SAMPLE_FAILING_LOG = """
This is pdfTeX, Version 3.141592653-2.6-1.40.24 (TeX Live 2022) (preloaded format=pdflatex 2022.5.18)
entering extended mode
(./broken.tex
LaTeX2e <2022-06-01> patch level 5
! Undefined control sequence.
l.42 \\invalidcommandhere
                        {arg}
The control sequence at the end of the top line
of your error message was never \\def'ed.
! LaTeX Error: File `nonexistent_pkg.sty' not found.
Type X to quit or <RETURN> to proceed.
Package fancyhdr Warning: \\headheight is too small (12.0pt):
Overfull \\vbox (14.2pt too high) has occurred while \\output is active
)
"""


def test_t_compile_1_parse_log_extracts_errors_and_warnings():
    """T-COMPILE-1: Verify that parse_log accurately extracts errors, warnings, and missing packages."""
    report = parse_log(SAMPLE_FAILING_LOG)
    assert not report.success
    assert len(report.errors) >= 1
    assert any("Undefined control sequence" in err for err in report.errors)
    assert any("nonexistent_pkg.sty" in pkg for pkg in report.missing_packages)
    assert any("headheight is too small" in w for w in report.warnings)
    assert any("Overfull \\vbox" in w for w in report.warnings)


@pytest.mark.latex
def test_t_compile_1_deliberately_broken_tex(tmp_path):
    """T-COMPILE-1: Verify that a deliberately broken .tex file returns success=False and saved log."""
    broken_tex = tmp_path / "broken_test.tex"
    broken_tex.write_text(
        r"""\documentclass{article}
\begin{document}
\undefinedcommandthatcancausefatalerror
\end{document}
""",
        encoding="utf-8",
    )

    report = run_latex(broken_tex, max_passes=2)
    assert not report.success
    assert len(report.errors) > 0
    assert any("Undefined control sequence" in e for e in report.errors)
    assert report.log_path and Path(report.log_path).is_file()
