import os

# Force UTF-8 encoding in all subprocesses
os.environ["PYTHONIOENCODING"] = "utf-8"

import builtins
import contextlib
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Dict, List


# Safe print wrapper to avoid Unicode crashes
_original_print = print

def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except UnicodeEncodeError:
        pass

builtins.print = safe_print

# Reconfigure Windows terminal encoding
if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
    sys.stderr.reconfigure(encoding="utf-8", errors="ignore")

from osdag_core.cli import _get_output_dictionary

from osdag_core.design_type.compression_member.compression_bolted import Compression_bolted
from osdag_core.design_type.compression_member.compression_welded import Compression_welded
from osdag_core.design_type.tension_member.tension_bolted import Tension_bolted
from osdag_core.design_type.tension_member.tension_welded import Tension_welded
from osdag_core.design_type.flexural_member.flexure import Flexure
from osdag_core.design_type.plate_girder.core.plate_girder import PlateGirderWelded

MODULE_CLASS_MAP = {
    "Tension Member Design - Bolted to End Gusset": Tension_bolted,
    "Tension Member Design - Welded to End Gusset": Tension_welded,
    "Struts Bolted to End Gusset": Compression_bolted,
    "Struts Welded to End Gusset": Compression_welded,
    "Flexural Members - Simply Supported": Flexure,
    "PLATE GIRDER": PlateGirderWelded,
}

# OUTPUT SUPPRESSION
@contextlib.contextmanager
def suppress_output(enabled: bool = True):
    if not enabled:
        yield
        return

    logging.disable(logging.CRITICAL)

    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull):
            with contextlib.redirect_stderr(devnull):
                yield

    logging.disable(logging.NOTSET)

def run_calculation(design_dict: Dict[str, Any], quiet: bool = True) -> Dict[str, Any]:
    # Every subprocess needs UTF-8 again
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
        sys.stderr.reconfigure(encoding="utf-8", errors="ignore")

    with suppress_output(quiet):
        module_name = design_dict.get("Module")
        module_class = MODULE_CLASS_MAP.get(module_name)

        if not module_class:
            raise ValueError(f"Unsupported module type: {module_name}")

        module_instance = module_class()
        module_instance.set_osdaglogger(None, None)

        validation_errors = module_instance.func_for_validation(design_dict)

        if validation_errors:
            print(f"[Osdag] Validation errors: {validation_errors}")
            raise RuntimeError("Validation errors occurred during execution.")

        output_dict = _get_output_dictionary(module_instance)

        return output_dict

_forkserver_preloaded = False


def design_pool(max_workers: int) -> ProcessPoolExecutor:
    """Executor for osdag_core design checks with a thread-safe start method.

    The default fork start method is unsafe here: the design pipeline runs on a
    QThread while the GUI thread spins the Qt event loop, and a fork taken at that
    moment inherits mutexes locked by other threads — the child deadlocks before it
    ever reaches run_calculation (observed hang in stage 7).

    forkserver avoids that (the server is launched via fork+exec, so workers fork
    from its clean single-threaded state) while staying fast: this module is
    preloaded into the server once, so every worker starts with osdag_core already
    imported and shares those pages copy-on-write. Windows has no forkserver and
    falls back to spawn — its default start method anyway.
    """
    import multiprocessing
    try:
        ctx = multiprocessing.get_context("forkserver")
        global _forkserver_preloaded
        if not _forkserver_preloaded:
            ctx.set_forkserver_preload(["osdagbridge.core.utils.connect"])
            _forkserver_preloaded = True
    except ValueError:
        ctx = multiprocessing.get_context("spawn")
    return ProcessPoolExecutor(max_workers=max_workers, mp_context=ctx)


def run_parallel_designs(design_dicts: List[Dict[str, Any]], quiet: bool = True) -> List[Dict[str, Any]]:
    cpu_count = os.cpu_count() or 4
    max_workers = min(cpu_count, len(design_dicts))

    with design_pool(max_workers) as executor:
        futures = [
            executor.submit(run_calculation, design_dict, quiet) 
            for design_dict in design_dicts
        ]
        results = [future.result() for future in futures]

    return results

