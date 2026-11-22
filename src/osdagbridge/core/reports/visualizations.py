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
