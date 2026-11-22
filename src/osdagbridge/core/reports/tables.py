"""Centralized table builder and cell formatting system for LaTeX reports.

Enforces repeating headers across page breaks (endfirsthead, endhead, endfoot,
endlastfoot), column wrapping, status badges, and vertical spacing guards.
"""

import math
from typing import List, Optional, Sequence, Union, Any
from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.utils.common import (
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_FOOTPATH,
    KEY_WC_LD_LANE_TABLE_COUNT,
)


def status_badge(passed: Optional[bool], pass_label: str = "PASS", fail_label: str = "FAIL") -> str:
    """Format a passing or failing status badge with semantic theme colors."""
    if passed is True:
        return f"\\textbf{{\\color{{OsdagPass}}{{{pass_label}}}}}"
    elif passed is False:
        return f"\\textbf{{\\color{{OsdagFail}}{{{fail_label}}}}}"
    return "-"


def cell(value: Any, decimals: int = 2, unit: str = "", na_str: str = "-") -> str:
    """Format an arbitrary value safely for LaTeX table embedding.

    Handles None, NaN, inf, bool, float, int, and str without double-escaping.
    """
    if value is None:
        return na_str

    if isinstance(value, bool):
        return status_badge(value)

    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            return na_str
        if isinstance(value, int):
            formatted = str(value)
        else:
            abs_val = abs(value)
            if abs_val > 0.0 and (abs_val < 1e-3 or abs_val >= 1e6):
                formatted = f"{value:.{decimals}e}"
            else:
                formatted = f"{value:.{decimals}f}"
                # Normalize negative zero (-0.000 -> 0.000)
                if formatted.startswith("-") and float(formatted) == 0.0:
                    formatted = formatted[1:]
        u = f"~{unit}".strip() if unit else ""
        return f"{formatted}{u}"

    s = str(value).strip()
    if not s or s.lower() in ("none", "nan", "null"):
        return na_str

    # If already formatted with LaTeX macros (\...), preserve as is
    if "\\" in s and any(cmd in s for cmd in ("\\infty", "\\makecell", "\\textbf", "\\color", "\\parbox", "\\dfrac", "\\sqrt", "\\alpha", "\\beta", "\\gamma", "\\sigma", "\\Delta", "\\text")):
        return s + (f"~{unit}" if unit else "")

    escaped = _tex(s)
    return escaped + (f"~{unit}" if unit else "")


def keep_heading_with_content(lines: int = 5) -> str:
    """Return LaTeX needspace guard to prevent orphan table titles or section splits."""
    return f"\\needspace{{{lines}\\baselineskip}}\n"


def build_longtable(
    caption: str,
    label: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    col_spec: Optional[str] = None,
    col_widths: Optional[Sequence[str]] = None,
    note: Optional[str] = None,
    zebra: bool = False,
    row_skip: str = "4pt",
) -> str:
    """Construct an enterprise-grade longtable with full page-break repeat headers.

    Emits \\endfirsthead, \\endhead, \\endfoot, and \\endlastfoot blocks to guarantee
    consistent headers on subsequent pages and prevent footer overlap.
    """
    num_cols = len(headers)
    if col_spec is None:
        if col_widths is not None and len(col_widths) == num_cols:
            col_spec = "|" + "|".join(f"L{{{w}}}" for w in col_widths) + "|"
        else:
            col_spec = "|" + "|".join(["l"] * num_cols) + "|"

    formatted_headers = " & ".join(f"\\textbf{{{h}}}" for h in headers) + " \\\\*"

    out = []
    out.append("\\setlength\\LTleft{0pt}")
    out.append("\\setlength\\LTright\\fill")
    out.append(f"\\begin{{longtable}}{{{col_spec}}}")
    out.append(f"\\caption{{\\textbf{{{caption}}}}}\\label{{{label}}} \\\\")
    out.append("\\hline")
    out.append("\\rowcolor{OsdagHeaderBg}")
    out.append(formatted_headers)
    out.append("\\hline")
    out.append("\\endfirsthead")
    out.append("")
    out.append("\\multicolumn{" + str(num_cols) + "}{c}{\\small\\textit{" + caption + " (continued from previous page)}} \\\\[4pt]")
    out.append("\\hline")
    out.append("\\rowcolor{OsdagHeaderBg}")
    out.append(formatted_headers)
    out.append("\\hline")
    out.append("\\endhead")
    out.append("")
    out.append("\\hline")
    out.append(f"\\multicolumn{{{num_cols}}}{{r}}{{\\small\\textit{{Continued on next page}}}} \\\\")
    out.append("\\endfoot")
    out.append("")
    out.append("\\hline")
    out.append("\\endlastfoot")
    out.append("")

    for idx, r in enumerate(rows):
        if zebra and idx % 2 == 1:
            out.append("\\rowcolor{OsdagZebra}")
        cells = []
        for c in r:
            if isinstance(c, tuple) and len(c) >= 2:
                cells.append(cell(c[0], decimals=c[1], unit=c[2] if len(c) > 2 else ""))
            elif isinstance(c, (int, float, bool, str)) or c is None:
                cells.append(cell(c))
            else:
                cells.append(str(c))
        row_str = " & ".join(cells) + f" \\\\[{row_skip}]"
        out.append(row_str)
        out.append("\\hline")

    out.append("\\end{longtable}")
    if note:
        out.append(f"\\noindent\\textit{{Note: {note}}}\n")
    return "\n".join(out)