EQUAL_ANGLE_DESIGNATIONS = [
    "20 x 20 x 3",
    "20 x 20 x 4",
    "25 x 25 x 3",
    "25 x 25 x 4",
    "25 x 25 x 5",
    "30 x 30 x 3",  
    "30 x 30 x 4",
    "30 x 30 x 5",
    "35 x 35 x 3",
    "35 x 35 x 4",
    "35 x 35 x 5",
    "35 x 35 x 6",
    "40 x 40 x 3",
    "40 x 40 x 4",
    "40 x 40 x 5",
    "40 x 40 x 6",
    "45 x 45 x 3",
    "45 x 45 x 4",
    "45 x 45 x 5",
    "45 x 45 x 6",
    "50 x 50 x 3",
    "50 x 50 x 4",
    "50 x 50 x 5",
    "50 x 50 x 6",
    "55 x 55 x 4",
    "55 x 55 x 5",
    "55 x 55 x 6",
    "55 x 55 x 8",
    "60 x 60 x 4",
    "60 x 60 x 5",
    "60 x 60 x 6",
    "60 x 60 x 8",
    "65 x 65 x 4",
    "65 x 65 x 5",
    "65 x 65 x 6",
    "65 x 65 x 8",
    "70 x 70 x 5",
    "70 x 70 x 6",
    "70 x 70 x 8",
    "70 x 70 x 10",
    "75 x 75 x 5",
    "75 x 75 x 6",
    "75 x 75 x 8",
    "75 x 75 x 10",
    "80 x 80 x 6",
    "80 x 80 x 8",
    "80 x 80 x 10",
    "80 x 80 x 12",
    "90 x 90 x 6",
    "90 x 90 x 8",
    "90 x 90 x 10",
    "90 x 90 x 12",
    "100 x 100 x 6",
    "100 x 100 x 8",
    "100 x 100 x 10",
    "100 x 100 x 12",
    "110 x 110 x 8",
    "110 x 110 x 10",
    "110 x 110 x 12",
    "110 x 110 x 16",
]

# TENSION BOLTED
design_dict_tension_bolted = {
    "Bolt.Bolt_Hole_Type": "Standard",
    "Bolt.Diameter": ["8", "10", "12", "16", "20", "24", "30", "36", "42", "48", "56", "64", "14", "18", "22", "27", "33", "39", "45", "52", "60"],
    "Bolt.Grade": ["3.6", "4.6", "4.8", "5.6", "5.8", "6.8", "8.8", "9.8", "10.9", "12.9"],
    "Bolt.Slip_Factor": "0.3",
    "Bolt.TensionType": "Pre-tensioned",
    "Bolt.Type": "Bearing Bolt",
    "Conn_Location": "Long Leg",
    "Connector.Material": "E 250 (Fe 410 W)A",
    "Connector.Plate.Thickness_List": ["8", "10", "12", "14", "16", "18", "20", "22", "25", "28", "32", "36", "40", "45", "50", "56", "63", "75", "80", "90", "100", "110", "120"],
    "Design.Design_Method": "Limit State Design",
    "Detailing.Corrosive_Influences": "No",
    "Detailing.Edge_type": "Sheared or hand flame cut",
    "Detailing.Gap": "10",
    "Load.Axial": "4",
    "Material": "E 250 (Fe 410 W)A",
    "Member.Designation": EQUAL_ANGLE_DESIGNATIONS,
    "Member.Length": "1500",
    "Member.Material": "E 250 (Fe 410 W)A",
    "Member.Profile": "Back to Back Angles",
    "Module": "Tension Member Design - Bolted to End Gusset",
    "out_titles_status": [1, 1, 1, 1, 1],
}

