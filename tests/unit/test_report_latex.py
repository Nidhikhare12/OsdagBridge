"""Regression tests for the LaTeX emitted by the report generator."""

from pathlib import Path
import re
import subprocess

from osdagbridge.core.reports import report_generator
from osdagbridge.core.reports.report_generator import preamble
from osdagbridge.core.reports.report_validator import validate_latex_source


REPORTS_DIR = Path(__file__).parents[2] / "src" / "osdagbridge" / "core" / "reports"
CHAPTER_FILES = sorted(REPORTS_DIR.glob("chap*.py"))


def test_preamble_uses_centralized_style_settings_once():
    tex = preamble("Sample Project", "JOB-1", "2026-08-10")

    expected_tokens = (
        r"\usepackage[a4paper, margin=1in]{geometry}",
        r"\usepackage{xcolor}",
        r"\usepackage{array}",
        r"\usepackage{booktabs}",
        r"\usepackage{longtable}",
        r"\usepackage{fancyhdr}",
        r"\definecolor{osdagGreen}{HTML}{91B014}",
        r"\setlength{\tabcolsep}{6pt}",
        r"\renewcommand{\arraystretch}{1.12}",
    )

    for token in expected_tokens:
        assert tex.count(token) == 1, token


def test_every_longtable_continuation_has_a_repeated_header():
    """A continuation header must contain visible table-header LaTeX.

    ``longtable`` does not repeat the first-page header automatically.  An
    empty block between ``\\endfirsthead`` and ``\\endhead`` therefore makes
    later pages lose their column headings.
    """
    pattern = re.compile(r"\\endfirsthead(?P<header>.*?)\\endhead", re.DOTALL)

    for chapter in CHAPTER_FILES:
        source = chapter.read_text(encoding="utf-8")
        for match in pattern.finditer(source):
            repeated_header = match.group("header")
            assert r"\hline" in repeated_header, chapter.name
            assert any(marker in repeated_header for marker in (r"\textbf", r"\multicolumn", r"\multirow")), chapter.name


def test_no_longtable_continuation_header_is_empty():
    pattern = re.compile(r"\\endfirsthead\s*\\endhead")
    empty_headers = [
        chapter.name
        for chapter in CHAPTER_FILES
        if pattern.search(chapter.read_text(encoding="utf-8"))
    ]

    assert empty_headers == []


def test_every_longtable_has_a_continuation_header_and_caption():
    pattern = re.compile(r"\\begin\{longtable\}.*?\\end\{longtable\}", re.DOTALL)

    for chapter in CHAPTER_FILES:
        for table in pattern.findall(chapter.read_text(encoding="utf-8")):
            assert r"\caption" in table, chapter.name
            assert r"\endfirsthead" in table, chapter.name
            assert r"\endhead" in table, chapter.name


def test_preamble_has_no_duplicate_latex_packages():
    packages = re.findall(
        r"\\usepackage(?:\[[^]]*\])?\{([^}]+)\}",
        preamble("Sample Project", "JOB-1", "2026-08-10"),
    )
    flattened = [package.strip() for group in packages for package in group.split(",")]

    assert len(flattened) == len(set(flattened))


def test_global_latex_dependencies_are_centralized_in_styles():
    generator_source = Path(report_generator.__file__).read_text(encoding="utf-8")

    assert r"\usepackage" not in generator_source


def test_report_sources_define_the_required_sections():
    required_sections = {
        "chap1.py": r"\chapter{Project Information}",
        "chap2.py": r"\chapter{Input Parameters}",
        "chap3.py": r"\chapter{Loads and Load Combinations}",
        "chap4.py": r"\chapter{Analysis Results}",
        "chap5.py": r"\chapter{Design Checks}",
        "chap6.py": r"\chapter{Drawings and Visualizations}",
        "chap7.py": r"\chapter{Material Take-off \& Quantity Summary}",
        "chap8.py": r"\chapter{Standards \& Assumptions}",
        "chap9.py": r"\chapter*{References}",
    }

    for filename, section in required_sections.items():
        assert section in (REPORTS_DIR / filename).read_text(encoding="utf-8")


