"""
end_diaphragm_welded.py

Osdag CLI interface for Welded Beam End Diaphragm design (PlateGirderWelded).
"""

from typing import Any
from osdagbridge.core.utils.connect import run_calculation


def design_welded_end_diaphragm(
    depth_mm: float,
    web_thk_mm: float,
    top_width_mm: float,
    top_thk_mm: float,
    bot_width_mm: float,
    bot_thk_mm: float,
    span_m: float,
    moment_kNm: float,
    shear_kN: float,
    material_grade: str = "E 250 (Fe 410 W)A",
) -> dict:
    """
    Run Osdag Plate Girder Welded design check for a Welded Beam end diaphragm.

    Parameters
    ----------
    depth_mm : float
        Total plate girder depth in mm.
    web_thk_mm : float
        Web thickness in mm.
    top_width_mm : float
        Top flange width in mm.
    top_thk_mm : float
        Top flange thickness in mm.
    bot_width_mm : float
        Bottom flange width in mm.
    bot_thk_mm : float
        Bottom flange thickness in mm.
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
    span_mm = round(span_m * 1000.0)
    payload = {
        "Module": "PLATE GIRDER",
        "Material": material_grade,
        "Total.Design_Type": "Customized",
        "Total.Depth": str(round(depth_mm)),
        "Web.Thickness": str(round(web_thk_mm)),
        "Topflange.Width": str(round(top_width_mm)),
        "TopFlange.Thickness": str(round(top_thk_mm)),
        "Bottomflange.Width": str(round(bot_width_mm)),
        "BottomFlange.Thickness": str(round(bot_thk_mm)),
        "Member.Length": str(span_mm),
        "Flexure.Type": "Major Laterally Supported",
        "Support.Width": "100",
        "Web.Philosophy": "Thick Web without ITS",
        "Torsion.restraint": "Fully Restrained",
        "Warping.restraint": "Both flanges fully restrained",
        "Bendingmoment.shape": "Uniform Loading with pinned-pinned support",
        "Load.Moment": str(round(max(0.1, moment_kNm), 3)),
        "Load.Shear": str(round(max(0.1, shear_kN), 3)),
        "Loading.Condition": "Normal",
        "LongitudnalStiffener": "No",
        "LongitudnalStiffener.Data": "No",
        "IntermediateStiffener.Spacing": str(span_mm),
        "IntermediateStiffener.Thickness": "No",
        "LongitudnalStiffner.Thickness": "No",
        "Deflection.Max": "150",
        "Symmetry": "Symmetric Girder",
        "Optimum.Class": "No",
    }
    return run_calculation(payload)