def build_vehicle_live_load_table(input_dict: dict, span_m: float, lanes_count: int) -> str:
    """Build Chapter 3 Table 3.2A for Vehicular Live Loads per Requirement 3.

    Features grouped braking header via multirow, bound dynamically to UI active vehicles.
    """
    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    # Evaluate impact factor for span
    try:
        im_a = 1.0 + IRC6_2017.cl_208_2_impact_factor(span_m)
        im_a_str = f"{im_a:.3f}"
    except Exception:
        im_a_str = "1.240"

    try:
        im_70r = 1.0 + IRC6_2017.cl_208_3_impact_factor(span_m)
        im_70r_str = f"{im_70r:.3f}"
    except Exception:
        im_70r_str = "1.100"

    # Evaluate braking force based on lane count per IRC 6 Cl. 211
    try:
        lanes = max(int(lanes_count), 1)
        brk_t = IRC6_2017.cl_211_2_braking_force(lanes)
        brk_kn = brk_t * 9.80665
        brk_str = f"{brk_kn:.2f} kN"
    except Exception:
        brk_str = "N/A"

    # Map standard IRC vehicles
    vehicle_rows = []
    if input_dict.get(KEY_LL_IRC_CLASS_A):
        vehicle_rows.append((
            "Class A Train",
            "8-axle wheeled vehicle train",
            "554.0 kN (55.4 t)",
            im_a_str,
            brk_str,
        ))

    if input_dict.get(KEY_LL_IRC_70R_WHEELED):
        vehicle_rows.append((
            "Class 70R (Wheeled)",
            "7-axle heavy wheeled vehicle",
            "1000.0 kN (100.0 t)",
            im_70r_str,
            brk_str,
        ))

    if input_dict.get(KEY_LL_IRC_70R_TRACKED):
        vehicle_rows.append((
            "Class 70R (Tracked)",
            "2 continuous bogie tracks",
            "700.0 kN (70.0 t)",
            im_70r_str,
            brk_str,
        ))

    if input_dict.get(KEY_LL_IRC_AA_WHEELED):
        vehicle_rows.append((
            "Class AA (Wheeled)",
            "2-axle heavy wheeled vehicle",
            "400.0 kN (40.0 t)",
            im_70r_str,
            brk_str,
        ))

    if input_dict.get(KEY_LL_IRC_AA_TRACKED):
        vehicle_rows.append((
            "Class AA (Tracked)",
            "Tracked military loading",
            "700.0 kN (70.0 t)",
            im_70r_str,
            brk_str,
        ))

    if input_dict.get(KEY_LL_IRC_CLASS_SV):
        vehicle_rows.append((
            "Special Vehicle (SV)",
            "Multi-axle hydraulic trailer",
            "3850.0 kN (385.0 t)",
            "1.000 (No impact per Cl. 204.5)",
            brk_str,
        ))

    if input_dict.get(KEY_LL_IRC_70R_BOGIE):
        vehicle_rows.append((
            "Class 70R (Bogie)",
            "2-axle bogie loading",
            "400.0 kN (40.0 t)",
            im_70r_str,
            brk_str,
        ))

    if input_dict.get(KEY_LL_IRC_CLASS_FATIGUE):
        vehicle_rows.append((
            "Fatigue Vehicle",
            "4-axle standardized truck",
            "400.0 kN (40.0 t)",
            "1.000 (Cl. 204.6)",
            "N/A",
        ))

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES)
    if custom and isinstance(custom, list):
        for c in custom:
            name = c.get("name", "Custom Vehicle") if isinstance(c, dict) else str(c)
            vehicle_rows.append((name, "Custom defined load pattern", "Custom", "1.000", brk_str))

    if not vehicle_rows:
        vehicle_rows.append(("Class A Train", "8-axle wheeled vehicle train", "554.0 kN", im_a_str, brk_str))

    num_rows = len(vehicle_rows)
    col_spec = "|L{3.0cm}|L{4.2cm}|C{2.3cm}|C{2.3cm}|C{3.2cm}|"

    out = []
    out.append("\\setlength\\LTleft{0pt}")
    out.append("\\setlength\\LTright\\fill")
    out.append(f"\\begin{{longtable}}{{{col_spec}}}")
    out.append("\\caption{\\textbf{Vehicular Live Loads and Dynamic Factors}}\\label{tab:vehicular-live-loads} \\\\")
    out.append("\\hline")
    out.append("\\rowcolor{OsdagHeaderBg}")
    out.append("\\textbf{Vehicle Class} & \\textbf{Configuration} & \\textbf{Total Load} & \\textbf{\\makecell{Impact\\\\Factor}} & \\textbf{\\makecell{Braking /\\\\Tractive Effort\\\\(Cl. 211)}} \\\\[6pt]")
    out.append("\\hline")
    out.append("\\endfirsthead")
    out.append("")
    out.append("\\multicolumn{5}{c}{\\small\\textit{Vehicular Live Loads and Dynamic Factors (continued from previous page)}} \\\\[4pt]")
    out.append("\\hline")
    out.append("\\rowcolor{OsdagHeaderBg}")
    out.append("\\textbf{Vehicle Class} & \\textbf{Configuration} & \\textbf{Total Load} & \\textbf{\\makecell{Impact\\\\Factor}} & \\textbf{\\makecell{Braking /\\\\Tractive Effort\\\\(Cl. 211)}} \\\\[6pt]")
    out.append("\\hline")
    out.append("\\endhead")
    out.append("")
    out.append("\\hline")
    out.append("\\multicolumn{5}{r}{\\small\\textit{Continued on next page}} \\\\")
    out.append("\\endfoot")
    out.append("")
    out.append("\\hline")
    out.append("\\endlastfoot")
    out.append("")

    for idx, (v_class, config, load, imp, brk) in enumerate(vehicle_rows):
        if idx % 2 == 1:
            out.append("\\rowcolor{OsdagZebra}")
        out.append(f"{v_class} & {config} & {load} & {imp} & {brk} \\\\[6pt]")
        out.append("\\hline")

    out.append("\\end{longtable}")
    out.append("\\noindent\\textit{Note: Longitudinal braking and tractive forces applied at 1.2 m above carriageway surface in accordance with IRC 6 Cl. 211.3.}\n")
    return "\n".join(out)


