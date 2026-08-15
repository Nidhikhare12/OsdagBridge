# =============================================================================
# OsdagBridge — Centralized Report Formatting & Style System (styles.py)
# Single source of truth for LaTeX document layout, geometries, color palettes,
# table styles, cell paddings, and matplotlib figure themes.
# =============================================================================

import os
import shutil
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend forced before pyplot imports
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Any

# ── Document Geometry & Margins ──────────────────────────────────────────────
# Margins and header/footer separations designed to eliminate text/row overlap
# into header and footer boxes across multi-page chapters.
DOCUMENT_GEOMETRY = {
    'paper': 'a4paper',
    'top': '1.0in',
    'bottom': '1.2in',
    'left': '1.0in',
    'right': '1.0in',
    'headheight': '15pt',
    'headsep': '18pt',
    'footskip': '35pt',
}

# ── Color Palette ─────────────────────────────────────────────────────────────
COLOR_PALETTE = {
    'osdagGreen': '#91B014',         # Primary brand color
    'osdagGreenDark': '#6F870F',     # Dark shade for headings
    'tableHeaderBg': '#EBF2D4',      # Soft green table header fill
    'tableAltRow': '#F5F8E8',        # Subtle zebra striping row background
    'passGreen': '#2E7D32',          # Pass status indicator
    'failRed': '#C62828',            # Fail status indicator
    'thresholdRed': '#D32F2F',       # Dashed threshold reference line (UR=1.0)
    'chartSteel': '#2B5C8F',         # Steel structural tonnage bar
    'chartConcrete': '#4CAF50',      # Concrete volume bar
    'chartRebar': '#FF9800',         # Reinforcement steel bar
    'textDark': '#222222',           # Body text
    'gridGray': '#E0E0E0',           # Chart grid lines
}

# ── Table Layout & Spacing Configuration ─────────────────────────────────────
TABLE_CONFIG = {
    'arraystretch': 1.15,
    'tabcolsep': '6pt',
    'LTpre': '8pt',
    'LTpost': '12pt',
}

def cleanup_assets(report_dir: str):
    """Purge old generated chart image assets (*.png) before each compilation run."""
    assets_dir = os.path.join(report_dir, "assets")
    if os.path.exists(assets_dir):
        for fname in os.listdir(assets_dir):
            if fname.endswith(".png") and ("chart" in fname or "summary" in fname or "takeoff" in fname):
                try:
                    os.remove(os.path.join(assets_dir, fname))
                except Exception:
                    pass

def colorize_ur_cell(ur_value: Any) -> str:
    """Format and colorize Utilization Ratio cell in LaTeX tables."""
    try:
        ur = float(ur_value)
        ur_str = f"{ur:.3f}"
        if ur > 1.0:
            return f"\\cellcolor[HTML]{{C62828}}{{\\color{{white}}\\textbf{{{ur_str}}}}}"
        else:
            return f"\\cellcolor[HTML]{{2E7D32}}{{\\color{{white}}\\textbf{{{ur_str}}}}}"
    except (ValueError, TypeError):
        return str(ur_value) if ur_value is not None else "N/A"

def apply_matplotlib_style():
    """Apply global dark/light modern clean theme to matplotlib plots."""
    plt.rcParams.update({
        'font.sans-serif': ['DejaVu Sans', 'Helvetica', 'Arial', 'sans-serif'],
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 13,
        'axes.edgecolor': '#CCCCCC',
        'axes.linewidth': 0.8,
        'grid.color': COLOR_PALETTE['gridGray'],
        'grid.linestyle': '--',
        'grid.alpha': 0.7,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'figure.autolayout': True,
    })

