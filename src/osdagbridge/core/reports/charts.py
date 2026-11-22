# =============================================================================
# OsdagBridge Report Charts — Matplotlib Figure Renderers
# =============================================================================
"""Chart rendering for utilization ratios and material quantities.

This module provides chart generation functions for:
- R4: Utilization ratio (UR) bar charts for girders, deck, cross bracing, end diaphragms
- R5: Material quantity bar charts (steel tonnage; concrete volume vs reinforcement weight)

All charts use matplotlib.figure.Figure + FigureCanvasAgg (no pyplot global state).
Never raises; returns None or {} on error so report generation continues.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Import matplotlib components (not pyplot)
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available; charts will not be generated")

# Import styles
try:
    from .styles import CHART
except ImportError:
    # Fallback if styles.py not in same package
    CHART = {
        "dpi": 200,
        "width_in": 6.2,
        "height_in_max": 7.0,
        "font_pt": 8,
        "ur_limit": 1.0,
        "limit_color": "#C62828",
        "pass_color": "#91B014",
        "fail_color": "#C62828",
        "na_color": "#9E9E9E",
    }


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class URRecord:
    """Utilization ratio record for one check."""
    group: str          # "Steel Plate Girders" | "Concrete Deck Slab" | "Cross Bracing" | "End Diaphragms"
    label: str          # e.g. "Girder --- Moment"
    value: Optional[float]  # None -> no data


# =============================================================================
# Helper Functions
# =============================================================================

def group_of(label: str) -> str:
    """Map check label to group name (assumption A1 from plan).
    
    Args:
        label: Check label from Table 5.22 (e.g. "Girder --- Moment")
        
    Returns:
        Group name for chart panel
    """
    label_lower = label.lower()
    
    if label_lower.startswith("girder"):
        return "Steel Plate Girders"
    elif any(x in label_lower for x in ["transverse shear (slab)", "crack width (slab)", "deck ---"]):
        return "Concrete Deck Slab"
    elif label_lower.startswith("cross bracing"):
        return "Cross Bracing"
    elif label_lower.startswith("end diaphragm"):
        return "End Diaphragms"
    else:
        return "Other"


def _to_float(x) -> Optional[float]:
    """Convert a value to float, returning None for invalid/missing values.
    
    Handles: None, "", "N.A.", "---", NaN, inf
    
    Args:
        x: Value to convert
        
    Returns:
        Float value or None
    """
    if x is None:
        return None
    
    if isinstance(x, (int, float)):
        import math
        if math.isnan(x) or math.isinf(x):
            return None
        return float(x)
    
    s = str(x).strip().upper()
    if not s or s in ("N.A.", "N/A", "---", "NAN", "INF"):
        return None
    
    try:
        val = float(s)
        import math
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    except (ValueError, TypeError):
        return None


def _escape_label(text: str) -> str:
    """Escape special characters in matplotlib labels.
    
    $ and % trigger mathtext mode; escape them for literal display.
    
    Args:
        text: Label text
        
    Returns:
        Escaped text
    """
    return text.replace('$', r'\$').replace('%', r'\%')


def _wrap_label(text: str, max_len: int = 25) -> str:
    """Wrap long labels to two lines at natural break points.
    
    Args:
        text: Label text
        max_len: Max characters per line
        
    Returns:
        Label with newline inserted if needed
    """
    if len(text) <= max_len:
        return text
    
    # Try to break at ' --- ' first
    if ' --- ' in text:
        return text.replace(' --- ', '\n')
    
    # Otherwise break at midpoint space
    mid = len(text) // 2
    for i in range(mid, len(text)):
        if text[i] == ' ':
            return text[:i] + '\n' + text[i+1:]
    
    return text


# =============================================================================
# Chart Helper Functions
# =============================================================================

def _new_figure(width_in: float, height_in: float) -> Figure:
    """Create a new Figure with standard DPI from styles.
    
    Args:
        width_in: Width in inches
        height_in: Height in inches
        
    Returns:
        Figure object configured with DPI from CHART settings
    """
    return Figure(figsize=(width_in, height_in), dpi=CHART["dpi"])


def _save_figure(fig: Figure, out_path: str) -> None:
    """Save a Figure to PNG file.
    
    Args:
        fig: Figure to save
        out_path: Output file path
    """
    canvas = FigureCanvasAgg(fig)
    canvas.print_png(out_path)


# =============================================================================
# R4: Utilization Ratio Chart
# =============================================================================

def render_ur_chart(records: list, out_dir: str) -> Optional[str]:
    """Render utilization ratio bar chart (2×2 grid, one panel per group).
    
    Chart design (per plan section 6.3):
    - 2×2 subplots (Girders, Deck, Cross Bracing, End Diaphragms)
    - Red dashed horizontal line at UR = 1.0
    - Passing bars (UR ≤ 1.0): green, no hatch
    - Failing bars (UR > 1.0): red with // diagonal hatch
    - Missing data: grey with xx hatch, labeled "N/A"
    - Value label above each bar
    - Y-axis label: "Utilization Ratio (Demand / Capacity)"
    - Y-limit: max(1.2, 1.15 × max_valid_ur)
    
    Args:
        records: List of URRecord instances
        out_dir: Directory to write PNG file
        
    Returns:
        Path to generated PNG file, or None on error/no data
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available; UR chart not generated")
        return None
    
    try:
        # Group records
        groups = {
            "Steel Plate Girders": [],
            "Concrete Deck Slab": [],
            "Cross Bracing": [],
            "End Diaphragms": [],
        }
        
        for rec in records:
            if rec.group in groups:
                groups[rec.group].append(rec)
        
        # Check if we have any valid data
        has_data = False
        for group_records in groups.values():
            for rec in group_records:
                if rec.value is not None:
                    has_data = True
                    break
            if has_data:
                break
        
        if not has_data:
            logger.info("No valid UR data; chart not generated")
            return None
        
        # Create figure with 2×2 subplots
        fig = _new_figure(CHART["width_in"], CHART["height_in_max"])
        fig.suptitle("Utilization Ratio of Primary Elements (UR = Demand / Capacity)", 
                     fontsize=10, fontweight='bold')
        
        # Subplot order: Girders (top-left), Deck (top-right), CB (bottom-left), ED (bottom-right)
        group_order = [
            "Steel Plate Girders",
            "Concrete Deck Slab",
            "Cross Bracing",
            "End Diaphragms",
        ]
        
        max_ur = 1.0
        
        for idx, group_name in enumerate(group_order, start=1):
            ax = fig.add_subplot(2, 2, idx)
            group_records = groups[group_name]
            
            if not group_records:
                ax.text(0.5, 0.5, "No data", ha='center', va='center', 
                       transform=ax.transAxes, fontsize=CHART["font_pt"])
                ax.set_title(group_name, fontsize=CHART["font_pt"] + 1, fontweight='bold')
                ax.axis('off')
                continue
            
            # Prepare data
            labels = []
            values = []
            colors = []
            hatches = []
            
            for rec in group_records:
                # Strip redundant prefix (panel title already says "Steel Plate Girders" etc.)
                label = rec.label
                if group_name == "Steel Plate Girders" and label.startswith("Girder --- "):
                    label = label.replace("Girder --- ", "", 1)
                elif group_name == "Concrete Deck Slab" and label.startswith("Deck --- "):
                    label = label.replace("Deck --- ", "", 1)
                
                # Wrap and escape label
                label = _wrap_label(_escape_label(label), max_len=20)
                labels.append(label)
                
                val = _to_float(rec.value)
                
                if val is None:
                    # N/A bar
                    values.append(0.5)  # Dummy height for visibility
                    colors.append(CHART["na_color"])
                    hatches.append('xx')
                elif val > 1.0:
                    # Failing bar
                    values.append(val)
                    colors.append(CHART["fail_color"])
                    hatches.append('//')
                    max_ur = max(max_ur, val)
                else:
                    # Passing bar
                    values.append(val)
                    colors.append(CHART["pass_color"])
                    hatches.append('')
                    max_ur = max(max_ur, val)
            
            # Plot bars
            x_pos = range(len(labels))
            bars = ax.bar(x_pos, values, color=colors, edgecolor='black', linewidth=0.5)
            
            # Apply hatches
            for bar, hatch in zip(bars, hatches):
                bar.set_hatch(hatch)
            
            # Add value labels above bars
            for i, (bar, rec) in enumerate(zip(bars, group_records)):
                val = _to_float(rec.value)
                if val is None:
                    label_text = "N/A"
                    y_pos = 0.5
                else:
                    label_text = f"{val:.2f}"
                    y_pos = bar.get_height()
                
                ax.text(bar.get_x() + bar.get_width() / 2, y_pos + 0.05,
                       label_text, ha='center', va='bottom', 
                       fontsize=CHART["font_pt"] - 1)
            
            # Red dashed line at UR = 1.0
            ax.axhline(y=1.0, color=CHART["limit_color"], linestyle='--', 
                      linewidth=1.5, label='UR = 1.0', zorder=10)
            
            # Set y-limit
            y_max = max(1.2, 1.15 * max_ur)
            ax.set_ylim(0, y_max)
            
            # Labels and formatting
            ax.set_xticks(x_pos)
            ax.set_xticklabels(labels, fontsize=CHART["font_pt"], rotation=30, ha='right')
            ax.set_ylabel("UR", fontsize=CHART["font_pt"])
            ax.set_title(group_name, fontsize=CHART["font_pt"] + 1, fontweight='bold')
            ax.grid(axis='y', alpha=0.3, linestyle=':', linewidth=0.5)
            
            # Legend only on first subplot
            if idx == 1:
                ax.legend(fontsize=CHART["font_pt"] - 1, loc='upper right')
        
        fig.tight_layout(rect=[0, 0.03, 1, 0.96])  # Leave space for suptitle and bottom labels
        
        # Save to file
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ur_chart.png")
        _save_figure(fig, out_path)
        
        logger.info(f"UR chart saved to {out_path}")
        return out_path
        
    except Exception as e:
        logger.error(f"Error generating UR chart: {e}", exc_info=True)
        return None


