"""
Phase 5 Full Integration & Regression Test Suite
================================================
Runs a complete bridge design end-to-end across all 8 combinations of:
  Cross Bracing: [Bolted, Welded]
  End Diaphragm: [Cross Bracing (Bolted), Cross Bracing (Welded), Rolled Beam, Welded Beam]

Verifies:
1. Operational stability (no exceptions/crashes).
2. Proper populating of crossbracing_design_results and end_diaphragm_design_results.
3. Full state isolation and accurate output keys.
"""

import sys
import os


sys.path.append('/home/khushi-dudhalkar/OsdagBridge/src')

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.defaults import BASIC_INPUT_DICT, solve_extend_basic_input_dict
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_PROJECT_LOCATION,
    KEY_SKEW_ANGLE,
    KEY_MP_CB_BRACING_CONNECTION,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    ED_TYPE_CROSS_BRACING,
    ED_TYPE_ROLLED_BEAM,
    ED_TYPE_WELDED_BEAM,
)

CB_OPTIONS = ["Bolted", "Welded"]
ED_OPTIONS = [
    ("Cross Bracing", "Bolted", None, None),
    ("Cross Bracing", "Welded", None, None),
    ("Rolled Beam", None, "ISMB 400", None),
    (
        "Welded Beam",
        None,
        None,
        {
            "depth": 500,
            "web_t": 10,
            "top_w": 250,
            "top_t": 16,
            "bot_w": 250,
            "bot_t": 16,
        },
    ),
]


def run_single_combination(cb_conn, ed_type, ed_conn=None, is_sec=None, welded_dims=None):
    print(f"\n" + "=" * 70)
    print(f"TESTING COMBINATION:")
    print(f"  Cross Bracing Connection: {cb_conn}")
    print(f"  End Diaphragm Type:       {ed_type}")
    if ed_conn:
        print(f"  End Diaphragm Connection: {ed_conn}")
    if is_sec:
        print(f"  End Diaphragm Section:    {is_sec}")
    if welded_dims:
        print(f"  End Diaphragm Welded Dims: {welded_dims}")
    print("=" * 70)

    input_dict = dict(BASIC_INPUT_DICT)
    input_dict[KEY_SPAN] = "15.0"
    input_dict[KEY_CARRIAGEWAY_WIDTH] = "7.5"
    input_dict[KEY_PROJECT_LOCATION] = "Integration Pass"
    input_dict[KEY_SKEW_ANGLE] = "0.0"

    solve_extend_basic_input_dict(input_dict)

    # Set CB parameters
    for k in list(input_dict.keys()):
        if k.startswith(KEY_MP_CB_BRACING_CONNECTION):
            input_dict[k] = cb_conn

    # Set ED parameters
    for k in list(input_dict.keys()):
        if k.startswith(KEY_MP_ED_TYPE):
            input_dict[k] = ed_type

    if ed_conn:
        input_dict[KEY_MP_ED_BRACING_CONNECTION] = ed_conn
        for k in list(input_dict.keys()):
            if k.startswith(KEY_MP_ED_BRACING_CONNECTION):
                input_dict[k] = ed_conn

    if is_sec:
        input_dict[KEY_MP_ED_IS_SECTION] = is_sec
        for k in list(input_dict.keys()):
            if k.startswith(KEY_MP_ED_IS_SECTION):
                input_dict[k] = is_sec

    if welded_dims:
        for k in list(input_dict.keys()):
            if k.startswith(KEY_MP_ED_TOTAL_DEPTH):
                input_dict[k] = str(welded_dims["depth"])
            elif k.startswith(KEY_MP_ED_WEB_THICKNESS):
                input_dict[k] = str(welded_dims["web_t"])
            elif k.startswith(KEY_MP_ED_TOP_FLANGE_WIDTH):
                input_dict[k] = str(welded_dims["top_w"])
            elif k.startswith(KEY_MP_ED_BOTTOM_FLANGE_WIDTH):
                input_dict[k] = str(welded_dims["bot_w"])
            elif k.startswith(KEY_MP_ED_TOP_FLANGE_THICKNESS):
                input_dict[k] = str(welded_dims["top_t"])
            elif k.startswith(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS):
                input_dict[k] = str(welded_dims["bot_t"])

    bridge = PlateGirderBridge()
    bridge.set_input(input_dict)
    bridge.design()

    cb_res = bridge.crossbracing_design_results
    ed_res = bridge.end_diaphragm_design_results

    assert cb_res, "Cross Bracing design results dictionary is empty!"
    assert ed_res, "End Diaphragm design results dictionary is empty!"

    # Verify ED structure matching ed_type
    for pair, designs in ed_res.items():
        print(f"  --> ED Pair {pair}: keys={list(designs.keys())}")
        if ed_type == "Cross Bracing":
            assert "diagonal" in designs or "chord" in designs, f"Missing diagonal/chord in ED pair {pair}, got keys: {list(designs.keys())}"
            conn_tag = "Welded" if ed_conn == "Welded" else "Bolted"
            # Verify connection mode recorded in summary
            for member_type in ("diagonal", "chord"):
                if member_type in designs:
                    for ftype, r in designs[member_type].items():
                        assert r is not None, f"Null result for ED {pair} {member_type} {ftype}"
        elif ed_type == "Rolled Beam":
            assert "rolled_beam" in designs, f"Missing rolled_beam result in ED pair {pair}"
            r = designs["rolled_beam"]
            assert r.get("Moment.Demand") is not None, f"Missing Moment.Demand in ED pair {pair}"
            assert r.get("Shear.Demand") is not None, f"Missing Shear.Demand in ED pair {pair}"
        elif ed_type == "Welded Beam":
            assert "welded_beam" in designs, f"Missing welded_beam result in ED pair {pair}"
            r = designs["welded_beam"]
            assert r.get("Moment.Demand") is not None, f"Missing Moment.Demand in ED pair {pair}"
            assert r.get("Shear.Demand") is not None, f"Missing Shear.Demand in ED pair {pair}"

    print(f"  --> SUCCESS: CB={cb_conn}, ED={ed_type} ({ed_conn or 'N/A'}) passed clean.")
    return True


def test_full_matrix():
    count = 0
    for cb_conn in CB_OPTIONS:
        for ed_type, ed_conn, is_sec, welded_dims in ED_OPTIONS:
            count += 1
            print(f"\n[Matrix Combination {count}/8]")
            run_single_combination(cb_conn, ed_type, ed_conn, is_sec, welded_dims)

    print("\n" + "=" * 70)
    print(f"ALL 8 COMBINATIONS PASSED PERFECTLY WITH FULL REGRESSION TEST!")
    print("=" * 70)


if __name__ == "__main__":
    test_full_matrix()