def test_latex_validator_reports_structural_regressions():
    source = r"""
\documentclass{report}
\usepackage{longtable}
\usepackage{longtable}
\begin{document}
\begin{longtable}{ll}
\caption{Broken table}\\
\endfirsthead
\endhead
\ref{missing-label}
\end{document}
"""

    result = validate_latex_source(source)

    assert not result.passed
    assert "Duplicate LaTeX package: longtable." in result.errors
    assert "Missing \\end{longtable}." in result.errors
    assert "Reference to missing label: missing-label." in result.errors
    assert "Longtable 1 has an empty continuation header." in result.errors


def test_latex_compilation_stops_after_the_first_failed_pass(monkeypatch, tmp_path):
    calls = []

    def failed_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(
            command, 1, stdout=b"LaTeX Error: broken table", stderr=b""
        )

    monkeypatch.setattr(report_generator.subprocess, "run", failed_run)

    result = report_generator._compile_latex("pdflatex", tmp_path, "report")

    assert not result.succeeded
    assert len(calls) == 1
    assert "pass 1" in result.diagnostics
    assert "LaTeX Error: broken table" in result.diagnostics


def test_latex_compilation_runs_two_passes_after_a_successful_first_pass(
    monkeypatch, tmp_path
):
    calls = []

    def successful_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(report_generator.subprocess, "run", successful_run)

    result = report_generator._compile_latex("pdflatex", tmp_path, "report")

    assert result.succeeded
    assert len(calls) == 2
    assert calls[0][0] == ["pdflatex", "-interaction=nonstopmode", "report.tex"]


def test_report_diagnostics_are_written_beside_the_tex_output(tmp_path):
    path = report_generator._write_report_diagnostics(
        tmp_path, "sample", "_latex_error.log", "LaTeX Error: broken table"
    )

    assert Path(path) == tmp_path / "sample_latex_error.log"
    assert Path(path).read_text(encoding="utf-8") == "LaTeX Error: broken table"


def test_generate_report_writes_tex_and_returns_pdf_after_successful_compilation(
    monkeypatch, tmp_path
):
    metadata = report_generator.ReportMetadata(
        project_name="Sample Project",
        project_location="Mumbai",
        designer="Designer",
        client="Client",
        company="Company",
        job_number="JOB-1",
        report_date="2026-08-12",
    )
    options = report_generator.ReportOptions(
        sections=[], include_figures=False, include_toc=False, include_pdf=True
    )
    payload = report_generator.ReportPayload(
        metadata=metadata,
        options=options,
        inputs={},
        analysis_summary={},
        design_checks=[],
        figures=report_generator.ReportFigures(),
    )
    request = report_generator.ReportRequest(
        metadata=metadata, options=options, output_dir=str(tmp_path), file_stem="sample"
    )

    monkeypatch.setattr(report_generator, "calculate_material_quantities", lambda *_: {})
    for renderer in (
        "title_page", "executive_summary", "ch1_project_info", "ch2_input_parameters",
        "ch3_loads", "ch4_analysis", "ch5_design_checks", "ch6_drawings",
        "ch7_quantities", "ch8_design_log", "references",
    ):
        monkeypatch.setattr(report_generator, renderer, lambda *_: "")

    def successful_compile(_compiler, working_dir, file_stem):
        (Path(working_dir) / f"{file_stem}.pdf").write_bytes(b"%PDF-1.4\n")
        return report_generator._LatexCompilation(succeeded=True)

    monkeypatch.setattr(report_generator, "_compile_latex", successful_compile)

    result = report_generator.generate_report(payload, request)

    assert result.error_message is None
    assert Path(result.tex_path).exists()
    assert Path(result.pdf_path).read_bytes().startswith(b"%PDF")
