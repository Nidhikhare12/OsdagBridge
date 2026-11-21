"""
OsdagBridge Report Generator — Centralized Formatting & Style System
Single Source of Truth for document layout, color palettes, typography,
table metrics, footer margins, and plot visualization styling.
"""

import re
from dataclasses import dataclass
from typing import Dict, Any, Tuple

# =============================================================================
# 1. COLOR PALETTES
# =============================================================================

# Brand and Theme Colors (Hex and RGB)
COLOR_OSDAG_GREEN = "#91B014"
COLOR_PRIMARY_NAVY = "#1F2D3D"
COLOR_SECONDARY_BLUE = "#2B6CB0"
COLOR_ACCENT_BLUE = "#0078D4"

# Table Colors
COLOR_TABLE_HEADER_BG = "#2B4C7E"       # Deep blue header for professional reports
COLOR_TABLE_HEADER_FG = "#FFFFFF"       # White text on header
COLOR_TABLE_ALT_ROW = "#F4F7FB"         # Very soft blue-grey for alternating rows
COLOR_TABLE_BORDER = "#B0BEC5"          # Crisp neutral border
COLOR_TABLE_HIGHLIGHT = "#E8F4FD"       # Highlighted cell background

# Status & Check Colors
COLOR_PASS_GREEN = "#2E7D32"            # UR <= 1.0
COLOR_FAIL_RED = "#D32F2F"              # UR > 1.0 (Limit exceeded)
COLOR_WARN_ORANGE = "#ED8936"           # High utilization warning

# Material Visualization Colors
COLOR_STEEL_GIRDER = "#2B6CB0"          # Steel plate girders
COLOR_STEEL_BRACING = "#4299E1"         # Cross bracing
COLOR_STEEL_DIAPHRAGM = "#63B3ED"       # End diaphragm
COLOR_CONCRETE = "#718096"              # Concrete volume
COLOR_REBAR = "#DD6B20"                 # Rebar steel weight

# Centralized Color Registry for LaTeX Preambles
LATEX_COLORS: Dict[str, str] = {
    "osdagGreen": COLOR_OSDAG_GREEN.lstrip("#"),
    "tableHeaderBg": COLOR_TABLE_HEADER_BG.lstrip("#"),
    "tableHeaderFg": COLOR_TABLE_HEADER_FG.lstrip("#"),
    "tableAltRow": COLOR_TABLE_ALT_ROW.lstrip("#"),
    "tableBorder": COLOR_TABLE_BORDER.lstrip("#"),
    "passGreen": COLOR_PASS_GREEN.lstrip("#"),
    "failRed": COLOR_FAIL_RED.lstrip("#"),
    "warnOrange": COLOR_WARN_ORANGE.lstrip("#"),
    "steelGirder": COLOR_STEEL_GIRDER.lstrip("#"),
    "concreteDeck": COLOR_CONCRETE.lstrip("#"),
    "rebarDeck": COLOR_REBAR.lstrip("#"),
}

# =============================================================================
# 2. PAGE GEOMETRY & MARGINS (FOOTER BLEED PREVENTION)
# =============================================================================

PAGE_GEOMETRY = {
    "paper": "a4paper",
    "top": "25mm",
    "bottom": "30mm",          # Generous bottom margin to strictly prevent footer overlap
    "left": "20mm",
    "right": "20mm",
    "headheight": "16pt",
    "headsep": "7mm",
    "footskip": "14mm",         # Distance from bottom of text body to bottom of footer
}

# =============================================================================
# 3. TYPOGRAPHY & SPACING
# =============================================================================

TYPOGRAPHY = {
    "document_class": "report",
    "base_font_size": "11pt",
    "line_spacing": "1.15",
    "section_title_size": r"\large\bfseries",
    "subsection_title_size": r"\normalsize\bfseries",
    "caption_font_size": r"\small",
    "table_font_size": r"\small",
}

# =============================================================================
# 4. TABLE FORMATTING & METRICS
# =============================================================================

TABLE_STYLE = {
    "tabcolsep": "5pt",                 # Horizontal padding between columns
    "arraystretch": "1.25",             # Row height multiplier for readability
    "extrarowheight": "1.2pt",          # Extra vertical clearance above text
    "arrayrulewidth": "0.5pt",          # Rule/border line thickness
    "LTpre": "6pt",                     # LongTable pre-skip
    "LTpost": "8pt",                    # LongTable post-skip
    "needspace_before_table": r"\needspace{7\baselineskip}",  # Prevent orphaned table headers
}

# =============================================================================
# 5. MATPLOTLIB / DATA VISUALIZATION CONFIGURATION
# =============================================================================

CHART_CONFIG = {
    "dpi": 200,
    "fig_width": 7.0,                   # inches
    "fig_height": 3.8,                  # inches
    "bar_width": 0.45,
    "ur_limit": 1.0,                    # Utilization ratio threshold line
    "font_family": "sans-serif",
    "title_size": 11,
    "label_size": 9.5,
    "tick_size": 8.5,
    "grid_alpha": 0.4,
}

# =============================================================================
# 6. LATEX SNIPPET GENERATORS & HELPERS
# =============================================================================

def get_latex_color_definitions() -> str:
    """Generate LaTeX \definecolor commands for all colors in the registry."""
    lines = []
    for name, hex_code in LATEX_COLORS.items():
        lines.append(f"\\definecolor{{{name}}}{{HTML}}{{{hex_code}}}")
    return "\n".join(lines)


