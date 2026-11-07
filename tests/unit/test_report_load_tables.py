import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.utils.common import (
    KEY_FOOTPATH, KEY_LL_FOOTPATH_PRESSURE_MODE, KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_CLASS_A, KEY_LL_IRC_70R_TRACKED, KEY_LL_IRC_AA_TRACKED, KEY_SPAN,
)
from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017


def test_selected_vehicles_and_separate_footpath():
    tex = ch3_loads({KEY_LL_IRC_CLASS_A: True, KEY_LL_IRC_70R_TRACKED: True,
                     KEY_FOOTPATH: "Single Side", KEY_LL_FOOTPATH_PRESSURE_MODE: "User-defined",
                     KEY_LL_FOOTPATH_PRESSURE_VALUE: 0.000004, KEY_LL_IRC_AA_TRACKED: "False",
                     KEY_SPAN: 30})
    assert "Class A, Class 70R (Tracked)" in tex
    vehicle, footpath = tex.split(r"\caption{\textbf{Footpath Live Load}}\\", 1)
    assert "Footpath pressure" not in vehicle
    assert "4e-06 kN/mm2 (custom input)" in footpath
    assert "Class AA (Tracked)" not in vehicle
    assert r"Class A:\allowbreak{} 1.207" in vehicle
    assert r"Class AA/70R:\allowbreak{} 1.100" in vehicle


def test_automatic_and_disabled_footpath():
    config = {KEY_FOOTPATH: "Both Sides", KEY_LL_FOOTPATH_PRESSURE_MODE: "Automatic"}
    assert f"{IRC6_2017.cl_206_1_footway_load():.3f} kN/m2" in ch3_loads(config)
    config[KEY_FOOTPATH] = "None"
    assert "Not applicable (no footpath)" in ch3_loads(config)


def test_missing_loads_are_not_fabricated():
    tex = ch3_loads({})
    assert "Vehicles Considered} & None" in tex
    assert "Not specified" in tex
    assert "Centrifugal Force} & Not available" in tex
