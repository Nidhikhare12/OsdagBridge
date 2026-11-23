"""Tests for the report charts (task items 4 and 5)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from osdagbridge.core.reports import charts
from osdagbridge.core.reports.charts import (
    MaterialQuantities,
    element_for_label,
    element_urs,
    material_quantities,
    parse_number,
    parse_ur,
)

PNG = b"\x89PNG\r\n\x1a\n"


def _is_png(path: str | None) -> bool:
    assert path is not None
    data = Path(path).read_bytes()
    return data.startswith(PNG) and len(data) > 3000


class TestParsing:
    @pytest.mark.parametrize("text,expected", [
        ("12.50", 12.5), (" 7 ", 7.0), ("1,234.5", 1234.5), (3, 3.0),
        (2.5, 2.5), ("-1.5", -1.5),
    ])
    def test_parse_number(self, text, expected) -> None:
        assert parse_number(text) == expected

    @pytest.mark.parametrize("bad", [
        "N.A.", "", None, True, "abc", "nan", "inf", float("nan"),
        float("inf"), [], {}])
    def test_parse_number_rejects(self, bad) -> None:
        assert parse_number(bad) is None

    @pytest.mark.parametrize("cell,expected", [
        ("0.85", 0.85), (r"\textcolor{red}{1.05}", 1.05), ("1", 1.0),
        ("---", None), ("", None), (None, None), ("n/a", None),
    ])
    def test_parse_ur(self, cell, expected) -> None:
        assert parse_ur(cell) == expected


class TestGrouping:
    @pytest.mark.parametrize("label,element", [
        ("Girder --- Moment", "Steel Plate Girders"),
        ("Transverse Shear (slab)", "Concrete Deck Slab"),
        ("Crack Width (slab)", "Concrete Deck Slab"),
        ("Deck --- Punching Shear", "Concrete Deck Slab"),
        ("Cross Bracing --- Tension", "Cross Bracing"),
        ("End Diaphragm --- Shear", "End Diaphragms"),
        ("Something else", None),
    ])
    def test_element_for_label(self, label, element) -> None:
        assert element_for_label(label) == element

    def test_governing_ur_is_the_maximum(self) -> None:
        result = element_urs([
            ("Girder --- Moment", "0.74"),
            ("Girder --- Shear", r"\textcolor{red}{1.03}"),
            ("Girder --- LTB (constr.)", "0.31"),
            ("Deck --- Flexure (sagging)", "0.66"),
            ("Cross Bracing --- Tension", "---"),
        ])
        assert result == {"Steel Plate Girders": 1.03,
                          "Concrete Deck Slab": 0.66,
                          "Cross Bracing": None, "End Diaphragms": None}

    def test_no_rows_gives_all_none(self) -> None:
        assert set(element_urs([]).values()) == {None}

    def test_unknown_labels_and_bad_cells_are_ignored(self) -> None:
        result = element_urs([("???", "0.9"), ("Girder --- X", "---")])
        assert set(result.values()) == {None}

    def test_order_is_the_task_order(self) -> None:
        assert list(element_urs([])) == [
            "Steel Plate Girders", "Concrete Deck Slab", "Cross Bracing",
            "End Diaphragms"]


class TestMaterialQuantities:
    BOM = {"steel_girders_wt_total": "42.50", "bracing_top_wt_total": "1.10",
           "bracing_bot_wt_total": "1.35", "bracing_diag_wt_total": "0.65",
           "concrete_deck_vol_total": "96.00", "rebar_deck_wt_total": "8.20"}

    def test_values(self) -> None:
        q = material_quantities(self.BOM)
        assert q.girders_t == 42.5
        assert q.bracing_t == pytest.approx(3.10)
        assert q.concrete_m3 == 96.0 and q.rebar_mt == 8.2

    def test_end_diaphragm_is_never_invented(self) -> None:
        assert material_quantities(self.BOM).end_diaphragm_t is None

    def test_combined_bracing_key_wins(self) -> None:
        bom = {**self.BOM, "steel_bracing_wt_total": "9.99"}
        assert material_quantities(bom).bracing_t == 9.99

    def test_partial_bracing_is_not_summed(self) -> None:
        bom = {**self.BOM, "bracing_diag_wt_total": "N.A."}
        assert material_quantities(bom).bracing_t is None

    def test_default_bom_is_all_none(self) -> None:
        q = material_quantities({k: "N.A." for k in self.BOM})
        assert q == MaterialQuantities(None, None, None, None, None)

    def test_missing_keys_and_negative_values(self) -> None:
        q = material_quantities({"steel_girders_wt_total": "-3"})
        assert q.girders_t is None and q.concrete_m3 is None


class TestRendering:
    def test_ur_chart_is_written(self, tmp_path: Path) -> None:
        path = charts.render_ur_chart(
            {"Steel Plate Girders": 0.74, "Concrete Deck Slab": 0.5,
             "Cross Bracing": 1.2, "End Diaphragms": None}, tmp_path)
        assert _is_png(path) and path.endswith("ur_summary.png")
        assert "\\" not in path

    def test_ur_chart_none_when_no_data(self, tmp_path: Path) -> None:
        assert charts.render_ur_chart(element_urs([]), tmp_path) is None
        assert list(tmp_path.iterdir()) == []

    @pytest.mark.parametrize("value", [0.0, 1.0, 1.003, 99.0, 1e6])
    def test_ur_chart_handles_boundaries_and_huge_values(
            self, tmp_path: Path, value: float) -> None:
        assert _is_png(charts.render_ur_chart(
            {"Steel Plate Girders": value}, tmp_path))

    def test_creates_missing_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b"
        assert _is_png(charts.render_ur_chart({"Cross Bracing": 0.4}, target))

    def test_steel_chart(self, tmp_path: Path) -> None:
        q = MaterialQuantities(42.5, 3.1, None, 96.0, 8.2)
        assert _is_png(charts.render_steel_chart(q, tmp_path))

    def test_steel_chart_none_when_nothing_available(
            self, tmp_path: Path) -> None:
        q = MaterialQuantities(None, None, None, 1.0, 1.0)
        assert charts.render_steel_chart(q, tmp_path) is None

    def test_zero_quantities_render(self, tmp_path: Path) -> None:
        q = MaterialQuantities(0.0, 0.0, None, 0.0, 0.0)
        assert _is_png(charts.render_steel_chart(q, tmp_path))
        assert _is_png(charts.render_concrete_rebar_chart(q, tmp_path))

    def test_concrete_chart_with_one_missing_panel(
            self, tmp_path: Path) -> None:
        q = MaterialQuantities(None, None, None, 96.0, None)
        assert _is_png(charts.render_concrete_rebar_chart(q, tmp_path))

    def test_concrete_chart_none_when_nothing_available(
            self, tmp_path: Path) -> None:
        q = MaterialQuantities(1.0, 1.0, None, None, None)
        assert charts.render_concrete_rebar_chart(q, tmp_path) is None

    def test_pyplot_is_never_imported(self) -> None:
        code = ("import sys; import osdagbridge.core.reports.charts; "
                "print('matplotlib.pyplot' in sys.modules)")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                             text=True, check=True).stdout.strip()
        assert out == "False"


class TestLatexHelpers:
    ROWS = [("Girder --- Moment", "0.74")]

    def test_skipped_without_chart_dir(self) -> None:
        assert charts.ur_summary_latex(self.ROWS, None) == ""
        assert charts.material_charts_latex({}, None) == ""

    def test_figure_is_embedded(self, tmp_path: Path) -> None:
        tex = charts.ur_summary_latex(self.ROWS, tmp_path)
        assert r"\includegraphics" in tex and "ur_summary.png" in tex
        assert "dashed line" in tex

    def test_no_data_gives_no_figure(self, tmp_path: Path) -> None:
        assert charts.ur_summary_latex([("Girder --- Moment", "---")],
                                       tmp_path) == ""
        assert charts.material_charts_latex({}, tmp_path) == ""

    def test_both_material_figures(self, tmp_path: Path) -> None:
        bom = TestMaterialQuantities.BOM
        tex = charts.material_charts_latex(bom, tmp_path)
        assert tex.count(r"\includegraphics") == 2

    def test_a_rendering_failure_never_aborts_the_report(
            self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(*_a: object, **_k: object) -> str:
            raise RuntimeError("renderer crashed")
        monkeypatch.setattr(charts, "render_ur_chart", boom)
        monkeypatch.setattr(charts, "render_steel_chart", boom)
        assert charts.ur_summary_latex(self.ROWS, tmp_path) == ""
        assert charts.material_charts_latex(
            TestMaterialQuantities.BOM, tmp_path) == ""


needs_latex = pytest.mark.skipif(
    shutil.which("pdflatex") is None, reason="pdflatex not installed")
needs_poppler = pytest.mark.skipif(
    any(shutil.which(tool) is None
        for tool in ("pdftotext", "pdfimages")),
    reason="poppler-utils (pdftotext, pdfimages) not installed")


def _compile(tex: str, folder: Path) -> tuple[int, Path]:
    (folder / "doc.tex").write_text(tex, encoding="utf-8")
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "doc.tex"],
                       cwd=folder, capture_output=True, check=False)
    log = (folder / "doc.log").read_text(errors="ignore")
    return sum(ln.startswith("!") for ln in log.splitlines()), folder / "doc.pdf"


@needs_latex
@needs_poppler
def test_chapter_7_compiles_with_both_charts(tmp_path: Path) -> None:
    from osdagbridge.core.reports.chap7 import ch7_quantities
    from osdagbridge.core.reports.latex_tables import normalize_longtables
    from osdagbridge.core.reports.report_generator import preamble
    bom = TestMaterialQuantities.BOM
    images = tmp_path / "images"
    tex = (preamble("T", "J", "d")
           + normalize_longtables(ch7_quantities(bom, chart_dir=str(images)))
           + "\n\\end{document}\n")
    errors, pdf = _compile(tex, tmp_path)
    assert errors == 0
    text = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout
    assert "Structural steel quantities by member group" in text
    assert "Concrete volume and reinforcement steel weight" in text
    listing = subprocess.run(["pdfimages", "-list", str(pdf)],
                             capture_output=True, text=True,
                             check=True).stdout.splitlines()
    assert len([ln for ln in listing[2:] if ln.strip()]) >= 2


def test_chapter_7_without_chart_dir_is_unchanged() -> None:
    from osdagbridge.core.reports.chap7 import ch7_quantities
    assert r"\includegraphics" not in ch7_quantities({})


@needs_latex
def test_section_5_5_chart_matches_table(tmp_path: Path) -> None:
    from osdagbridge.core.reports.chap5 import ch5_design_checks
    from osdagbridge.core.reports.latex_tables import normalize_longtables
    from osdagbridge.core.reports.report_generator import (
        ReportDataBridge,
        preamble,
    )
    output = {"design_results": {"per_girder": {"G1": {"checks": [
        {"check_id": 1, "dcr": 0.74, "demand": 1200.0, "capacity": 1620.0,
         "demand_unit": "kN-m", "capacity_unit": "kN-m"},
        {"check_id": 2, "dcr": 1.03, "demand": 640.0, "capacity": 621.0,
         "demand_unit": "kN", "capacity_unit": "kN"}], "per_lc": {}}}}}
    bridge = ReportDataBridge(output, {}, None)

    plain = ch5_design_checks({}, bridge)
    assert r"\includegraphics" not in plain

    with_chart = ch5_design_checks({}, bridge, chart_dir=str(tmp_path / "im"))
    assert "ur_summary.png" in with_chart
    # the chart reads the same cells the table prints
    assert r"\textcolor{red}{1.03}" in with_chart
    assert (tmp_path / "im" / "ur_summary.png").is_file()

    tex = (preamble("T", "J", "d") + normalize_longtables(with_chart)
           + "\n\\end{document}\n")
    errors, _ = _compile(tex, tmp_path)
    assert errors == 0
