"""
end_diaphragm_rolled.py

Osdag CLI interface for Rolled Beam End Diaphragm design (Flexure Simply Supported).
"""

from typing import Any
from osdagbridge.core.utils.connect import run_calculation


def design_rolled_end_diaphragm(
    designation: str,
    span_m: float,
    moment_kNm: float,
    shear_kN: float,
    material_grade: str = "E 250 (Fe 410 W)A",
) -> dict:
    """
    Run Osdag Simply Supported Flexure design check for a Rolled Beam end diaphragm.

    Parameters
    ----------
    designation : str
        Selected beam section designation (e.g., 'MB 300').
    span_m : float
        Effective span length in meters.
    moment_kNm : float
        Factored bending moment in kNm.
    shear_kN : float
        Factored shear force in kN.
    material_grade : str
        Steel grade.

    Returns
    -------
    dict
        Osdag design output dictionary.
    """
    des = designation.strip()
    if des.startswith("ISMB"):
        des = des.replace("ISMB", "MB").strip()
    elif des.startswith("IS") and not des.startswith("ISL") and not des.startswith("ISM"):
        des = des[2:].strip()

    payload = {
        "Module": "Flexural Members - Simply Supported",
        "Member.Profile": "Beams and Columns",
        "Member.Designation": [des],
        "Material": material_grade,
        "Member.Material": material_grade,
        "Flexure.Type": "Major Laterally Supported",
        "Torsion.restraint": "Fully Restrained",
        "Warping.restraint": "Both flanges fully restrained",
        "Member.Length": str(round(span_m, 3)),
        "Length.Overwrite": "No",
        "Effective.Area_Para": "1.0",
        "Optimum.Class": "No",
        "Bearing.Length": "100",
        "Load.Moment": str(round(max(0.1, moment_kNm), 3)),
        "Load.Shear": str(round(max(0.1, shear_kN), 3)),
        "Loading.Condition": "Normal",
    }
    return run_calculation(payload)
