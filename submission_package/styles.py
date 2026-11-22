# =============================================================================
# OsdagBridge — Centralized Report Styling & Formatting System (styles.py)
# Single Source of Truth for Layout Rules, Colors, Table Formats, and Spacing.
# =============================================================================

from typing import List, Optional

# --- 1. Global Document Geometry & Page Setup ---
PAGE_GEOMETRY = {
    "paper": "a4paper",
    "top": "25mm",
    "bottom": "30mm",      # Ample clearance preventing table bleed into footer
    "left": "20mm",
    "right": "20mm",
    "headheight": "15pt",
    "headsep": "10pt",
    "footskip": "18mm",     # Ensures 18mm separation between text body and footer
}

LINE_STRETCH = 1.15

# --- 2. Color Palette ---
COLORS = {
    "primary": "#91B014",         # Osdag Brand Green
    "secondary": "#2A4B7C",       # Deep Bridge Blue
    "accent": "#4A7C59",          # Muted Green
    "dark_text": "#1F2937",       # Charcoal Slate for high readability
    "pass": "#16A34A",            # Verified Check Green
    "fail": "#DC2626",            # Safety Margin Violation Red
    "warning": "#D97706",         # Warning Amber
    "grid": "#E5E7EB",            # Subtle plot and table gridline
    "card_bg": "#F9FAFB",         # Light card background
}

# LaTeX Color Definitions
TEX_COLOR_DEFS = r"""
\definecolor{osdagGreen}{HTML}{91B014}
\definecolor{osdagBlue}{HTML}{2A4B7C}
\definecolor{osdagPass}{HTML}{16A34A}
\definecolor{osdagFail}{HTML}{DC2626}
\definecolor{osdagWarning}{HTML}{D97706}
\definecolor{osdagSlate}{HTML}{1F2937}
"""

# --- 3. Table Layout Parameters ---
TABLE_LAYOUT = {
    "tabcolsep": "5.5pt",         # Horizontal cell padding
    "arraystretch": 1.15,         # Vertical row stretch
    "arrayrulewidth": "0.5pt",    # Table outline thickness
    "extrarowheight": "0.8pt",    # Extra cell height to prevent ascender collision
    "lt_pre": "0pt",              # Space before longtable
    "lt_post": "6pt",             # Space after longtable
    "page_break_threshold": "6",  # \Needspace threshold in baselineskips
}


def get_geometry_tex() -> str:
    """Return LaTeX \\geometry command from centralized settings."""
    g = PAGE_GEOMETRY
    return (
        f"\\usepackage[{g['paper']}, top={g['top']}, bottom={g['bottom']}, "
        f"left={g['left']}, right={g['right']}, headheight={g['headheight']}, "
        f"headsep={g['headsep']}, footskip={g['footskip']}]{{geometry}}"
    )


def get_table_setup_tex() -> str:
    """Return table formatting instructions for LaTeX preamble."""
    t = TABLE_LAYOUT
    return (
        f"\\setlength{{\\tabcolsep}}{{{t['tabcolsep']}}}\n"
        f"\\renewcommand{{\\arraystretch}}{{{t['arraystretch']}}}\n"
        f"\\setlength{{\\LTpre}}{{{t['lt_pre']}}}\n"
        f"\\setlength{{\\LTpost}}{{{t['lt_post']}}}\n"
        f"\\setlength{{\\arrayrulewidth}}{{{t['arrayrulewidth']}}}\n"
        f"\\setlength{{\\extrarowheight}}{{{t['extrarowheight']}}}\n"
        f"\\BeforeBeginEnvironment{{table}}{{\\needspace{{{t['page_break_threshold']}\\baselineskip}}}}\n"
        f"\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{t['page_break_threshold']}\\baselineskip}}}}"
    )


# --- 4. Reusable Repeated Table Header Generator (Requirement 1) ---
def build_longtable_header(
    caption: str,
    col_spec: str,
    headers: List[str],
    label: str = "",
    n_cols: Optional[int] = None,
) -> str:
    """
    Construct a PyLaTeX-compliant / LaTeX longtable header block with
    automatic repeated column headers across multi-page transitions.

    Includes:
      - \\caption and optional \\label on the first page
      - \\endfirsthead: First page header
      - \\endhead: Repeated header on subsequent pages with '(Continued)' banner
      - \\endfoot: Continuation notice at the bottom of split pages
      - \\endlastfoot: Clean bottom rule on final page
    """
    if n_cols is None:
        n_cols = len(headers)

    header_row = " & ".join([f"\\textbf{{{h}}}" for h in headers]) + r" \\[6pt]"
    label_tex = f"\\label{{{label}}}" if label else ""

    tex = [
        f"\\begin{{longtable}}{{{col_spec}}}",
        f"\\caption{{\\textbf{{{caption}}}}}{label_tex}\\\\",
        r"\hline",
        header_row,
        r"\hline",
        r"\endfirsthead",
        "",
        f"\\multicolumn{{{n_cols}}}{{c}}{{\\small\\itshape Table \\thetable\\ -- Continued from previous page}} \\\\[4pt]",
        r"\hline",
        header_row,
        r"\hline",
        r"\endhead",
        "",
        r"\hline",
        f"\\multicolumn{{{n_cols}}}{{r}}{{\\footnotesize\\itshape Continued on next page...}} \\\\",
        r"\hline",
        r"\endfoot",
        "",
        r"\hline",
        r"\endlastfoot",
    ]
    return "\n".join(tex)


# --- 5. Data Visualization & Matplotlib Style Consistency ---
def apply_report_chart_style(ax, title: str = "", xlabel: str = "", ylabel: str = ""):
    """
    Apply professional, publication-quality styling to a Matplotlib Axes object
    matching OsdagBridge visual branding.
    """
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color=COLORS["dark_text"])
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10, fontweight="bold", labelpad=8, color=COLORS["dark_text"])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10, fontweight="bold", labelpad=8, color=COLORS["dark_text"])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(COLORS["dark_text"])
    ax.spines["bottom"].set_color(COLORS["dark_text"])
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    ax.yaxis.grid(True, linestyle="--", alpha=0.5, color=COLORS["grid"], zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=COLORS["dark_text"], labelsize=9)
