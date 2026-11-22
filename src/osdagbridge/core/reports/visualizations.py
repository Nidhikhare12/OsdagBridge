# =============================================================================
# OsdagBridge — Utilization Ratio Visualizations  (R4)
#
# Public API
# ----------
# extract_ur_data(bridge) -> list[dict]
#     Returns a 4-element list of UR records for:
#       Plate Girder, Concrete Deck Slab, Cross Bracing, End Diaphragm
#
# generate_ur_chart(ur_data, output_path, title) -> None
#     Writes a horizontal bar chart PNG to output_path using the Agg backend.
#     Never fabricates demand/capacity values — only reads design results.
# =============================================================================
from __future__ import annotations

import math
import os
import sys
from typing import TYPE_CHECKING

# Ensure Conda Library\bin is on PATH and in DLL search path on Windows
if sys.platform == "win32":
    _lib_bin = os.path.join(sys.prefix, "Library", "bin")
    if os.path.isdir(_lib_bin):
        if _lib_bin not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _lib_bin + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(_lib_bin)
            except OSError:
                pass

from osdagbridge.core.reports.styles import (
    COLOR_OSDAG_GREEN_HEX,
    COLOR_STATUS_FAIL,
    COLOR_STATUS_PASS,
    COLOR_STATUS_WARN,
    COLOR_UR_THRESHOLD,
)

if TYPE_CHECKING:  # avoid circular import at runtime
    from osdagbridge.core.reports.report_generator import ReportDataBridge

# ---------------------------------------------------------------------------
# Constants — mirroring keyfile.py values so we do not import from there
# (keyfile.py is a data module; importing it here would pull in heavy deps
#  and break unit tests that mock only report_generator primitives).
# ---------------------------------------------------------------------------
_DCR_PASS = 0.90
_DCR_FAIL = 1.00

# Check IDs to include in the governing plate-girder UR.
# Excludes stiffener checks (20, 21) and stud detailing (6, 7).
_PG_CHECK_IDS = {1, 2, 3, 4, 5, 8, 9, 11, 13, 14}

# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def _classify_ur(ur: float | None) -> str:
    """Return PASS / WARN / FAIL / Not Available based on numeric UR."""
    if ur is None:
        return "Not Available"
    if ur < _DCR_PASS:
        return "PASS"
    if ur < _DCR_FAIL:
        return "WARN"
    return "FAIL"


def _bar_color(status: str) -> str:
    """Map a status string to an RGB hex colour (matches Osdag palette)."""
    _map = {
        "PASS": "#" + COLOR_OSDAG_GREEN_HEX,     # Osdag green
        "WARN": "#" + "FFA500",                   # orange
        "FAIL": "#" + "CC0000",                   # dark red
        "Not Available": "#AAAAAA",
        "Not Run": "#AAAAAA",
        "Not Designed": "#AAAAAA",
        "Design Not Implemented": "#AAAAAA",
    }
    return _map.get(status, "#AAAAAA")


# ---------------------------------------------------------------------------
# Component extractors
# ---------------------------------------------------------------------------

def _extract_girder_ur(bridge) -> dict:
    """
    Governing plate-girder UR = max DCR over all interior girders and all
    included check IDs (1-5, 8, 9, 11, 13, 14).

    Returns a dict with keys: label, ur, check, status.
    """
    per_girder = (
        (bridge.output_dict.get("design_results") or {})
        .get("per_girder") or {}
    )
    if not per_girder:
        return {"label": "Plate Girder (Governing)", "ur": None,
                "check": "", "status": "Not Run"}

    best_ur: float | None = None
    best_check = ""
    for g_name, g_data in per_girder.items():
        if str(g_name).startswith("EB"):
            continue          # edge beams excluded from summary
        for chk in (g_data.get("checks") or []):
            cid = int(chk.get("check_id", -1))
            if cid not in _PG_CHECK_IDS:
                continue
            dcr = chk.get("dcr")
            try:
                dcr = float(dcr)
                if not math.isfinite(dcr):
                    continue
            except (TypeError, ValueError):
                continue
            if best_ur is None or dcr > best_ur:
                best_ur = dcr
                best_check = chk.get("name", f"Check {cid}")

    if best_ur is None:
        return {"label": "Plate Girder (Governing)", "ur": None,
                "check": "", "status": "Not Run"}
    return {
        "label": "Plate Girder (Governing)",
        "ur": best_ur,
        "check": best_check,
        "status": _classify_ur(best_ur),
    }