def make_longtable_header(caption: str, headers: List[str], col_spec: str, label: Optional[str] = None) -> str:
    """
    Generate LaTeX longtable start code with repeated header block across page breaks.
    Includes \\endfirsthead, \\endhead, \\endfoot, and \\endlastfoot rules to prevent text bleed.
    Also includes \\needspace to protect page bottom boundaries and caption safety.
    """
    lbl_str = f"\\label{{{label}}}" if label else ""
    header_row = " & ".join([f"\\textbf{{{h}}}" for h in headers]) + r" \\" + "\n"
    
    return f"""\\needspace{{4\\baselineskip}}
\\rowcolors{{2}}{{white}}{{tableAltRow}}
\\begin{{longtable}}{{{col_spec}}}
\\caption{{\\textbf{{{caption}}}}} {lbl_str} \\\\
\\hline
\\rowcolor[HTML]{{EBF2D4}} {header_row}\\hline
\\endfirsthead
\\caption*{{\\textbf{{{caption}}} --- Continued}} \\\\
\\hline
\\rowcolor[HTML]{{EBF2D4}} {header_row}\\hline
\\endhead
\\hline
\\endfoot
\\hline
\\endlastfoot
"""

def get_latex_style_preamble() -> str:
    """Return LaTeX code defining custom column types, colors, fancyhdr, and preamble rules."""
    return f"""
% Centralized OsdagBridge Style Definitions (from styles.py)
\\usepackage{{lmodern}}
\\usepackage{{needspace}}
\\usepackage{{subcaption}}
\\usepackage[table,xcdraw]{{xcolor}}
\\definecolor{{osdagGreen}}{{HTML}}{{{COLOR_PALETTE['osdagGreen'].replace('#', '')}}}
\\definecolor{{osdagGreenDark}}{{HTML}}{{{COLOR_PALETTE['osdagGreenDark'].replace('#', '')}}}
\\definecolor{{tableHeaderBg}}{{HTML}}{{{COLOR_PALETTE['tableHeaderBg'].replace('#', '')}}}
\\definecolor{{tableAltRow}}{{HTML}}{{{COLOR_PALETTE['tableAltRow'].replace('#', '')}}}
\\definecolor{{passGreen}}{{HTML}}{{{COLOR_PALETTE['passGreen'].replace('#', '')}}}
\\definecolor{{failRed}}{{HTML}}{{{COLOR_PALETTE['failRed'].replace('#', '')}}}

% Section heading styling with Osdag green
\\usepackage{{titlesec}}
\\titleformat{{\\chapter}}[display]
  {{\\normalfont\\huge\\bfseries\\color{{osdagGreenDark}}}}{{\\chaptertitlename\\ \\thechapter}}{{20pt}}{{\\Huge}}
\\titleformat{{\\section}}
  {{\\normalfont\\Large\\bfseries\\color{{osdagGreen}}}}{{\\thesection}}{{1em}}{{}}
\\titleformat{{\\subsection}}
  {{\\normalfont\\large\\bfseries\\color{{osdagGreenDark}}}}{{\\thesubsection}}{{1em}}{{}}

% Table spacing rules & row height
\\setlength{{\\tabcolsep}}{{{TABLE_CONFIG['tabcolsep']}}}
\\renewcommand{{\\arraystretch}}{{{TABLE_CONFIG['arraystretch']}}}
\\setlength{{\\LTpre}}{{{TABLE_CONFIG['LTpre']}}}
\\setlength{{\\LTpost}}{{{TABLE_CONFIG['LTpost']}}}
\\setlength{{\\LTcapwidth}}{{\\textwidth}}

% Header & Footer Theming
\\usepackage{{fancyhdr}}
\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[L]{{\\small\\nouppercase{{\\leftmark}}}}
\\fancyhead[R]{{\\small\\nouppercase{{\\rightmark}}}}
\\fancyfoot[C]{{\\thepage}}
\\renewcommand{{\\headrulewidth}}{{0.4pt}}
\\renewcommand{{\\footrulewidth}}{{0.4pt}}
\\colorlet{{headrulecolor}}{{osdagGreen}}
\\colorlet{{footrulecolor}}{{osdagGreen}}

% Custom Column Types with Fixed Width & Alignment
\\newcolumntype{{L}}[1]{{>{{{r"\\raggedright\\arraybackslash"}}}p{{#1}}}}
\\newcolumntype{{C}}[1]{{>{{{r"\\centering\\arraybackslash"}}}p{{#1}}}}
\\newcolumntype{{R}}[1]{{>{{{r"\\raggedleft\\arraybackslash"}}}p{{#1}}}}

% Prevent row bleed into footer box
\\raggedbottom
"""