def get_geometry_latex() -> str:
    """Generate geometry package inclusion string."""
    geom = PAGE_GEOMETRY
    return (
        f"\\usepackage[{geom['paper']}, top={geom['top']}, bottom={geom['bottom']}, "
        f"left={geom['left']}, right={geom['right']}, headheight={geom['headheight']}, "
        f"headsep={geom['headsep']}, footskip={geom['footskip']}]{{geometry}}"
    )


def get_table_environment_settings() -> str:
    """Return LaTeX commands configuring table padding and line heights."""
    st = TABLE_STYLE
    return f"""% Centralized Table Formatting (from styles.py)
\\setlength{{\\tabcolsep}}{{{st['tabcolsep']}}}
\\renewcommand{{\\arraystretch}}{{{st['arraystretch']}}}
\\setlength{{\\extrarowheight}}{{{st['extrarowheight']}}}
\\setlength{{\\arrayrulewidth}}{{{st['arrayrulewidth']}}}
\\setlength{{\\LTpre}}{{{st['LTpre']}}}
\\setlength{{\\LTpost}}{{{st['LTpost']}}}
\\setlength{{\\LTleft}}{{\\fill}}
\\setlength{{\\LTright}}{{\\fill}}
\\BeforeBeginEnvironment{{table}}{{{st['needspace_before_table']}}}
\\BeforeBeginEnvironment{{longtable}}{{{st['needspace_before_table']}}}
"""


def format_table_header(headers: list, col_spec: str = None) -> Tuple[str, str]:
    """
    Generate LaTeX longtable header block with \\endfirsthead and \\endhead.
    Guarantees repeated headers on subsequent pages across page transitions.
    """
    n_cols = len(headers)
    header_cells = " & ".join([f"\\textbf{{{h}}}" for h in headers])
    header_row = f"\\rowcolor{{tableHeaderBg}} " + " & ".join(
        [f"\\textcolor{{white}}{{\\textbf{{{h}}}}}" for h in headers]
    ) + r" \\[6pt]"

    first_head = f"""\\hline
{header_row}
\\hline
\\endfirsthead
"""
    cont_head = f"""\\hline
\\multicolumn{{{n_cols}}}{{c}}{{\\textit{{\\small(Table continued from previous page)}}}} \\\\[4pt]
\\hline
{header_row}
\\hline
\\endhead
"""
    foot = f"""\\hline
\\multicolumn{{{n_cols}}}{{r}}{{\\textit{{\\footnotesize Continued on next page\\ldots}}}} \\\\[4pt]
\\endfoot
"""
    last_foot = f"""\\hline
\\endlastfoot
"""
    return first_head + cont_head + foot + last_foot


def post_process_longtables(tex: str) -> str:
    """
    Scans the compiled LaTeX string for any \\begin{longtable} environments.
    For any longtable lacking an \\endhead directive, automatically structures it
    with standard repeating headers and continuation cues across page transitions:
      - \\endfirsthead: Initial header with tableHeaderBg
      - \\endhead: Repeated header on subsequent pages with '(Table continued from previous page)'
      - \\endfoot: 'Continued on next page...'
      - \\endlastfoot: Bottom border rule
    Guarantees compliance across all tables in every chapter.
    """
    def enhance_table(match: re.Match) -> str:
        table_text = match.group(0)
        if r"\endhead" in table_text:
            return table_text  # Already configured

        # Match \begin{longtable}{spec} ... \hline (header_row) \\ \hline
        m = re.search(
            r"(\\begin\{longtable\}\{[^}]+\}\s*)(.*?)(\\hline\s*\n\s*(.*?)\s*\\\\\s*(?:\[[^\]]*\])?\s*\n\s*\\hline)",
            table_text,
            re.DOTALL
        )
        if not m:
            return table_text

        begin_tag = m.group(1)
        caption_part = m.group(2).strip()
        header_content = m.group(4).strip()

        ncols = len(header_content.split('&'))

        # Apply header styling if not already styled
        if r"\rowcolor" in header_content:
            styled_header = header_content + r" \\[6pt]"
        else:
            styled_header = f"\\rowcolor{{tableHeaderBg}} {header_content} \\\\[6pt]"

        caption_line = ""
        if caption_part:
            if not caption_part.endswith(r"\\"):
                caption_line = caption_part + r" \\" + "\n"
            else:
                caption_line = caption_part + "\n"

        header_block = (
            begin_tag + "\n" +
            caption_line +
            r"\hline" + "\n" +
            styled_header + "\n" +
            r"\hline" + "\n" +
            r"\endfirsthead" + "\n" +
            r"\hline" + "\n" +
            f"\\multicolumn{{{ncols}}}{{c}}{{\\textit{{\\small(Table continued from previous page)}}}} \\\\[4pt]\n" +
            r"\hline" + "\n" +
            styled_header + "\n" +
            r"\hline" + "\n" +
            r"\endhead" + "\n" +
            r"\hline" + "\n" +
            f"\\multicolumn{{{ncols}}}{{r}}{{\\textit{{\\footnotesize Continued on next page\\ldots}}}} \\\\[4pt]\n" +
            r"\endfoot" + "\n" +
            r"\hline" + "\n" +
            r"\endlastfoot\n"
        )

        rest = table_text[m.end():]
        return header_block + rest

    return re.sub(r"\\begin\{longtable\}.*?\\end\{longtable\}", enhance_table, tex, flags=re.DOTALL)

