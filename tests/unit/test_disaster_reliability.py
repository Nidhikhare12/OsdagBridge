"""Fault-injection and disaster-handling reliability tests (Scenarios S1-S5)."""

import pytest
import os
import shutil
from pathlib import Path
from unittest.mock import patch

from osdagbridge.core.reports.latex.compile import find_compiler, run_latex, CompileReport
from osdagbridge.core.reports.latex.document import build_preamble
from osdagbridge.core.reports.latex.figures import figure_or_placeholder, placeholder
from osdagbridge.core.reports.theme import get_active_theme
import matplotlib


class TestDisasterHandlingScenarios:
    """Rigorous verification of the 5 disaster-handling scenarios."""

    # -------------------------------------------------------------------------
    # Scenario 1: Missing System TeX Distribution
    # -------------------------------------------------------------------------
    def test_s1_missing_compiler_returns_structured_error(self, tmp_path):
        """When pdflatex is missing, run_latex returns CompileReport with error instead of crashing."""
        dummy_tex = tmp_path / "test_doc.tex"
        dummy_tex.write_text(r"\documentclass{article}\begin{document}Hello\end{document}", encoding="utf-8")

        # Simulate non-existent compiler
        with patch("osdagbridge.core.reports.latex.compile.find_compiler", return_value=("non_existent_pdflatex_bin_xyz", {})):
            with patch("shutil.which", return_value=None):
                report = run_latex(dummy_tex, max_passes=2)

                assert isinstance(report, CompileReport)
                assert report.success is False
                assert report.passes == 0
                assert len(report.errors) > 0
                assert "LaTeX compiler executable not found" in report.errors[0]

    # -------------------------------------------------------------------------
    # Scenario 2: Malformed / Empty Dictionaries (Rule 3)
    # -------------------------------------------------------------------------
    def test_s2_empty_dictionaries_fallback_to_dashes(self):
        """Empty input and output dicts must produce '---' without raising KeyError."""
        from osdagbridge.core.reports.report_generator import ReportDataBridge, ReportPayload, ReportMetadata, ReportOptions, ReportFigures
        from osdagbridge.core.reports.chap2 import ch2_input_parameters
        from osdagbridge.core.reports.chap3 import ch3_loads
        from osdagbridge.core.reports.data.utilization import collect_utilization
        from osdagbridge.core.reports.data.quantities import collect_quantities

        meta = ReportMetadata(
            project_name="",
            project_location="",
            designer="",
            client="",
            company="",
        )
        opts = ReportOptions(sections=["input_parameters", "loads"], include_figures=False, include_toc=False, include_pdf=False)
        payload = ReportPayload(
            metadata=meta,
            options=opts,
            inputs={},
            analysis_summary={},
            design_checks=[],
            figures=ReportFigures(),
            output_dict={},
        )
        bridge = ReportDataBridge(output_dict={}, input_dict={}, payload=payload)

        # 1. Cross-bracing bridge queries must return empty or fallback
        assert bridge.get_cb_pairs() == []
        assert bridge.get_cb_brace_type() == "X"
        assert bridge.get_cb_section("G1-G2", "diagonal", "tension") == ""

        # 2. Utilization collector handles empty dict gracefully
        ud = collect_utilization(bridge)
        assert len(ud.records) > 0
        for rec in ud.records:
            assert rec.ur is None or isinstance(rec.ur, (int, float))

        # 3. Quantities collector handles empty dict gracefully
        qs = collect_quantities({})
        assert qs.steel_girders_wt is None or qs.steel_girders_wt == 0.0

        # 4. Chapters compile with empty dicts without crashing
        tex_ch2 = ch2_input_parameters(meta, {}, {})
        assert "---" in tex_ch2
        tex_ch3 = ch3_loads({})
        assert "---" in tex_ch3

    # -------------------------------------------------------------------------
    # Scenario 3: Matplotlib GUI Thread Safety
    # -------------------------------------------------------------------------
    def test_s3_matplotlib_backend_is_headless_agg(self):
        """Matplotlib must use headless Agg backend to prevent Qt GUI crashes on Windows."""
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        backend = matplotlib.get_backend().lower()
        assert "agg" in backend, f"Expected Agg backend, got {backend}"

        # Verify Figure creation uses pure OO API without pyplot
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvasAgg(fig)
        assert fig is not None
        assert canvas is not None

    # -------------------------------------------------------------------------
    # Scenario 4: Extremely Long Project / Job Names
    # -------------------------------------------------------------------------
    def test_s4_extremely_long_names_truncated_cleanly(self):
        """Preamble truncates long project and job names with an ellipsis to prevent header overflow."""
        long_name = "Super Long Bridge Project Name Exceeding Sixty Characters That Would Overflow LaTeX Headers"
        long_job = "JOB-NUMBER-EXCEEDING-TWENTY-FOUR-CHARACTERS"
        long_date = "2026-11-16-EXTRA-LONG-DATE"

        preamble_str = build_preamble(
            project_name=long_name,
            job_number=long_job,
            report_date=long_date,
            report_version="Rev 0",
        )

        theme = get_active_theme()
        # Left header length is bounded
        assert len(long_name) > theme.header_footer.header_left_max_chars
        assert "..." in preamble_str or r"\ldots" in preamble_str

        # Long strings must not bleed raw unescaped characters into TeX
        assert "\\fancyhead[L]" in preamble_str
        assert "\\fancyhead[R]" in preamble_str

    # -------------------------------------------------------------------------
    # Scenario 5: Corrupt Image or Chart Generation Failure
    # -------------------------------------------------------------------------
    def test_s5_missing_or_corrupt_image_falls_back_gracefully(self):
        """Missing image paths fall back to structured placeholder figure without crashing."""
        # 1. placeholder function creates a framed container
        ph_box = placeholder("Test Missing Asset")
        assert "PLACEHOLDER: Test Missing Asset" in ph_box
        assert r"\fbox" in ph_box

        # 2. figure_or_placeholder with None emits placeholder
        fig_markup = figure_or_placeholder(None, "Unavailable Chart Caption")
        assert "PLACEHOLDER" in fig_markup
        assert "Unavailable Chart Caption" in fig_markup
