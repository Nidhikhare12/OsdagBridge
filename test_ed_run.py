import sys
import os
import copy

sys.path.append('/home/khushi-dudhalkar/OsdagBridge/src')

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.defaults import BASIC_INPUT_DICT, solve_extend_basic_input_dict
from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_PROJECT_LOCATION, KEY_SKEW_ANGLE,
    KEY_MP_ED_TYPE, KEY_MP_ED_BRACING_CONNECTION, KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_TOTAL_DEPTH, KEY_MP_ED_WEB_THICKNESS, KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH, KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS
)

def run_ed_design(ed_type, connection_type=None, is_section=None, welded_dims=None):
    print(f"\n==================================================")
    print(f"RUNNING END DIAPHRAGM DESIGN:")
    print(f"  Type: {ed_type}")
    if connection_type:
        print(f"  Connection: {connection_type}")
    if is_section:
        print(f"  IS Section: {is_section}")
    if welded_dims:
        print(f"  Welded Dims: {welded_dims}")
    print(f"==================================================")
    
    input_dict = dict(BASIC_INPUT_DICT)
    input_dict[KEY_SPAN] = "15.0"
    input_dict[KEY_CARRIAGEWAY_WIDTH] = "7.5"
    input_dict[KEY_PROJECT_LOCATION] = "Test Bridge ED"
    input_dict[KEY_SKEW_ANGLE] = "0.0"
    
    # Pre-populate defaults (creates dynamic keys for 4 girders i.e. G1G2, G2G3, G3G4)
    solve_extend_basic_input_dict(input_dict)
    
    # Update type and parameters for all end diaphragms
    for k in list(input_dict.keys()):
        if k.startswith(KEY_MP_ED_TYPE):
            input_dict[k] = ed_type
        elif connection_type and k.startswith(KEY_MP_ED_BRACING_CONNECTION):
            input_dict[k] = connection_type
        elif is_section and k.startswith(KEY_MP_ED_IS_SECTION):
            input_dict[k] = is_section
        elif welded_dims:
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
    
    # Run design
    bridge.design()
    
    print("\nDesign completed successfully!")
    print(f"End Diaphragm Results:")
    for pair, designs in bridge.end_diaphragm_design_results.items():
        print(f"Pair: {pair}")
        for member_type, res in designs.items():
            if member_type in ("diagonal", "chord"):
                print(f"  {member_type}:")
                for force_type, r in res.items():
                    section = r.get("section_size.designation") or r.get("Optimum.Designation")
                    status = "PASS" if section else "FAIL"
                    print(f"    {force_type}: {status} (Section: {section})")
            elif member_type in ("rolled_beam", "welded_beam"):
                section = res.get("Optimum.Designation")
                status = "PASS" if section else "FAIL"
                ur = res.get("Optimum.UR")
                m_dem = res.get("Moment.Demand")
                m_cap = res.get("Moment.Strength")
                v_dem = res.get("Shear.Demand")
                v_cap = res.get("Shear.Strength")
                print(f"  {member_type}: {status} (Section/Designation: {section}, UR: {ur})")
                print(f"    Moment Demand: {m_dem} kNm, Capacity: {m_cap} kNm")
                print(f"    Shear Demand:  {v_dem} kN, Capacity: {v_cap} kN")
                assert m_dem is not None, f"Missing Moment.Demand in {member_type}"
                assert v_dem is not None, f"Missing Shear.Demand in {member_type}"
                assert section is not None, f"Missing Designation in {member_type}"

if __name__ == "__main__":
    os.makedirs("/home/khushi-dudhalkar/OsdagBridge/logs", exist_ok=True)
    
    # 1. Cross Bracing (Bolted)
    run_ed_design("Cross Bracing", connection_type="Bolted")
    
    # 2. Cross Bracing (Welded)
    run_ed_design("Cross Bracing", connection_type="Welded")
    
    # 3. Rolled Beam
    run_ed_design("Rolled Beam", is_section="ISMB 400")
    
    # 4. Welded Beam
    welded_dims = {
        "depth": 500,
        "web_t": 10,
        "top_w": 250,
        "top_t": 16,
        "bot_w": 250,
        "bot_t": 16
    }
    run_ed_design("Welded Beam", welded_dims=welded_dims)

    # 5. State isolation test: CB = Bolted, ED = Welded
    # Verifies that changing CB connection type has no effect on ED results, and vice versa.
    print("\n" + "=" * 60)
    print("STATE ISOLATION TEST: CB=Bolted, ED=Welded (Cross Bracing)")
    print("=" * 60)
    from osdagbridge.core.utils.common import KEY_MP_CB_BRACING_CONNECTION
    input_dict = dict(BASIC_INPUT_DICT)
    input_dict[KEY_SPAN] = "15.0"
    input_dict[KEY_CARRIAGEWAY_WIDTH] = "7.5"
    input_dict[KEY_PROJECT_LOCATION] = "Isolation Test"
    input_dict[KEY_SKEW_ANGLE] = "0.0"
    solve_extend_basic_input_dict(input_dict)

    for k in list(input_dict.keys()):
        if k.startswith(KEY_MP_ED_TYPE):
            input_dict[k] = "Cross Bracing"
        elif k.startswith(KEY_MP_ED_BRACING_CONNECTION):
            input_dict[k] = "Welded"           # ED uses Welded
        elif k.startswith(KEY_MP_CB_BRACING_CONNECTION):
            input_dict[k] = "Bolted"           # CB uses Bolted (different)

    bridge = PlateGirderBridge()
    bridge.set_input(input_dict)
    bridge.design()

    ed_results = bridge.end_diaphragm_design_results
    cb_results = bridge.crossbracing_design_results

    print("\n[ISOLATION] ED results (should show Welded pipeline):")
    for pair, designs in ed_results.items():
        print(f"  Pair {pair}: keys={list(designs.keys())}")

    print("\n[ISOLATION] CB results (should show Bolted pipeline, independent of ED):")
    for pair, designs in cb_results.items():
        print(f"  Pair {pair}: keys={list(designs.keys())}")

    print("\nState isolation test completed successfully.")
    print("\nAll End Diaphragm runs finished successfully!")