def _extract_deck_ur(bridge) -> dict:
    """
    Governing deck-slab UR = max over 6 ULS/SLS checks mirroring Table 5.22.
    Returns a dict with keys: label, ur, check, status.
    """
    from osdagbridge.core.utils.common import (
        KEY_DD_M_ULS_SAG, KEY_DD_MU_BOT,
        KEY_DD_M_ULS_HOG, KEY_DD_MU_TOP,
        KEY_DD_M_ULS_OH,  KEY_DD_MU_OH,
        KEY_DD_PUNCH_VED, KEY_DD_VRD_C_MPA,
        KEY_DD_SHEAR_VED, KEY_DD_SHEAR_VRDC,
        KEY_DD_WK_BOT,    KEY_DD_WK_TOP,
        KEY_DD_WK_OH,     KEY_DD_WK_LIMIT,
        KEY_DD_HAS_OVERHANG,
    )

    deck_rpt = bridge.output_dict.get("deck_report_values") or {}
    if not deck_rpt:
        return {"label": "Concrete Deck Slab (Governing)", "ur": None,
                "check": "", "status": "Not Run"}

    def _dv(key):
        v = deck_rpt.get(key)
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    def _safe_ur(demand, cap, name):
        if cap > 0 and math.isfinite(demand) and math.isfinite(cap):
            val = demand / cap
            if math.isfinite(val):
                return (val, name)
        return (None, name)

    _dk_oh = bool(deck_rpt.get(KEY_DD_HAS_OVERHANG))
    _wk_lim = _dv(KEY_DD_WK_LIMIT)
    _wk_bot = _dv(KEY_DD_WK_BOT)
    _wk_top = _dv(KEY_DD_WK_TOP)
    _wk_oh  = _dv(KEY_DD_WK_OH) if _dk_oh else 0.0
    _gov_wk = max(_wk_bot, _wk_top, _wk_oh)

    candidates = [
        _safe_ur(_dv(KEY_DD_M_ULS_SAG), _dv(KEY_DD_MU_BOT),   "Flexure (Sag)"),
        _safe_ur(_dv(KEY_DD_M_ULS_HOG), _dv(KEY_DD_MU_TOP),   "Flexure (Hog)"),
        _safe_ur(_dv(KEY_DD_PUNCH_VED), _dv(KEY_DD_VRD_C_MPA), "Punching Shear"),
        _safe_ur(_dv(KEY_DD_SHEAR_VED), _dv(KEY_DD_SHEAR_VRDC),"One-Way Shear"),
    ]
    if _dk_oh:
        candidates.append(_safe_ur(_dv(KEY_DD_M_ULS_OH), _dv(KEY_DD_MU_OH), "Overhang Flexure"))
    if _wk_lim > 0:
        candidates.append((_gov_wk / _wk_lim, "Crack Width"))

    best_ur: float | None = None
    best_check = ""
    for ur, name in candidates:
        if ur is None:
            continue
        if best_ur is None or ur > best_ur:
            best_ur = ur
            best_check = name

    if best_ur is None:
        return {"label": "Concrete Deck Slab (Governing)", "ur": None,
                "check": "", "status": "Not Run"}
    return {
        "label": "Concrete Deck Slab (Governing)",
        "ur": best_ur,
        "check": best_check,
        "status": _classify_ur(best_ur),
    }


def _extract_cb_ur(bridge) -> dict:
    """
    Governing cross-bracing UR = max efficiency over all pairs, members,
    force types using existing ReportDataBridge helpers.
    """
    pairs = bridge.get_cb_pairs()
    if not pairs:
        return {"label": "Cross Bracing (Governing)", "ur": None,
                "check": "", "status": "Not Designed"}

    best_ur: float | None = None
    best_label = ""
    for pair in pairs:
        for member in ("diagonal", "chord"):
            for ft in ("tension", "compression"):
                raw = bridge.get_cb_efficiency(pair, member, ft)
                if not raw:
                    continue
                try:
                    val = float(raw)
                    if not math.isfinite(val):
                        continue
                except (TypeError, ValueError):
                    continue
                if best_ur is None or val > best_ur:
                    best_ur = val
                    best_label = f"{pair} / {member} ({ft})"

    if best_ur is None:
        return {"label": "Cross Bracing (Governing)", "ur": None,
                "check": "", "status": "Not Designed"}
    return {
        "label": "Cross Bracing (Governing)",
        "ur": best_ur,
        "check": best_label,
        "status": _classify_ur(best_ur),
    }


