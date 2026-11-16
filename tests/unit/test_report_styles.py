"""Regression tests for the PDF report styling and layout fixes.

These tests protect the six report-generation improvements:

1. every ``longtable`` repeats its header row after a page break
2. table rows never sit in the page footer (no manual row skips)
3. live loads and footway loads are reported as separate tables with units
4. the utilisation-ratio summary has a chart with a capacity line at 1.0
5. chapter 7 has material-quantity charts
6. all styling lives in ``styles.py``

They are pure string/PNG checks -- no LaTeX installation is required.
"""

from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

from osdagbridge.core.reports import charts, styles
from osdagbridge.core.reports.report_generator import (
    ensure_repeating_headers,
    preamble,
)

REPORT_DIR = Path(charts.__file__).resolve().parent

LONGTABLE_BEGIN = r"\begin{longtable}"
LONGTABLE_END = r"\end{longtable}"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _longtables(tex: str):
    """Yield the body of every longtable in *tex* (without begin/end lines)."""
    for block in tex.split(LONGTABLE_BEGIN)[1:]:
        yield block.split(LONGTABLE_END)[0]


def _raw_table() -> str:
    """A table written the way the old chapter modules wrote them."""
    return "\n".join([
        LONGTABLE_BEGIN + r"{|L{5cm}|p{9cm}|}",
        r"\caption{\textbf{Typical Section Details}}",
        r"\hline",
        r"\textbf{parameter} & \textbf{value} \\",
        r"\hline",
        r"Width & 5.9 \\[6pt]",
        r"\hline",
        r"Girders & 3 \\[6pt]",
        r"\hline",
        LONGTABLE_END,
    ])


# ---------------------------------------------------------------------------
# 1 + 2: repeating headers and uniform row height
# ---------------------------------------------------------------------------

def test_styles_longtable_declares_all_four_page_sections():
    table = styles.longtable(
        colspec=r"{|L{5cm}|p{9cm}|}",
        headers=[r"\textbf{Parameter}", r"\textbf{Value}"],
        body=styles.rows([("Span", "20 m"), ("Width", "5.9 m")]),
        caption=r"\textbf{Geometry}",
        label="tab:geometry",
    )
    for marker in ("endfirsthead", "endhead", "endfoot", "endlastfoot"):
        assert "\\" + marker in table
    assert table.count(LONGTABLE_BEGIN) == 1
    assert table.count(LONGTABLE_END) == 1


def test_header_row_appears_in_first_head_and_repeating_head():
    table = styles.longtable(
        colspec=r"{|L{5cm}|p{9cm}|}",
        headers=[r"\textbf{Parameter}", r"\textbf{Value}"],
        body=styles.rows([("Span", "20 m")]),
        caption=r"\textbf{Geometry}",
    )
    head, rest = table.split(r"\endfirsthead", 1)
    repeating = rest.split(r"\endhead", 1)[0]
    for part in (head, repeating):
        assert r"\textbf{Parameter} & \textbf{Value}" in part


def test_raw_longtable_gains_repeating_header_and_footer():
    patched = ensure_repeating_headers(_raw_table())
    for marker in ("endfirsthead", "endhead", "endfoot", "endlastfoot"):
        assert patched.count("\\" + marker) == 1


def test_caption_row_is_terminated_before_first_rule():
    """Regression: an unterminated ``\\caption`` caused 'Misplaced \\noalign'."""
    patched = ensure_repeating_headers(_raw_table())
    lines = [ln.strip() for ln in patched.splitlines()]
    for i, line in enumerate(lines):
        if line.startswith(r"\caption"):
            assert line.endswith(r"\\"), line
            # the caption must be followed by a rule, not swallowed by it
            assert lines[i + 1] in (r"\hline", r"\label{Continued}")


def test_manual_row_skip_is_normalised():
    patched = ensure_repeating_headers(_raw_table())
    assert r"\\[6pt]" not in patched


def test_ensure_repeating_headers_is_idempotent():
    once = ensure_repeating_headers(_raw_table())
    twice = ensure_repeating_headers(once)
    assert once == twice
    assert twice.count(r"\endhead") == 1


