"""Unit tests for live load data extraction (T-LL-1)."""

from pathlib import Path
import json
import pytest

from osdagbridge.core.reports.data.live_loads import collect_live_loads
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_BL_IRC_CLASS_A,
    KEY_FOOTPATH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
)


def test_t_ll_1_baseline_default_selection():
    """T-LL-1: Verify vehicles and footpath extraction from baseline fixture."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "reports" / "baseline_default.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    inp = data["input_dict"]

    ll = collect_live_loads(inp)
    assert len(ll.vehicles) == 8  # 8 vehicles ticked in baseline
    assert ll.footpath is None  # no_of_footpaths = 0 in baseline
    assert not ll.centrifugal_evaluated

    # Verify Class A on 24m span: 1 + 0.24 = 1.240
    class_a = next(v for v in ll.vehicles if "Class A" in v.name)
    assert class_a.impact_factor == 1.24
    assert class_a.total_load_kN == pytest.approx(543.474, rel=1e-3)


def test_t_ll_1_single_vehicle_selection():
    """T-LL-1: Verify selection when only one vehicle is ticked in input."""
    single_inp = {
        KEY_SPAN: 24.0,
        KEY_LL_IRC_CLASS_A: True,
        KEY_BL_IRC_CLASS_A: True,
        KEY_FOOTPATH: "None",
        KEY_TS_NO_OF_FOOTPATHS: 0,
    }
    ll = collect_live_loads(single_inp)
    assert len(ll.vehicles) == 1
    assert ll.vehicles[0].name == "Class A"
    assert ll.vehicles[0].braking_considered is True
    # The upstream helper raises UnboundLocalError for 1-2 lanes, so braking_value_kN is None
    assert ll.vehicles[0].braking_value_kN is None
    assert ll.footpath is None


def test_t_ll_1_footpath_present_when_configured():
    """T-LL-1: Verify footpath configuration when count > 0 and geometry != None."""
    sample_inp = {
        KEY_SPAN: 24.0,
        KEY_FOOTPATH: "Both Sides",
        KEY_TS_NO_OF_FOOTPATHS: 2,
        KEY_TS_FOOTPATH_WIDTH: 1.5,
        KEY_LL_FOOTPATH_PRESSURE_MODE: "As per IRC 6",
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
    }
    ll = collect_live_loads(sample_inp)
    assert len(ll.vehicles) == 2
    assert ll.footpath is not None
    assert ll.footpath.count == 2
    assert ll.footpath.width_m == 1.5
    assert ll.footpath.intensity_kN_m2 is not None
    assert ll.footpath.intensity_kN_m2 > 0.0
