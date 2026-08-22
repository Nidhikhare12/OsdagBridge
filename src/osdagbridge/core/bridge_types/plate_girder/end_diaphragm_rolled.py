"""
end_diaphragm_rolled.py

Osdag CLI interface for Rolled Beam End Diaphragm design (Flexure Simply Supported).
"""

from typing import Any, List

from osdagbridge.core.utils.connect import run_calculation


# Standard Indian beam sections in ascending depth order.
# Used as fallback candidates when the user-specified section is too small.
_FALLBACK_BEAMS: list[str] = [
    "JB 150", "MB 100", "MB 125", "MB 150", "WB 150",
    "JB 175", "MB 175", "WB 175",
    "JB 200", "MB 200", "WB 200",
    "JB 225", "MB 225", "WB 225",
    "MB 250", "WB 250",
    "MB 300", "WB 300",
    "MB 350", "WB 350",
    "MB 400", "WB 400",
    "MB 450", "WB 450",
    "MB 500", "WB 500",
    "MB 550", "WB 550",
    "MB 600", "WB 600",
]


def _normalize_designation(designation: str) -> str:
    """Normalize an Indian Standard beam designation for Osdag's Flexure module.

    Osdag's Beams database stores designations like 'MB 300', 'JB 150', etc.
    User input may come as 'ISMB 300' which needs to be converted to 'MB 300'.
    """
    des = designation.strip()
    if des.startswith("ISMB"):
        des = des.replace("ISMB", "MB").strip()
    elif des.startswith("ISJB"):
        des = des.replace("ISJB", "JB").strip()
    elif des.startswith("ISWB"):
        des = des.replace("ISWB", "WB").strip()
    elif des.startswith("ISLB"):
        des = des.replace("ISLB", "LB").strip()
    elif des.startswith("IS") and not des.startswith("ISL") and not des.startswith("ISM"):
        des = des[2:].strip()
    return des


def _build_payload(
    designations: List[str],
    span_m: float,
    moment_kNm: float,
    shear_kN: float,
    material_grade: str,
) -> dict:
    """Build the Osdag Flexure module payload dictionary."""
    return {
        "Module": "Flexural Members - Simply Supported",
        "Member.Profile": "Beams and Columns",
        "Member.Designation": designations,
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


def _is_design_successful(result: dict) -> bool:
    """Check whether Osdag returned a populated (non-empty) design result."""
    opt_des = result.get("Optimum.Designation", "")
    return bool(opt_des and str(opt_des).strip())


def design_rolled_end_diaphragm(
    designation: str,
    span_m: float,
    moment_kNm: float,
    shear_kN: float,
    material_grade: str = "E 250 (Fe 410 W)A",
) -> dict:
    """
    Run Osdag Simply Supported Flexure design check for a Rolled Beam end diaphragm.

    The function first attempts the design with the user-specified section alone.
    If that section is structurally inadequate (e.g. plastic section modulus too
    small for the applied moment), it automatically retries with a broader list of
    standard Indian beam sections so Osdag can find the lightest adequate one.

    Parameters
    ----------
    designation : str
        Selected beam section designation (e.g., 'MB 300', 'JB 150', 'ISMB 400').
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
        Osdag design output dictionary. Contains ``'design_status': True/False``
        and, on failure, ``'design_failure_reason'`` with a human-readable message.
    """
    des = _normalize_designation(designation)

    # --- Attempt 1: User's specified section only ---
    payload = _build_payload([des], span_m, moment_kNm, shear_kN, material_grade)
    result = run_calculation(payload)

    if _is_design_successful(result):
        result["design_status"] = True
        result["design_attempt"] = "user_section"
        return result

    # --- Attempt 2: Broader fallback list ---
    # Build a candidate list: user's section first, then all fallback beams
    # that are not duplicates.
    candidates = [des]
    for fb in _FALLBACK_BEAMS:
        if fb != des and fb not in candidates:
            candidates.append(fb)

    print(
        f"[Rolled Beam] Section '{des}' alone is inadequate for "
        f"M={moment_kNm:.2f} kNm, V={shear_kN:.2f} kN. "
        f"Retrying with {len(candidates)} candidate sections..."
    )

    payload2 = _build_payload(candidates, span_m, moment_kNm, shear_kN, material_grade)
    result2 = run_calculation(payload2)

    if _is_design_successful(result2):
        selected = result2.get("Optimum.Designation", "")
        print(
            f"[Rolled Beam] Osdag selected '{selected}' as optimum "
            f"(UR={result2.get('Optimum.UR', '?')}). "
            f"Original user section '{des}' was too small."
        )
        result2["design_status"] = True
        result2["design_attempt"] = "fallback_list"
        result2["original_designation"] = des
        return result2

    # --- Both attempts failed ---
    print(
        f"[Rolled Beam] WARNING: Design failed even with {len(candidates)} "
        f"candidate sections. M={moment_kNm:.2f} kNm, V={shear_kN:.2f} kN, "
        f"span={span_m:.3f} m. No standard Indian beam is adequate."
    )
    result2["design_status"] = False
    result2["design_attempt"] = "fallback_list"
    result2["design_failure_reason"] = (
        f"No standard beam section is adequate for "
        f"M={moment_kNm:.2f} kNm, V={shear_kN:.2f} kN at span={span_m:.3f} m. "
        f"User specified '{des}'. Consider a welded beam or plate girder."
    )
    return result2