def test_hand_written_header_gets_footer_only():
    table = "\n".join([
        LONGTABLE_BEGIN + r"{|L{5cm}|p{9cm}|}",
        r"\endfirsthead",
        r"\endhead",
        r"Span & 20 m \\",
        r"\end{longtable}",
    ])
    patched = ensure_repeating_headers(table)
    assert patched.count(r"\endhead") == 1
    assert patched.count(r"\endfirsthead") == 1
    assert patched.count(r"\endfoot") == 1
    assert patched.count(r"\endlastfoot") == 1


# ---------------------------------------------------------------------------
# 6: styles.py is the single source of truth
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["chap1.py", "chap2.py", "chap3.py", "chap4.py",
                                  "chap5.py", "chap6.py", "chap7.py", "chap8.py",
                                  "chap9.py", "executive_summary.py"])
def test_chapters_do_not_set_spacing_by_hand(name):
    path = REPORT_DIR / name
    if not path.exists():
        pytest.skip(f"{name} not present")
    source = path.read_text(encoding="utf-8")
    offenders = [line.strip() for line in source.splitlines()
                 if r"\setlength" in line and "styles." not in line]
    assert not offenders, f"{name} sets spacing directly: {offenders}"


@pytest.mark.parametrize("name", ["chap1.py", "chap2.py", "chap3.py", "chap4.py",
                                  "chap5.py", "chap6.py", "chap7.py", "chap8.py",
                                  "chap9.py", "executive_summary.py"])
def test_chapters_do_not_hardcode_hex_colours(name):
    path = REPORT_DIR / name
    if not path.exists():
        pytest.skip(f"{name} not present")
    source = path.read_text(encoding="utf-8")
    matches = re.findall(r"#[0-9A-Fa-f]{6}", source)
    assert not matches, f"{name} hardcodes colours: {matches}"


def test_tables_use_compact_padding_that_fits_the_text_block():
    """4pt column padding keeps wide tables inside the 1in margins."""
    assert styles.TABLE["tabcolsep"] == "4pt"
    tex = styles.longtable(
        colspec="|L{5.0cm}|p{10.5cm}|",
        headers=[r"\textbf{Parameter}", r"\textbf{Value}"],
        body="a & b \\\\",
        caption=r"\textbf{Example}",
    )
    assert r"\setlength{\tabcolsep}{4pt}" in tex


def test_solver_unicode_math_symbols_are_escaped():
    """Raw ``≤``/``≥`` from solver messages must not reach pdflatex."""
    from osdagbridge.core.reports.report_utils import _tex

    tex = _tex("Leg ≤ H_limit, UR ≥ 1.0, ±5%, x ≈ y")
    assert "≤" not in tex and "≥" not in tex and "≈" not in tex
    assert r"$\leq$" in tex and r"$\geq$" in tex and r"$\approx$" in tex
    # escaping still happened first: the underscore is protected
    assert r"\_" in tex


def test_preamble_uses_styles_module():
    tex = preamble("Bridge", "Job-1", "2026-01-01", "Rev 0")
    assert r"\raggedbottom" in tex
    assert f"headheight={styles.PAGE['headheight']}" in tex
    assert "footskip=" in tex and "includeheadfoot" in tex
    for role, name in styles._COLOR_NAMES.items():
        assert "\\definecolor{" + name + "}" in tex


# ---------------------------------------------------------------------------
# 3: live loads split from footway loads, both with units
# ---------------------------------------------------------------------------

def _ch3_tex(no_of_footpaths: int) -> str:
    from osdagbridge.core.reports.chap3 import ch3_loads
    from osdagbridge.core.utils.common import (
        KEY_LL_IRC_CLASS_A,
        KEY_TS_NO_OF_FOOTPATHS,
        KEY_WC_LD_LANE_TABLE_COUNT,
    )

    inputs = {
        KEY_LL_IRC_CLASS_A: True,
        KEY_TS_NO_OF_FOOTPATHS: no_of_footpaths,
        KEY_WC_LD_LANE_TABLE_COUNT: 2,
    }
    return ch3_loads(inputs)


def test_live_loads_and_footway_are_separate_tables():
    tex = _ch3_tex(2)
    assert "Live Loads --- Vehicles (LL)" in tex
    assert "Live Loads --- Footway (LL)" in tex
    # each table declares a Unit column
    assert tex.count(r"\textbf{Unit}") >= 2