def _extract_ed_ur(bridge) -> dict:
    """
    End Diaphragm UR.
    - Cross Bracing type: read end_diaphragm_design_results directly
      (same pair→member→force_type→{efficiency} structure as CB).
    - Rolled Beam / Welded Beam: no design check implemented → 'Design Not Implemented'.
    - Unknown / missing type: 'Not Available'.
    """
    from osdagbridge.core.utils.common import KEY_MP_ED_TYPE

    # Determine ED type from the first pair's output_dict entry
    ed_design_results = bridge.output_dict.get("end_diaphragm_design_results") or {}
    # Try to infer type from output_dict pair keys
    ed_type = None
    for key, val in bridge.output_dict.items():
        if isinstance(key, str) and "end_diaphragm_type" in key.lower():
            ed_type = str(val).strip()
            break
    if ed_type is None:
        # Fallback: search for KEY_MP_ED_TYPE sub-key pattern in output_dict
        for key, val in bridge.output_dict.items():
            if isinstance(key, str) and key.startswith("member_properties.end_diaphragm.type"):
                ed_type = str(val).strip()
                break

    # If we couldn't determine type but have design results, treat as CB-type
    if ed_type is None and ed_design_results:
        ed_type = "Cross Bracing"

    if ed_type is None:
        return {"label": "End Diaphragm", "ur": None,
                "check": "", "status": "Not Available"}

    if ed_type in ("Rolled Beam", "Welded Beam"):
        return {"label": "End Diaphragm", "ur": None,
                "check": ed_type, "status": "Design Not Implemented"}

    if ed_type == "Cross Bracing":
        if not ed_design_results:
            return {"label": "End Diaphragm", "ur": None,
                    "check": "", "status": "Not Designed"}
        # Read efficiency directly from end_diaphragm_design_results
        # Structure: {pair: {member: {force_type: raw_osdag_result}}}
        from osdagbridge.core.bridge_types.plate_girder.results_data import (
            _extract_osdag_summary,
        )
        best_ur: float | None = None
        best_label = ""
        for pair, members in ed_design_results.items():
            if not isinstance(members, dict):
                continue
            for member, force_types in members.items():
                if not isinstance(force_types, dict):
                    continue
                for ft, raw in force_types.items():
                    summary = _extract_osdag_summary(raw or {})
                    eff = summary.get("efficiency")
                    try:
                        eff = float(eff)
                        if not math.isfinite(eff):
                            continue
                    except (TypeError, ValueError):
                        continue
                    if best_ur is None or eff > best_ur:
                        best_ur = eff
                        best_label = f"{pair} / {member} ({ft})"
        if best_ur is None:
            return {"label": "End Diaphragm", "ur": None,
                    "check": "", "status": "Not Designed"}
        return {
            "label": "End Diaphragm",
            "ur": best_ur,
            "check": best_label,
            "status": _classify_ur(best_ur),
        }

    # Unknown ED type string
    return {"label": "End Diaphragm", "ur": None,
            "check": ed_type, "status": "Not Available"}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_ur_data(bridge) -> list[dict]:
    """
    Return a 4-element list of UR records, one per structural component:
      [Plate Girder, Concrete Deck Slab, Cross Bracing, End Diaphragm]

    Each record is a dict with:
      label  (str)        — display label for the chart
      ur     (float|None) — numeric utilization ratio, or None if unavailable
      check  (str)        — name of the governing check / source description
      status (str)        — 'PASS', 'WARN', 'FAIL', 'Not Run', 'Not Designed',
                            'Design Not Implemented', or 'Not Available'
    """
    return [
        _extract_girder_ur(bridge),
        _extract_deck_ur(bridge),
        _extract_cb_ur(bridge),
        _extract_ed_ur(bridge),
    ]


