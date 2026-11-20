"""
styles.py - Centralized Styling & Theme System for OsdagBridge Reports
Single Source of Truth for visual styles, geometry, colors, table parameters,
header/footer metrics, and plot palettes across the LaTeX report generation subsystem.
"""

from typing import Dict, Any

# =============================================================================
# COLOR PALETTE
# =============================================================================
COLORS = {
    "osdag_green": "#91B014",       # Brand Green
    "osdag_dark_green": "#6E870D",  # Accent Green
    "border_gray": "#D3D3D3",       # Light gray borders
    "table_header_bg": "#F5F7FA",   # Table header background
    "pass_green": "#2E7D32",        # Status PASS color
    "fail_red": "#C62828",          # Status FAIL / Warning color
    "threshold_red": "#D32F2F",     # Red dashed line for UR=1.0
    "bar_girder": "#1976D2",        # Blue for girders
    "bar_deck": "#388E3C",          # Green for concrete deck
    "bar_bracing": "#F57C00",       # Orange for cross bracing
    "bar_diaphragm": "#7B1FA2",     # Purple for end diaphragms
    "bar_steel": "#455A64",         # Blue Grey for structural steel
    "bar_rebar": "#D32F2F",         # Dark red for rebar
    "text_dark": "#212121",         # Dark body text
}

# =============================================================================
# DOCUMENT GEOMETRY & SPACING (LaTeX)
# =============================================================================
GEOMETRY = {
    "paper": "a4paper",
    "top": "2.2cm",
    "bottom": "2.6cm",       # Safe bottom margin preventing footer overlap
    "left": "2.0cm",
    "right": "2.0cm",
    "headheight": "18pt",    # Resolves fancyhdr \headheight warning (min 17.5pt)
    "headsep": "14pt",
    "footskip": "28pt",      # Adequate buffer between table bottom and footer
}

# =============================================================================
# TABLE STYLING DEFAULTS
# =============================================================================
TABLE_STYLE = {
    "tabcolsep": "5.5pt",           # Horizontal padding inside cells
    "arraystretch": 1.15,           # Vertical row height factor
    "arrayrulewidth": "0.5pt",      # Rule line width
    "extrarowheight": "0.6pt",      # Additional row height
    "lt_pre_skip": "4pt",           # Pre-skip before longtable
    "lt_post_skip": "8pt",          # Post-skip after longtable
    "needspace_lines": "5\\baselineskip",  # Page break buffer before table
}

# =============================================================================
# PLOT STYLING (Matplotlib)
# =============================================================================
PLOT_STYLE = {
    "figure_figsize": (8.5, 4.2),
    "dpi": 300,
    "font_family": "sans-serif",
    "font_size": 9,
    "title_size": 11,
    "label_size": 9.5,
    "tick_size": 8.5,
    "grid_alpha": 0.4,
    "bar_width": 0.55,
    "threshold_line_style": "--",
    "threshold_line_width": 1.75,
}

# =============================================================================
# HELPER FUNCTIONS TO EMIT LATEX PREAMBLE FRAGMENTS
# =============================================================================
def get_latex_geometry_options() -> str:
    """Return geometry package options string."""
    return (
        f"{GEOMETRY['paper']}, "
        f"top={GEOMETRY['top']}, "
        f"bottom={GEOMETRY['bottom']}, "
        f"left={GEOMETRY['left']}, "
        f"right={GEOMETRY['right']}, "
        f"headheight={GEOMETRY['headheight']}, "
        f"headsep={GEOMETRY['headsep']}, "
        f"footskip={GEOMETRY['footskip']}"
    )

def get_table_spacing_latex() -> str:
    """Return LaTeX macro settings for table spacing."""
    return f"""% Table layout and spacing from styles.py
\\setlength{{\\tabcolsep}}{{{TABLE_STYLE['tabcolsep']}}}
\\renewcommand{{\\arraystretch}}{{{TABLE_STYLE['arraystretch']}}}
\\setlength{{\\LTpre}}{{{TABLE_STYLE['lt_pre_skip']}}}
\\setlength{{\\LTpost}}{{{TABLE_STYLE['lt_post_skip']}}}
\\setlength{{\\arrayrulewidth}}{{{TABLE_STYLE['arrayrulewidth']}}}
\\setlength{{\\extrarowheight}}{{{TABLE_STYLE['extrarowheight']}}}

% Prevent tables from overflowing into footers
\\BeforeBeginEnvironment{{table}}{{\\needspace{{{TABLE_STYLE['needspace_lines']}}}}}
\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{TABLE_STYLE['needspace_lines']}}}}}
"""