def test_footway_table_reports_absence_when_no_footpath():
    tex = _ch3_tex(0)
    assert "Live Loads --- Footway (LL)" in tex
    assert "Not applicable" in tex


# ---------------------------------------------------------------------------
# 4 + 5: charts
# ---------------------------------------------------------------------------

def test_ur_chart_is_written(tmp_path):
    out = tmp_path / "ur.png"
    rows = [
        {"label": "Girder — Moment", "ur": 0.42},
        {"label": "Girder — Fatigue", "ur": 1.45},
    ]
    assert charts.ur_summary_png(rows, str(out)) == str(out)
    assert out.stat().st_size > 5000


def test_ur_chart_puts_ratio_on_y_axis_with_horizontal_limit(
        monkeypatch, tmp_path):
    import matplotlib.axes as mpl_axes

    seen = {}
    original_axhline = mpl_axes.Axes.axhline
    original_ylabel = mpl_axes.Axes.set_ylabel

    def spy_axhline(self, y, *args, **kwargs):
        seen["limit"] = y
        return original_axhline(self, y, *args, **kwargs)

    def spy_ylabel(self, label, *args, **kwargs):
        seen["ylabel"] = label
        return original_ylabel(self, label, *args, **kwargs)

    monkeypatch.setattr(mpl_axes.Axes, "axhline", spy_axhline)
    monkeypatch.setattr(mpl_axes.Axes, "set_ylabel", spy_ylabel)

    rows = [{"label": "Girder — Fatigue", "ur": 1.45},
            {"label": "Girder — Moment", "ur": 0.42}]
    assert charts.ur_summary_png(rows, str(tmp_path / "ur.png"))
    assert seen["limit"] == 1.0                       # horizontal capacity line
    assert "Utilization Ratio" in seen["ylabel"]      # UR is on the y axis


def test_ur_chart_skips_non_numeric_rows(tmp_path):
    out = tmp_path / "ur.png"
    rows = [{"label": "Deck", "ur": "N/A"}, {"label": "Girder", "ur": 0.5}]
    assert charts.ur_summary_png(rows, str(out)) == str(out)


def test_ur_chart_returns_none_without_data(tmp_path):
    out = tmp_path / "ur.png"
    assert charts.ur_summary_png([{"label": "Deck", "ur": "---"}], str(out)) is None
    assert not out.exists()


def test_material_charts_are_written(tmp_path):
    quantities = {
        "steel_girders_wt_total": "7.34",
        "bracing_top_wt_total": "0.04",
        "bracing_bot_wt_total": "0.04",
        "bracing_diag_wt_total": "0.10",
        "concrete_deck_vol_total": "29.50",
        "rebar_deck_wt_total": "3.54",
    }
    steel = tmp_path / "steel.png"
    concrete = tmp_path / "concrete.png"
    assert charts.material_steel_png(quantities, str(steel)) == str(steel)
    assert charts.material_concrete_rebar_png(quantities, str(concrete)) == str(concrete)
    assert steel.stat().st_size > 5000
    assert concrete.stat().st_size > 5000


def test_steel_chart_groups_girders_bracing_and_end_diaphragms():
    groups = dict(charts._STEEL_COMPONENTS)
    assert {"Girders", "Cross Bracing", "End Diaphragms"} <= set(groups)
    # The three bracing members are reported as one "Cross Bracing" bar.
    assert len(groups["Cross Bracing"]) == 3
    assert groups["End Diaphragms"] == ("end_diaphragm_wt_total",)


def test_chapter7_bom_lists_end_diaphragms():
    from osdagbridge.core.reports.chap7 import ch7_quantities

    tex = ch7_quantities({
        "end_diaphragm_qty": "12",
        "end_diaphragm_wt_total": "0.05",
    })
    assert "End Diaphragms" in tex
    assert "0.05" in tex