def build_centrifugal_force_table(input_dict: dict) -> str:
    """Build Chapter 3 Table 3.2B for Centrifugal Forces per Requirement 3."""
    radius_val = input_dict.get("geometry.horizontal_radius")
    speed_val = input_dict.get("loading.design_speed")

    is_curved = False
    radius_m = None
    if radius_val not in (None, "", "inf", "infinity", "0", 0):
        try:
            r = float(radius_val)
            if r > 0.0:
                radius_m = r
                is_curved = True
        except (ValueError, TypeError):
            is_curved = False

    if is_curved and radius_m is not None:
        try:
            speed_kmh = float(speed_val) if speed_val not in (None, "") else 80.0
            centrifugal_factor = (speed_kmh ** 2) / (127.0 * radius_m)
            c_factor_str = f"{centrifugal_factor:.4f}"
            c_force_str = f"{centrifugal_factor * 100.0:.2f} % of Live Load"
        except Exception:
            c_factor_str = "-"
            c_force_str = "-"

        rows = [
            ("Alignment Type", "Horizontal Curve"),
            ("Radius of Curvature (R)", f"{radius_m:.1f} m"),
            ("Design Speed (V)", f"{speed_kmh:.1f} km/h"),
            ("Centrifugal Factor (C = V^2 / 127R)", c_factor_str),
            ("Transverse Centrifugal Force", c_force_str),
        ]
        note = "Centrifugal force acts horizontally at 1.2 m above roadway per IRC 6 Cl. 212."
    else:
        rows = [
            ("Alignment Type", "Straight / Tangent Alignment"),
            ("Radius of Curvature (R)", "$\\infty$ (Straight)"),
            ("Centrifugal Factor (C)", "0.0000"),
            ("Centrifugal Force", "0.00 kN (Negligible)"),
        ]
        note = "Bridge is situated on a straight alignment; centrifugal forces are zero per IRC 6 Cl. 212."

    return build_longtable(
        caption="Centrifugal Force Evaluation (IRC 6 Cl. 212)",
        label="tab:centrifugal-force",
        headers=["Parameter", "Design Value"],
        rows=rows,
        col_widths=["7.0cm", "8.5cm"],
        note=note,
        zebra=True,
    )