# TENSION WELDED
design_dict_tension_welded = {
    "Conn_Location": "Long Leg",
    "Connector.Material": "E 165 (Fe 290)",
    "Connector.Plate.Thickness_List": ["8", "10", "12"],
    "Design.Design_Method": "Limit State Design",
    "Load.Axial": "5",
    "Material": "E 165 (Fe 290)",
    "Member.Designation": EQUAL_ANGLE_DESIGNATIONS,
    "Member.Length": "500",
    "Member.Material": "E 165 (Fe 290)",
    "Member.Profile": "Angles",
    "Module": "Tension Member Design - Welded to End Gusset",
    "Weld.Fab": "Shop Weld",
    "Weld.Material_Grade_OverWrite": "290",
    "out_titles_status": [1, 1, 1, 1, 1],
}

# STRUTS BOLTED
design_dict_struts_bolted = {
    "Bolt.Bolt_Hole_Type": "Standard",
    "Bolt.Diameter": ["8", "10", "12", "16", "20", "24", "30", "36", "42", "48", "56", "64", "14", "18", "22", "27", "33", "39", "45", "52", "60"
],
    "Bolt.Grade": ["3.6", "4.6", "4.8", "5.6", "5.8", "6.8", "8.8", "9.8", "10.9", "12.9"],
    "Bolt.Slip_Factor": "0.3",
    "Bolt.TensionType": "Pre-tensioned",
    "Bolt.Type": "Bearing Bolt",
    "Conn_Location": "Long Leg",
    "Connector.Material": "E 250 (Fe 410 W)A",
    "Connector.Plate.Thickness_List": ["8", "10", "12", "16", "18", "20", "22", "25", "28", "32", "36", "40", "45", "50", "56", "63", "75", "80", "90", "100", "110", "120"],
    "Design.Design_Method": "Limit State Design",
    "Detailing.Corrosive_Influences": "No",
    "Detailing.Edge_type": "Sheared or hand flame cut",
    "Detailing.Gap": "10",
    "End_1": "Fixed",
    "End_2": "Fixed",
    "Load.Axial": "10",
    "Material": "E 250 (Fe 410 W)A",
    "Member.Designation": EQUAL_ANGLE_DESIGNATIONS,
    "Member.Length": "1500",
    "Member.Material": "E 250 (Fe 410 W)A",
    "Member.Profile": "Back to Back Angles",
    "Module": "Struts Bolted to End Gusset",
    "is_leg_loaded": "Yes",
}

