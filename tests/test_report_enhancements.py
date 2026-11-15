"""Regression tests for the report-generator enhancement assignment."""
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.report_charts import build_chart_images, utilization_rows
from osdagbridge.core.reports.report_generator import preamble
from osdagbridge.core.reports.styles import repeating_longtable_header


def test_shared_theme_reserves_header_and_footer_space():
    latex = preamble("Demo", "JOB-1", "2026-11-15")
    assert "bottom=0.95in" in latex
    assert "headheight=16pt" in latex
    assert "reportPass" in latex


def test_longtable_header_is_repeated_on_later_pages():
    header = repeating_longtable_header(r"\textbf{A} & \textbf{B} \\")
    assert r"\endfirsthead" in header
    assert r"\endhead" in header
    assert header.count(r"\textbf{A}") == 2


def test_chapter_three_separates_vehicle_and_footway_loads():
    latex = ch3_loads({})
    assert "Vehicle Live Loads" in latex
    assert "Footway Live Load" in latex
    assert "Load Combinations" in latex and r"\endhead" in latex


def test_charts_are_pngs_from_actual_payload_values():
    images = build_chart_images(
        [{"name": "Plate girder", "utilization_ratio": 0.83}],
        {
            "steel_girders_wt_total": "20.0",
            "concrete_deck_vol_total": "35.0",
            "rebar_deck_wt_total": "3.5",
        },
    )
    assert set(images) == {"utilization_summary", "material_quantities"}
    assert all(image.startswith(b"\x89PNG\r\n\x1a\n") for image in images.values())


def test_utilization_chart_accepts_calculated_output_dictionary_values():
    assert utilization_rows({"girder_utilization": "0.76"}) == [("girder utilization", 0.76)]


def test_chapter_seven_repeats_header_and_embeds_quantity_chart():
    latex = ch7_quantities({}, {"material_quantities": "images/material_quantities.png"})
    assert r"\endfirsthead" in latex
    assert "material_quantities.png" in latex