# =============================================================================
# R5: Material Quantity Charts
# =============================================================================

def render_quantity_charts(quantities: dict, out_dir: str) -> dict:
    """Render material quantity bar charts.
    
    Generates two charts:
    1. Steel tonnage (MT): Girders, Cross Bracing (sum of top/bottom/diagonal), End Diaphragms
    2. Concrete volume (m³) vs Reinforcement weight (MT)
    
    Args:
        quantities: Dict from boq_generator.calculate_material_quantities()
        out_dir: Directory to write PNG files
        
    Returns:
        Dict with keys 'steel_tonnage' and 'concrete_rebar' mapping to file paths (or None)
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available; quantity charts not generated")
        return {}
    
    result = {}
    
    # Chart 1: Steel Tonnage
    try:
        steel_data = {}
        
        # Girders
        girder_wt = _to_float(quantities.get("steel_girders_wt_total"))
        if girder_wt is not None:
            steel_data["Girders"] = girder_wt
        
        # Cross Bracing (sum of top, bottom, diagonal)
        cb_top = _to_float(quantities.get("bracing_top_wt_total")) or 0.0
        cb_bot = _to_float(quantities.get("bracing_bot_wt_total")) or 0.0
        cb_diag = _to_float(quantities.get("bracing_diag_wt_total")) or 0.0
        cb_total = cb_top + cb_bot + cb_diag
        
        # Fallback to aggregate key if available
        if cb_total == 0.0:
            cb_total = _to_float(quantities.get("steel_bracing_wt_total")) or 0.0
        
        if cb_total > 0.0:
            steel_data["Cross Bracing"] = cb_total
        
        # End Diaphragms — not in BOQ yet (OI-1), show N/A
        steel_data["End Diaphragms"] = None
        
        # Only render if we have at least some real data (not just the N/A end diaphragm)
        has_real_data = girder_wt is not None or cb_total > 0.0
        if has_real_data:
            result["steel_tonnage"] = _render_steel_tonnage_chart(steel_data, out_dir)
        else:
            result["steel_tonnage"] = None
    
    except Exception as e:
        logger.error(f"Error generating steel tonnage chart: {e}", exc_info=True)
        result["steel_tonnage"] = None
    
    # Chart 2: Concrete Volume vs Reinforcement Weight
    try:
        concrete_vol = _to_float(quantities.get("concrete_deck_vol_total"))
        rebar_wt = _to_float(quantities.get("rebar_deck_wt_total"))
        
        if concrete_vol is not None and rebar_wt is not None:
            result["concrete_rebar"] = _render_concrete_rebar_chart(concrete_vol, rebar_wt, out_dir)
        else:
            result["concrete_rebar"] = None
    
    except Exception as e:
        logger.error(f"Error generating concrete/rebar chart: {e}", exc_info=True)
        result["concrete_rebar"] = None
    
    return result


def _render_steel_tonnage_chart(data: dict, out_dir: str) -> Optional[str]:
    """Render steel tonnage bar chart.
    
    Args:
        data: Dict mapping component name to tonnage (MT), or None for N/A
        out_dir: Output directory
        
    Returns:
        Path to PNG file or None
    """
    try:
        fig = _new_figure(CHART["width_in"], 4.0)
        ax = fig.add_subplot(111)
        
        labels = []
        values = []
        colors = []
        hatches = []
        
        for component, tonnage in data.items():
            labels.append(component)
            if tonnage is None:
                values.append(0.5)  # Dummy height
                colors.append(CHART["na_color"])
                hatches.append('xx')
            else:
                values.append(tonnage)
                colors.append(CHART["pass_color"])
                hatches.append('')
        
        x_pos = range(len(labels))
        bars = ax.bar(x_pos, values, color=colors, edgecolor='black', linewidth=0.5)
        
        for bar, hatch in zip(bars, hatches):
            bar.set_hatch(hatch)
        
        # Value labels
        for bar, component, tonnage in zip(bars, labels, data.values()):
            if tonnage is None:
                label_text = "N/A"
                y_pos = 0.5
            else:
                label_text = f"{tonnage:.2f}"
                y_pos = bar.get_height()
            
            ax.text(bar.get_x() + bar.get_width() / 2, y_pos + max(values) * 0.02,
                   label_text, ha='center', va='bottom', fontsize=CHART["font_pt"])
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, fontsize=CHART["font_pt"], rotation=0)
        ax.set_ylabel("Weight (MT)", fontsize=CHART["font_pt"])
        ax.set_title("Steel Tonnage by Component", fontsize=10, fontweight='bold', pad=8)
        ax.grid(axis='y', alpha=0.3, linestyle=':', linewidth=0.5)
        
        # Adjust y-axis upper limit so value labels are not clipped
        y_max = max(values) * 1.18 if values else 1.0
        ax.set_ylim(0, y_max)
        
        fig.tight_layout()
        
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "steel_tonnage.png")
        _save_figure(fig, out_path)
        
        logger.info(f"Steel tonnage chart saved to {out_path}")
        return out_path
        
    except Exception as e:
        logger.error(f"Error in _render_steel_tonnage_chart: {e}", exc_info=True)
        return None


def _render_concrete_rebar_chart(concrete_vol: float, rebar_wt: float, out_dir: str) -> Optional[str]:
    """Render concrete volume vs reinforcement weight chart (two panels).
    
    Args:
        concrete_vol: Concrete volume in m³
        rebar_wt: Reinforcement weight in MT
        out_dir: Output directory
        
    Returns:
        Path to PNG file or None
    """
    try:
        fig = _new_figure(CHART["width_in"], 4.0)
        
        # Panel 1: Concrete Volume
        ax1 = fig.add_subplot(121)
        bars1 = ax1.bar([0], [concrete_vol], color=CHART["pass_color"], 
                       edgecolor='black', linewidth=0.5, width=0.5)
        ax1.text(0, concrete_vol + concrete_vol * 0.05, f"{concrete_vol:.2f}",
                ha='center', va='bottom', fontsize=CHART["font_pt"])
        ax1.set_xticks([0])
        ax1.set_xticklabels(["Deck Slab"], fontsize=CHART["font_pt"])
        ax1.set_ylabel("Volume (m³)", fontsize=CHART["font_pt"])
        ax1.set_title("Concrete Volume", fontsize=CHART["font_pt"] + 1, fontweight='bold', pad=8)
        ax1.grid(axis='y', alpha=0.3, linestyle=':', linewidth=0.5)
        
        # Adjust y-axis upper limit so value label is not clipped
        y1_max = concrete_vol * 1.18 if concrete_vol > 0 else 1.0
        ax1.set_ylim(0, y1_max)
        
        # Panel 2: Reinforcement Weight
        ax2 = fig.add_subplot(122)
        bars2 = ax2.bar([0], [rebar_wt], color=CHART["pass_color"], 
                       edgecolor='black', linewidth=0.5, width=0.5)
        ax2.text(0, rebar_wt + rebar_wt * 0.05, f"{rebar_wt:.2f}",
                ha='center', va='bottom', fontsize=CHART["font_pt"])
        ax2.set_xticks([0])
        ax2.set_xticklabels(["Deck Slab"], fontsize=CHART["font_pt"])
        ax2.set_ylabel("Weight (MT)", fontsize=CHART["font_pt"])
        ax2.set_title("Reinforcement Steel", fontsize=CHART["font_pt"] + 1, fontweight='bold', pad=8)
        ax2.grid(axis='y', alpha=0.3, linestyle=':', linewidth=0.5)
        
        # Adjust y-axis upper limit so value label is not clipped
        y2_max = rebar_wt * 1.18 if rebar_wt > 0 else 1.0
        ax2.set_ylim(0, y2_max)
        
        # Optional: Add rebar intensity as subtitle
        if concrete_vol > 0:
            intensity = (rebar_wt * 1000.0) / concrete_vol  # kg/m³
            fig.suptitle(f"Concrete Deck Materials (Rebar intensity: {intensity:.1f} kg/m³)",
                        fontsize=9, fontweight='bold')
        else:
            fig.suptitle("Concrete Deck Materials", fontsize=9, fontweight='bold')
        
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "concrete_rebar.png")
        _save_figure(fig, out_path)
        
        logger.info(f"Concrete/rebar chart saved to {out_path}")
        return out_path
        
    except Exception as e:
        logger.error(f"Error in _render_concrete_rebar_chart: {e}", exc_info=True)
        return None