# STRUTS WELDED
design_dict_struts_welded = {
    " In_Plane": "1.0",
    " Out_of_Plane": "1.0",
    "Bolt.Number": "1.0",
    "Conn_Location": "Long Leg",
    "Connector.Plate.Thickness_List": "8",
    "Design.Design_Method": "Limit State Design",
    "Effective.Area_Para": "1.0",
    "End_1": "Fixed",
    "End_2": "Fixed",
    "Load.Axial": "9",
    "Load.Type": "Concentric Load",
    "Material": "E 165 (Fe 290)",
    "Member.Designation": EQUAL_ANGLE_DESIGNATIONS,
    "Member.Length": "900",
    "Member.Material": "E 165 (Fe 290)",
    "Member.Profile": "Angles",
    "Module": "Struts Welded to End Gusset",
    "Optimum.AllowUR": "1.0",
    "Weld.Fab": "Shop Weld",
    "Weld.Material_Grade_OverWrite": "290",
    "out_titles_status": [1, 1, 1, 1, 1],
}
# END DIAPHRAGM — ROLLED (Simply Supported / Flexure module)
# KEY → string-value reference (from osdag_core.Common):
#   KEY_MODULE                = 'Module'
#   KEY_SEC_PROFILE           = 'Member.Profile'      (must be in VALUES_SEC_PROFILE3 = ['Beams and Columns'])
#   KEY_SECSIZE               = 'Member.Designation'
#   KEY_MATERIAL              = 'Material'
#   KEY_SEC_MATERIAL          = 'Member.Material'      ← was missing (caused KeyError)
#   KEY_DESIGN_TYPE_FLEXURE   = 'Flexure.Type'         (must be in VALUES_SUPP_TYPE_temp)
#   KEY_TORSIONAL_RES         = 'Torsion.restraint'
#   KEY_WARPING_RES           = 'Warping.restraint'
#   KEY_LENGTH                = 'Member.Length'
#   KEY_MOMENT                = 'Load.Moment'
#   KEY_SHEAR                 = 'Load.Shear'
#   KEY_LENGTH_OVERWRITE      = 'Length.Overwrite'     ← was missing
#   KEY_EFFECTIVE_AREA_PARA   = 'Effective.Area_Para'  ← was missing
#   KEY_ALLOW_CLASS           = 'Optimum.Class'        ← was missing
#   KEY_BEARING_LENGTH        = 'Bearing.Length'       ← was missing
#   KEY_LOAD                  = 'Loading.Condition'    ← was missing
#   KEY_DP_DESIGN_METHOD      = 'Design.Design_Method' ← was missing
design_dict_end_diaphragm_rolled = {
    # --- Input dock keys (from input_values()) ---
    "Module": "Flexural Members - Simply Supported",
    "Member.Profile": "Beams and Columns",           # VALUES_SEC_PROFILE3 = ['Beams and Columns']
    "Member.Designation": [
        "MB 200", "MB 250", "MB 300", "MB 350",
        "MB 400", "MB 450", "MB 500", "MB 600",
        "WB 300", "WB 350", "WB 400", "WB 450", "WB 500",
    ],
    "Material": "E 250 (Fe 410 W)A",
    "Flexure.Type": "Major Laterally Supported",     # VALUES_SUPP_TYPE_temp[0]
    "Torsion.restraint": "Fully Restrained",
    "Warping.restraint": "Both flanges fully restrained",
    "Member.Length": "1500",    # mm  — placeholder; overwritten at runtime with actual ED span
    "Load.Moment": "5",         # kNm — placeholder; overwritten at runtime with |Mz|
    "Load.Shear": "5",          # kN  — placeholder; overwritten at runtime with |Vy|
    # --- Design-preference keys (from get_values_for_design_pref / input_dictionary_without_design_pref) ---
    "Member.Material": "E 250 (Fe 410 W)A",  # KEY_SEC_MATERIAL — was missing
    "Length.Overwrite": "NA",                # KEY_LENGTH_OVERWRITE
    "Effective.Area_Para": "1.0",            # KEY_EFFECTIVE_AREA_PARA
    "Optimum.Class": "Yes",                  # KEY_ALLOW_CLASS
    "Bearing.Length": "NA",                  # KEY_BEARING_LENGTH
    "Loading.Condition": "Normal",           # KEY_LOAD
    "Design.Design_Method": "Limit State Design",  # KEY_DP_DESIGN_METHOD
}