def build_footway_live_load_table(input_dict: dict) -> str:
    """Build Chapter 3 Table 3.2C for Footway Live Load per Requirement 3."""
    footpath_type = str(input_dict.get(KEY_FOOTPATH, "None")).strip().lower()
    fp_width = input_dict.get(KEY_TS_FOOTPATH_WIDTH)
    has_footpath = footpath_type not in ("none", "no", "")

    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE, "")
    fp_custom_val = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE, "")

    if has_footpath:
        try:
            width_m = float(fp_width) if fp_width not in (None, "") else 1.5
        except (ValueError, TypeError):
            width_m = 1.5

        if str(fp_mode).strip().lower() in ("as per irc 6", "as per irc6", "automatic", ""):
            intensity_str = r"4.00 kN/m$^2$"
            governing_clause = "IRC 6 Cl. 206.1 (Pedestrian crowd load on footway)"
        else:
            intensity_str = f"{float(fp_custom_val):.2f} " + r"kN/m$^2$" if fp_custom_val else r"4.00 kN/m$^2$"
            governing_clause = "User Specified Custom Footpath Intensity"

        rows = [
            ("Footpath Provision", "Provided on Superstructure"),
            ("Footpath Width", f"{width_m:.2f} m"),
            ("Live Load Intensity (P)", intensity_str),
            ("Governing Code & Clause", governing_clause),
        ]
        note = "Pedestrian live load applied over footpath area per IRC 6 Cl. 206.1."
    else:
        rows = [
            ("Footpath Provision", "None (No Footpath on Deck)"),
            ("Footpath Width", "0.00 m"),
            ("Live Load Intensity", r"0.00 kN/m$^2$"),
            ("Governing Code & Clause", "IRC 6 Cl. 206"),
        ]
        note = "No pedestrian footway provided in the bridge typical cross section; footpath live load is not applicable."

    return build_longtable(
        caption="Footpath / Pedestrian Live Load (IRC 6 Cl. 206)",
        label="tab:footpath-live-load",
        headers=["Parameter", "Design Detail"],
        rows=rows,
        col_widths=["7.0cm", "8.5cm"],
        note=note,
        zebra=True,
    )
