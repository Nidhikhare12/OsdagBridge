"""Regression checks for the OsdagBridge report-generation enhancements.

These tests intentionally use empty/missing data only; they do not fabricate
engineering inputs or claim that a bridge design has been analysed.
"""
import math

from osdagbridge.core.reports.styles import format_longtable
from osdagbridge.core.reports.charts import (
    _draw_ur_bar_chart,
    generate_quantity_charts,
    generate_ur_charts,
)
from osdagbridge.core.reports.chap8 import ch8_design_log


def test_format_longtable_repeats_header_and_continuation_footer():
    result = format_longtable(
        col_spec="|c|c|",
        caption="Regression table",
        header_rows=r"\textbf{A} & \textbf{B}",
        body_rows="1 & 2 \\",
        ncols=2,
    )
    assert r"\endfirsthead" in result
    assert r"\endhead" in result
    assert r"\endfoot" in result
    assert r"\endlastfoot" in result


def test_empty_engineering_data_does_not_create_charts(tmp_path):
    assert generate_ur_charts({}, {}, None, str(tmp_path)) == {}
    assert generate_quantity_charts({}, str(tmp_path)) == {}
    assert list(tmp_path.iterdir()) == []


def test_invalid_utilization_does_not_create_chart(tmp_path):
    assert _draw_ur_bar_chart(
        [("invalid", math.nan)], "Invalid", str(tmp_path / "invalid.png")
    ) is None
    assert not (tmp_path / "invalid.png").exists()


def test_chapter_eight_includes_supplied_design_log():
    tex = ch8_design_log(["INFO: Analysis completed"], {})
    assert r"\section{Design Log}" in tex
    assert "Analysis completed" in tex