# END DIAPHRAGM — WELDED (Plate Girder module)
# KEY → string-value reference (from osdag_core.Common):
#   KEY_MODULE                           = 'Module'
#   KEY_MATERIAL                         = 'Material'
#   KEY_OVERALL_DEPTH_PG_TYPE            = 'Total.Design_Type'       ('Optimized' or 'Customized')
#   KEY_OVERALL_DEPTH_PG                 = 'Total.Depth'
#   KEY_WEB_THICKNESS_PG                 = 'Web.Thickness'
#   KEY_TOP_Bflange_PG                   = 'Topflange.Width'
#   KEY_TOP_FLANGE_THICKNESS_PG          = 'TopFlange.Thickness'
#   KEY_BOTTOM_Bflange_PG                = 'Bottomflange.Width'
#   KEY_BOTTOM_FLANGE_THICKNESS_PG       = 'BottomFlange.Thickness'
#   KEY_LENGTH                           = 'Member.Length'
#   KEY_DESIGN_TYPE_FLEXURE              = 'Flexure.Type'
#   KEY_SUPPORT_WIDTH                    = 'Support.Width'
#   KEY_WEB_PHILOSOPHY                   = 'Web.Philosophy'
#   KEY_TORSIONAL_RES                    = 'Torsion.restraint'
#   KEY_WARPING_RES                      = 'Warping.restraint'
#   KEY_MOMENT                           = 'Load.Moment'
#   KEY_SHEAR                            = 'Load.Shear'
#   KEY_BENDING_MOMENT_SHAPE             = 'Bendingmoment.shape'
#   KEY_IntermediateStiffener_thickness  = 'IntermediateStiffener.Thickness'  ← was missing
#   KEY_LongitudnalStiffener_thickness   = 'LongitudnalStiffner.Thickness'    ← was missing
#   KEY_MAX_DEFL                         = 'Deflection.Max'                   ← was missing
#   KEY_LOAD                             = 'Loading.Condition'                ← was missing
#   KEY_ALLOW_CLASS                      = 'Optimum.Class'                    ← was missing
#   KEY_LongitudnalStiffener             = 'LongitudnalStiffener.Data'        ← was missing
#   KEY_IntermediateStiffener_spacing    = 'IntermediateStiffener.Spacing'    ← was missing
design_dict_end_diaphragm_welded = {
    # --- Input dock keys (from input_values()) ---
    "Module": "PLATE GIRDER",
    "Material": "E 250 (Fe 410 W)A",
    "Total.Design_Type": "Optimized",              # 'Optimized' branch for optimal section sizing
    "Girder.Symmetry": "Symmetric Girder",
    "Total.Depth": "600",
    "Web.Thickness": "10",
    "Topflange.Width": "200",
    "TopFlange.Thickness": "12",
    "Bottomflange.Width": "200",
    "BottomFlange.Thickness": "12",
    "Member.Length": "1500",    # mm  — placeholder; overwritten at runtime with actual ED span
    "Flexure.Type": "Major Laterally Supported",   # VALUES_SUPP_TYPE_temp[0]
    "Support.Width": "150",
    "Web.Philosophy": "Thick Web without ITS",
    "Torsion.restraint": "Fully Restrained",
    "Warping.restraint": "Both flanges fully restrained",
    "Load.Moment": "5",         # kNm — placeholder; overwritten at runtime with |Mz|
    "Load.Shear": "5",          # kN  — placeholder; overwritten at runtime with |Vy|
    "Bendingmoment.shape": "Uniform Loading with pinned-pinned support",
    # --- Design-preference keys (from get_values_for_design_pref / input_dictionary_without_design_pref) ---
    "IntermediateStiffener.Thickness": "All",    # KEY_IntermediateStiffener_thickness
    "LongitudnalStiffner.Thickness": "All",      # KEY_LongitudnalStiffener_thickness
    "Deflection.Max": 600,                       # KEY_MAX_DEFL (int, matches default for Highway Bridge)
    "Loading.Condition": "Normal",               # KEY_LOAD
    "Optimum.Class": "Yes",                      # KEY_ALLOW_CLASS
    "LongitudnalStiffener.Data": "No",           # KEY_LongitudnalStiffener
    "IntermediateStiffener.Spacing": "NA",       # KEY_IntermediateStiffener_spacing
}

# STANDALONE TESTING
if __name__ == "__main__":
    """
    Standalone testing:
    Runs 4 parallel Osdag designs
    using ProcessPoolExecutor
    """

    design_dicts = [
        design_dict_tension_bolted,
        design_dict_tension_welded,
        design_dict_struts_bolted,
        design_dict_struts_welded,
    ]
    start_time = time.perf_counter()
    results = run_parallel_designs(design_dicts, quiet=True)
    end_time = time.perf_counter()
    total_time = end_time - start_time

    print("\nParallel execution completed\n")
    print(f"Total designs : {len(results)}")
    print(f"Execution time: {total_time:.4f} seconds")
    print(f"Average/design: {total_time / len(results):.4f} seconds")
    print("\nSample outputs:\n")

    for index, result in enumerate(results):
        print(f"\nDesign {index + 1}:\n")
        print(result)