def generate_ur_chart(
    ur_data: list[dict],
    output_path: str,
    title: str = "Utilization Ratio Summary",
) -> None:
    """
    Generate a horizontal bar chart of utilization ratios and save as PNG.

    Parameters
    ----------
    ur_data     : list returned by extract_ur_data()
    output_path : absolute or relative path to write the PNG
    title       : chart title shown above the figure
    """
    import matplotlib
    matplotlib.use("Agg")          # non-interactive; must be set before pyplot
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import matplotlib.lines as mlines

    labels = [rec["label"] for rec in ur_data]
    urs    = [rec["ur"] for rec in ur_data]
    statuses = [rec["status"] for rec in ur_data]
    checks   = [rec["check"] for rec in ur_data]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    fig.patch.set_facecolor("white")

    y_pos = list(range(len(labels)))

    for i, (ur, status, chk) in enumerate(zip(urs, statuses, checks)):
        color = _bar_color(status)
        if ur is None:
            # Gray hatched bar at a nominal width to signal N/A
            bar = ax.barh(i, 0.3, color=color, edgecolor="#666666",
                          hatch="///", height=0.5, zorder=3)
            ax.text(0.35, i, f"({status})", va="center", ha="left",
                    fontsize=8.5, color="#555555", style="italic")
        else:
            ax.barh(i, ur, color=color, edgecolor="white",
                    height=0.5, zorder=3)
            ax.text(ur + 0.01, i, f"{ur:.3f}", va="center", ha="left",
                    fontsize=8.5, fontweight="bold", color="#222222")
            if chk:
                ax.text(-0.02, i - 0.30, chk, va="center", ha="right",
                        fontsize=6.5, color="#555555", style="italic",
                        transform=ax.get_yaxis_transform())

    # UR = 1.0 reference line
    ax.axvline(x=1.0, color="#CC0000", linestyle="--", linewidth=1.5,
               zorder=4, label="UR = 1.0 (capacity limit)")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Utilization Ratio (Demand / Capacity)", fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold", pad=10)

    # X-axis range
    valid_urs = [u for u in urs if u is not None]
    x_max = max(1.25, max(valid_urs) + 0.15) if valid_urs else 1.25
    ax.set_xlim(0, x_max)
    ax.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    # Legend patches
    legend_patches = [
        mpatches.Patch(color="#91B014", label="PASS  (UR < 0.90)"),
        mpatches.Patch(color="#FFA500", label="WARN  (0.90 ≤ UR < 1.00)"),
        mpatches.Patch(color="#CC0000", label="FAIL  (UR ≥ 1.00)"),
        mpatches.Patch(color="#AAAAAA", label="Not Available / Not Designed"),
        mlines.Line2D([0], [0], color="#CC0000", linestyle="--",
                   linewidth=1.5, label="UR = 1.0 limit"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=7.5,
              framealpha=0.85)

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# =============================================================================
# Material Quantity Visualizations (R5)
#
# Public API
# ----------
# extract_quantity_data(input_dict: dict) -> dict
#     Extracts structural steel, concrete, and reinforcement quantities from
#     calculated BOQ keys. Distinguishes available vs. unavailable vs. estimated.
#
# generate_quantity_charts(qty_data: dict, tmp_dir: str) -> tuple[str | None, str | None]
#     Generates two PNG charts inside tmp_dir:
#       1. Structural Steel Quantities (MT) - Horizontal bar chart
#       2. Concrete (m³) & Reinforcement (MT) - Side-by-side subplots
# =============================================================================

def _parse_quantity(val) -> tuple[float | None, str]:
    """
    Parse a numeric quantity value from string or number.
    Returns (numeric_value, status_code).
    status_code can be:
      - 'VALID'
      - 'ZERO'
      - 'NOT_AVAILABLE' (if None or 'N.A.')
      - 'INVALID' (if malformed, NaN, Inf, or negative)
    """
    if val is None or val == "N.A." or val == "":
        return None, "NOT_AVAILABLE"
    try:
        f = float(val)
    except (ValueError, TypeError):
        return None, "INVALID"
    if not math.isfinite(f) or f < 0.0:
        return None, "INVALID"
    if f == 0.0:
        return 0.0, "ZERO"
    return f, "VALID"


def extract_quantity_data(input_dict: dict) -> dict:
    """
    Extract structural steel, concrete, and reinforcement quantities from input_dict.

    Parameters
    ----------
    input_dict : dict
        Dictionary containing inputs and calculated BOQ quantities.

    Returns
    -------
    dict
        Structured quantity summary with parsed values, units, and status notes.
    """
    if not isinstance(input_dict, dict):
        input_dict = {}

    # 1. Plate Girders (MT)
    g_val, g_code = _parse_quantity(input_dict.get("steel_girders_wt_total"))
    if g_val is not None:
        g_status = "Available" if g_val > 0.0 else "Zero Quantity"
    elif g_code == "NOT_AVAILABLE":
        g_status = "Not Available — Girder quantity not calculated"
    else:
        g_status = "Invalid — Girder quantity malformed or negative"

    # 2. Cross Bracing (MT)
    # Composed of top chord, bottom chord, and diagonal chords
    top_val, top_code = _parse_quantity(input_dict.get("bracing_top_wt_total"))
    bot_val, bot_code = _parse_quantity(input_dict.get("bracing_bot_wt_total"))
    diag_val, diag_code = _parse_quantity(input_dict.get("bracing_diag_wt_total"))

    cb_components = {
        "top": top_val,
        "bot": bot_val,
        "diag": diag_val,
    }

    if top_code == "INVALID" or bot_code == "INVALID" or diag_code == "INVALID":
        cb_val = None
        cb_status = "Invalid — Bracing component data malformed or negative"
    elif top_code == "NOT_AVAILABLE" and bot_code == "NOT_AVAILABLE" and diag_code == "NOT_AVAILABLE":
        cb_val = None
        cb_status = "Not Available — Cross bracing quantity not calculated"
    elif top_val is not None and bot_val is not None and diag_val is not None:
        cb_val = top_val + bot_val + diag_val
        cb_status = "Available" if cb_val > 0.0 else "Zero Quantity"
    else:
        cb_val = None
        cb_status = "Incomplete — Some bracing components not available"

    # 3. End Diaphragms (MT)
    # Check if explicitly provided (future-proof), otherwise mark as not calculated
    ed_raw = input_dict.get("ed_steel_wt_total") or input_dict.get("end_diaphragm_wt_total")
    ed_val, ed_code = _parse_quantity(ed_raw)
    if ed_val is not None:
        ed_status = "Available" if ed_val > 0.0 else "Zero Quantity"
    elif ed_code == "INVALID":
        ed_status = "Invalid — ED quantity malformed or negative"
    else:
        ed_status = "Not Available — ED quantity not calculated"

    # 4. Structural Steel Subtotal / Total
    # Rule: If ED is unavailable, do not label as total. Use computed subtotal.
    if g_val is not None and cb_val is not None:
        if ed_val is not None:
            subtotal_val = g_val + cb_val + ed_val
            subtotal_label = "Total Structural Steel"
            is_total = True
            subtotal_status = "Total Available"
        else:
            subtotal_val = g_val + cb_val
            subtotal_label = "Computed subtotal (girders + cross bracing; ED excluded)"
            is_total = False
            subtotal_status = "Subtotal Available (ED excluded)"
    else:
        subtotal_val = None
        subtotal_label = "Computed subtotal (girders + cross bracing; ED excluded)"
        is_total = False
        subtotal_status = "Not Available — Components incomplete"

    # 5. Concrete Deck Slab (m³)
    c_val, c_code = _parse_quantity(input_dict.get("concrete_deck_vol_total"))
    if c_val is not None:
        c_status = "Available" if c_val > 0.0 else "Zero Volume"
    elif c_code == "NOT_AVAILABLE":
        c_status = "Not Available — Concrete volume not calculated"
    else:
        c_status = "Invalid — Concrete volume malformed or negative"

    # 6. Reinforcement Steel (MT) — Rule-of-thumb estimate
    r_val, r_code = _parse_quantity(input_dict.get("rebar_deck_wt_total"))
    if r_val is not None:
        r_status = "Estimated (120 kg/m³ of concrete)"
    elif r_code == "NOT_AVAILABLE":
        r_status = "Not Available — Reinforcement quantity not calculated"
    else:
        r_status = "Invalid — Reinforcement quantity malformed or negative"

    return {
        "plate_girders": {
            "label": "Plate Girders",
            "value": g_val,
            "unit": "MT",
            "status": g_status,
            "is_available": g_val is not None,
        },
        "cross_bracing": {
            "label": "Cross Bracing",
            "value": cb_val,
            "unit": "MT",
            "status": cb_status,
            "is_available": cb_val is not None,
            "components": cb_components,
        },
        "end_diaphragms": {
            "label": "End Diaphragms",
            "value": ed_val,
            "unit": "MT",
            "status": ed_status,
            "is_available": ed_val is not None,
        },
        "structural_steel_subtotal": {
            "label": subtotal_label,
            "value": subtotal_val,
            "unit": "MT",
            "status": subtotal_status,
            "is_available": subtotal_val is not None,
            "is_total": is_total,
        },
        "concrete_deck": {
            "label": "Deck Concrete",
            "value": c_val,
            "unit": "m³",
            "status": c_status,
            "is_available": c_val is not None,
        },
        "reinforcement": {
            "label": "Reinforcement Steel",
            "value": r_val,
            "unit": "MT",
            "status": r_status,
            "is_available": r_val is not None,
            "is_estimated": True,
            "estimate_annotation": "Estimated (120 kg/m³ of concrete)",
        },
    }


def generate_quantity_charts(
    qty_data: dict,
    tmp_dir: str,
) -> tuple[str | None, str | None]:
    """
    Generate the structural steel and concrete/reinforcement quantity charts.

    Parameters
    ----------
    qty_data : dict
        Structured data dictionary returned by extract_quantity_data().
    tmp_dir  : str
        Temporary directory path where images will be saved.

    Returns
    -------
    tuple[str | None, str | None]
        (chart1_path, chart2_path) paths to the saved PNG files, or None on failure.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    if not os.path.isdir(tmp_dir):
        return None, None

    chart1_path = os.path.join(tmp_dir, "qty_chart_steel.png")
    chart2_path = os.path.join(tmp_dir, "qty_chart_concrete_rebar.png")

    # -------------------------------------------------------------------------
    # Chart 1: Structural Steel Quantities (MT) - Horizontal Bar Chart
    # -------------------------------------------------------------------------
    try:
        fig1, ax1 = plt.subplots(figsize=(8.5, 4.2))
        fig1.patch.set_facecolor("white")

        items = [
            qty_data.get("structural_steel_subtotal", {}),
            qty_data.get("end_diaphragms", {}),
            qty_data.get("cross_bracing", {}),
            qty_data.get("plate_girders", {}),
        ]

        labels = [item.get("label", "") for item in items]
        values = [item.get("value") for item in items]
        statuses = [item.get("status", "") for item in items]
        is_avails = [item.get("is_available", False) for item in items]

        # Colors: Girders (Green), Cross Bracing (Orange), End Diaphragms (Gray), Subtotal (Steel Blue)
        colors = ["#2B5B84", "#AAAAAA", "#FFA500", "#91B014"]

        valid_vals = [v for v in values if v is not None]
        x_max = max(valid_vals) * 1.35 if valid_vals else 10.0
        nom_width = max(0.08 * x_max, 0.5)

        y_pos = list(range(len(items)))

        for i, (val, status, avail, col) in enumerate(zip(values, statuses, is_avails, colors)):
            if avail and val is not None:
                ax1.barh(i, val, color=col, edgecolor="white", height=0.52, zorder=3)
                ax1.text(val + 0.02 * x_max, i, f"{val:.2f} MT",
                         va="center", ha="left", fontsize=9, fontweight="bold", color="#222222")
            else:
                ax1.barh(i, nom_width, color="#CCCCCC", edgecolor="#888888",
                         hatch="///", height=0.52, zorder=3)
                ax1.text(nom_width + 0.02 * x_max, i, f"({status})",
                         va="center", ha="left", fontsize=8, color="#555555", style="italic")

        # Distinct separation line above subtotal bar
        ax1.axhline(0.5, color="#D0D0D0", linestyle="--", linewidth=0.9, zorder=2)

        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(labels, fontsize=8.5)
        ax1.set_xlabel("Weight (Metric Tonnes, MT)", fontsize=9)
        ax1.set_title("Structural Steel Material Quantities (IS 2062)", fontsize=10.5, fontweight="bold", pad=12)
        ax1.set_xlim(0, x_max)
        ax1.grid(axis="x", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
        ax1.set_axisbelow(True)

        # Legend
        legend_patches = [
            mpatches.Patch(color="#91B014", label="Plate Girders"),
            mpatches.Patch(color="#FFA500", label="Cross Bracing"),
            mpatches.Patch(color="#2B5B84", label="Computed Subtotal"),
            mpatches.Patch(color="#CCCCCC", hatch="///", label="Not Available / Uncalculated"),
        ]
        ax1.legend(handles=legend_patches, loc="lower right", fontsize=8, framealpha=0.9)

        fig1.tight_layout()
        fig1.savefig(chart1_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig1)
    except Exception:
        chart1_path = None

    # -------------------------------------------------------------------------
    # Chart 2: Concrete Volume (m³) & Reinforcement Weight (MT) - Subplots
    # -------------------------------------------------------------------------
    try:
        fig2, (ax_conc, ax_rebar) = plt.subplots(1, 2, figsize=(8.5, 4.0))
        fig2.patch.set_facecolor("white")

        # Left: Concrete Volume (m³)
        conc_item = qty_data.get("concrete_deck", {})
        c_val = conc_item.get("value")
        c_avail = conc_item.get("is_available", False)
        c_status = conc_item.get("status", "")

        if c_avail and c_val is not None:
            ax_conc.bar(0, c_val, width=0.45, color="#91B014", edgecolor="white", zorder=3)
            ax_conc.text(0, c_val + 0.02 * c_val, f"{c_val:.2f} m³",
                         ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#222222")
            ax_conc.set_ylim(0, max(c_val * 1.25, 1.0))
        else:
            ax_conc.bar(0, 0.25, width=0.45, color="#CCCCCC", edgecolor="#888888",
                        hatch="///", zorder=3)
            ax_conc.text(0, 0.28, f"({c_status})",
                         ha="center", va="bottom", fontsize=8, color="#555555", style="italic")
            ax_conc.set_ylim(0, 1.0)

        ax_conc.set_xticks([0])
        ax_conc.set_xticklabels(["Deck Slab Concrete\n(Grade M40)"], fontsize=9)
        ax_conc.set_ylabel("Volume (m³)", fontsize=9)
        ax_conc.set_title("Concrete Volume", fontsize=10, fontweight="bold", pad=10)
        ax_conc.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
        ax_conc.set_axisbelow(True)

        # Right: Reinforcement Steel (MT)
        rebar_item = qty_data.get("reinforcement", {})
        r_val = rebar_item.get("value")
        r_avail = rebar_item.get("is_available", False)
        r_status = rebar_item.get("status", "")

        if r_avail and r_val is not None:
            ax_rebar.bar(0, r_val, width=0.45, color="#D84315", edgecolor="white", zorder=3)
            ax_rebar.text(0, r_val + 0.02 * r_val, f"{r_val:.2f} MT",
                          ha="center", va="bottom", fontsize=9.5, fontweight="bold", color="#222222")
            ax_rebar.set_ylim(0, max(r_val * 1.30, 1.0))
        else:
            ax_rebar.bar(0, 0.25, width=0.45, color="#CCCCCC", edgecolor="#888888",
                         hatch="///", zorder=3)
            ax_rebar.text(0, 0.28, f"({r_status})",
                          ha="center", va="bottom", fontsize=8, color="#555555", style="italic")
            ax_rebar.set_ylim(0, 1.0)

        ax_rebar.set_xticks([0])
        ax_rebar.set_xticklabels(["Reinforcement Steel\n(Fe 500 Grade)"], fontsize=9)
        ax_rebar.set_ylabel("Weight (Metric Tonnes, MT)", fontsize=9)
        ax_rebar.set_title("Reinforcement Steel Weight", fontsize=10, fontweight="bold", pad=10)
        ax_rebar.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.5, zorder=0)
        ax_rebar.set_axisbelow(True)

        # Estimate annotation box on the reinforcement subplot
        ax_rebar.text(
            0.5, 0.88,
            "Note: Empirical estimate\n(120 kg/m³ of concrete slab)\nActual detailing not computed",
            transform=ax_rebar.transAxes, ha="center", va="top",
            fontsize=7.8, style="italic", color="#4E342E",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF8E1", edgecolor="#FFE082", alpha=0.92, linewidth=0.8),
            zorder=5,
        )

        fig2.tight_layout()
        fig2.savefig(chart2_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig2)
    except Exception:
        chart2_path = None

    return chart1_path, chart2_path
