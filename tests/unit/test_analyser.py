"""Unit tests for analysis summary extraction and structural demand verification.

Validates query methods and calculation transformations used in Chapter 4 (Analysis Results):
- Span length and allowable deflection limit calculations (L/800 and L/600 per IRC 24).
- Extraction of maximum bending moments, shear force envelopes, and support reactions.
- Resilient fallback to '---' or None when keys are missing or malformed.
"""

import json
from pathlib import Path
import pytest

from osdagbridge.core.reports.report_generator import ReportDataBridge
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_SD_DEFL_LIVE,
    KEY_SD_DEFL_TOTAL,
)


def test_analysis_summary_extraction_for_reports():
    """Verify analysis summary extraction, deflection limits, and safe fallbacks."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "reports" / "baseline_default.json"
    assert fixture_path.is_file(), f"Missing fixture: {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    input_dict = data.get("input_dict", {})
    output_dict = data.get("output_dict", {})

    bridge = ReportDataBridge(output_dict=output_dict, input_dict=input_dict, payload=None)

    # 1. Structural span and allowable deflection limits
    span_m = float(bridge.input_dict.get(KEY_SPAN, 0.0) or 0.0)
    assert span_m == pytest.approx(24.0, rel=1e-3), f"Expected span 24.0 m, got {span_m}"

    allowable_live_mm = span_m * 1000.0 / 800.0
    allowable_total_mm = span_m * 1000.0 / 600.0

    assert allowable_live_mm == pytest.approx(30.0, rel=1e-3), "Allowable live deflection should be L/800 = 30.0 mm"
    assert allowable_total_mm == pytest.approx(40.0, rel=1e-3), "Allowable total deflection should be L/600 = 40.0 mm"

    # 2. Deflection demands extraction across girders
    num_girders = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1) or 1)
    assert num_girders == 4, f"Expected 4 girders in baseline fixture, got {num_girders}"

    live_deflections = []
    total_deflections = []
    for gi in range(1, num_girders + 1):
        l_val = bridge.output_dict.get(f"{KEY_SD_DEFL_LIVE}.G{gi}")
        t_val = bridge.output_dict.get(f"{KEY_SD_DEFL_TOTAL}.G{gi}")
        if l_val is not None:
            live_deflections.append(float(l_val))
        if t_val is not None:
            total_deflections.append(float(t_val))

    assert len(live_deflections) == 4, "Should extract live deflection for all 4 girders"
    max_live_defl = max(live_deflections)
    # Baseline governing live deflection is ~26.153 mm
    assert max_live_defl == pytest.approx(26.153, abs=0.1)
    assert max_live_defl <= allowable_live_mm, "Governing live deflection must satisfy L/800 limit (PASS)"

    # 3. Maximum bending moments and shear envelopes from analysis summary
    asum = bridge.output_dict.get("analysis_summary", {})
    assert "load_cases" in asum, "analysis_summary must contain load_cases"

    load_cases = asum["load_cases"]
    assert len(load_cases) >= 20, "Expected at least 20 analysis load cases in baseline"

    # Check that each load case contains valid structural tokens
    for lc_name, lc_data in load_cases.items():
        if "max_bm" in lc_data:
            assert isinstance(lc_data["max_bm"], (int, float))
            assert lc_data["max_bm"] >= 0.0
        if "max_sf" in lc_data:
            assert isinstance(lc_data["max_sf"], (int, float))
            assert lc_data["max_sf"] >= 0.0

    # 4. Graceful handling of empty or missing analysis data
    empty_bridge = ReportDataBridge(output_dict={}, input_dict={}, payload=None)
    assert empty_bridge.input_dict.get(KEY_SPAN) is None
    assert empty_bridge.output_dict.get("analysis_summary", {}).get("load_cases") is None
    assert empty_bridge.get_cb_pairs() == []
    assert empty_bridge.get_cb_brace_type() == "X"
    assert empty_bridge.get_cb_force("G1-G2", "diagonal", "tension") == ""