def test_chapter7_embeds_figures(tmp_path):
    from osdagbridge.core.reports.chap7 import ch7_quantities

    steel = tmp_path / "steel.png"
    concrete = tmp_path / "concrete.png"
    steel.write_bytes(b"\x89PNG\r\n\x1a\n")
    concrete.write_bytes(b"\x89PNG\r\n\x1a\n")

    tex = ch7_quantities({}, figures={"steel": str(steel), "concrete": str(concrete)})
    assert tex.count(r"\includegraphics") == 2
    assert r"\begin{longtable}" in tex


def test_chapter7_without_figures_has_no_includegraphics():
    from osdagbridge.core.reports.chap7 import ch7_quantities

    assert r"\includegraphics" not in ch7_quantities({})


# ---------------------------------------------------------------------------
# 4: the UR chart is driven by the §5.5 table rows
# ---------------------------------------------------------------------------

def test_ur_chart_receives_section_5_5_rows():
    from osdagbridge.core.reports.chap5 import ch5_design_checks
    from osdagbridge.core.reports.report_generator import ReportDataBridge
    from osdagbridge.core.utils.common import KEY_TS_NO_OF_GIRDERS

    inputs = {KEY_TS_NO_OF_GIRDERS: 2}
    bridge = ReportDataBridge({}, inputs,
                              types.SimpleNamespace(inputs=inputs, output_dict={}))
    captured = {}

    def _chart(rows):
        captured["rows"] = list(rows)
        return None

    ch5_design_checks({}, bridge, ur_chart=_chart)
    assert captured["rows"], "chart callback received no rows"
    assert all({"label", "ur"} <= set(row) for row in captured["rows"])


# ---------------------------------------------------------------------------
# 5: end-diaphragm steel reaches the BOM and the chart
# ---------------------------------------------------------------------------

def test_end_diaphragm_quantity_matches_chapter5_geometry():
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    from osdagbridge.core.utils.common import (
        KEY_SPAN, KEY_TS_DECK_THICKNESS, KEY_TS_GIRDER_SPACING,
        KEY_TS_NO_OF_GIRDERS, KEY_MP_ED_TYPE, KEY_TD_ED_PROP_A,
    )

    inputs = {
        KEY_SPAN: "20", KEY_TS_NO_OF_GIRDERS: "3", KEY_TS_DECK_THICKNESS: "250",
        "typical_section.overall_bridge_width": "5.9",
        KEY_TS_GIRDER_SPACING: "1.9667",
        "member_properties.girder_details.section_input.depth": "1120",
    }
    outputs = {}
    for pair in ("G1G2", "G2G3"):
        # The UI stores the diaphragm type per panel, with a member suffix.
        inputs[f"{KEY_MP_ED_TYPE}.{pair}.E1M1"] = "Cross Bracing"
        # 237 mm² angle, as printed in the Chapter 5 end-diaphragm table.
        outputs[f"{KEY_TD_ED_PROP_A}.{pair}"] = 2.37

    quantities = calculate_material_quantities(inputs, outputs)
    assert quantities["end_diaphragm_qty"] == "12"      # 2 panels x 3 members x 2 ends
    assert 0.04 <= float(quantities["end_diaphragm_wt_total"]) <= 0.06
    # Diagonal = hypot(girder spacing, 85 % of girder depth) = 2.18 m
    assert "2.18" in quantities["end_diaphragm_vol_formula"]


def test_end_diaphragm_quantity_falls_back_to_cross_bracing_data():
    """The end-diaphragm bar must exist even if no ED-specific key is reachable."""
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    from osdagbridge.core.utils.common import (
        KEY_SPAN, KEY_TS_DECK_THICKNESS, KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS,
    )

    inputs = {
        KEY_SPAN: "20", KEY_TS_NO_OF_GIRDERS: "3", KEY_TS_DECK_THICKNESS: "250",
        "typical_section.overall_bridge_width": "5.9",
        KEY_TS_GIRDER_SPACING: "1.9667",
    }
    outputs = {
        "transverse_member_design.cb.section_properties.bracing.G1G2.A": 2.37,
        "crossbracing_forces_dict": {
            "geometry": {"diagonal_length_m": 2.19, "cb_spacing_m": 5.0}},
    }
    quantities = calculate_material_quantities(inputs, outputs)
    assert quantities["end_diaphragm_qty"] == "12"
    assert float(quantities["end_diaphragm_wt_total"]) > 0.0
