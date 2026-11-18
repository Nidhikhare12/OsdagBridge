"""
Centralized styling definitions and LaTeX helpers for OsdagBridge reports.

Provides consistent document geometry, color definitions, table parameters,
and longtable header builders across all report chapters.
"""

from typing import Optional, List, Dict, Any

# =============================================================================
# 1. COLOR PALETTE (Hex Codes & Semantic Roles)
# =============================================================================
# Canonical Osdag Green Brand
COLOR_OSDAG_GREEN       = "#91B014"

# Neutral Document Tones
COLOR_PRIMARY_TEXT      = "#1F2937"  # Deep Charcoal for text
COLOR_SECONDARY_TEXT    = "#4B5563"  # Muted Slate for subtitles/notes
COLOR_TABLE_HEADER_BG   = "#F1F5F9"  # Soft slate-gray for table headers
COLOR_TABLE_ROW_ALT     = "#F8FAFC"  # Light tint for zebra striping
COLOR_TABLE_BORDER      = "#CBD5E1"  # Crisp boundary border

# Engineering Status Indicators
COLOR_PASS              = "#15803D"  # Professional forest green (Pass <= 1.0)
COLOR_WARN              = "#B45309"  # Amber warning (0.90 <= UR < 1.0)
COLOR_FAIL              = "#B91C1C"  # Clear crimson (Fail > 1.0)
COLOR_THRESHOLD_LINE    = "#DC2626"  # Dashed threshold limit line (UR = 1.0)

# Chart & Material Take-off Palettes
COLOR_STEEL_GIRDER      = "#1E40AF"  # Deep Royal Blue
COLOR_STEEL_BRACING     = "#3B82F6"  # Vivid Blue
COLOR_STEEL_DIAPHRAGM   = "#60A5FA"  # Sky Blue
COLOR_CONCRETE_VOLUME   = "#475569"  # Slate Concrete Gray
COLOR_REBAR_WEIGHT      = "#EA580C"  # Vibrant Steel-Orange
COLOR_GRID              = "#E2E8F0"  # Subtle chart gridline

# =============================================================================
# 2. DOCUMENT GEOMETRY & MARGIN CONSTRAINTS
# =============================================================================
# Ensures 14mm footskip to prevent table rows from bleeding into the footer rule.
GEOMETRY_OPTIONS = (
    "a4paper, "
    "top=25mm, "
    "bottom=28mm, "
    "left=20mm, "
    "right=20mm, "
    "headheight=15mm, "
    "headsep=7mm, "
    "footskip=14mm"
)

# Vertical Spacing Metrics
TABLE_COL_SEP           = "6pt"
TABLE_ARRAY_STRETCH     = "1.12"
TABLE_EXTRA_ROW_HEIGHT  = "0.8pt"
TABLE_RULE_WIDTH        = "0.5pt"
TABLE_LT_PRE_SKIP       = "2pt"
TABLE_LT_POST_SKIP      = "6pt"
NEEDSPACE_THRESHOLD     = "5\\baselineskip"

# =============================================================================
# 3. LATEX PREAMBLE DEFINITIONS & MACROS
# =============================================================================
def get_latex_color_definitions() -> str:
    """Returns LaTeX \\definecolor statements for all brand and semantic colors."""
    return r"""
\definecolor{osdagGreen}{HTML}{91B014}
\definecolor{headerBg}{HTML}{F1F5F9}
\definecolor{rowAlt}{HTML}{F8FAFC}
\definecolor{tableBorder}{HTML}{CBD5E1}
\definecolor{statusPass}{HTML}{15803D}
\definecolor{statusWarn}{HTML}{B45309}
\definecolor{statusFail}{HTML}{B91C1C}
\definecolor{thresholdRed}{HTML}{DC2626}
"""

def get_table_environment_settings() -> str:
    """Returns LaTeX settings for table spacing, row height, and buffer controls."""
    return f"""
% Centralized Table Layout & Buffer Controls
\\setlength{{\\tabcolsep}}{{{TABLE_COL_SEP}}}
\\renewcommand{{\\arraystretch}}{{{TABLE_ARRAY_STRETCH}}}
\\setlength{{\\extrarowheight}}{{{TABLE_EXTRA_ROW_HEIGHT}}}
\\setlength{{\\arrayrulewidth}}{{{TABLE_RULE_WIDTH}}}
\\setlength{{\\LTpre}}{{{TABLE_LT_PRE_SKIP}}}
\\setlength{{\\LTpost}}{{{TABLE_LT_POST_SKIP}}}

% Page-bottom Threshold Buffers (prevent footer bleeding)
\\BeforeBeginEnvironment{{table}}{{\\needspace{{{NEEDSPACE_THRESHOLD}}}}}
\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{NEEDSPACE_THRESHOLD}}}}}
"""

def get_column_types() -> str:
    """Returns definitions for custom aligned column types L, C, R."""
    return r"""
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}
"""

def get_header_footer_styles(project_name: str, job_number: str, report_date: str, report_version: str = "Rev 0") -> str:
    """
    Builds clean, collision-free fancyhdr page styles.
    Eliminates negative vertical shifts that caused footer text to overlap table rows.
    """
    return f"""
\\fancypagestyle{{main}}{{
  \\fancyhf{{}}
  \\fancyhead[L]{{\\parbox[b]{{0.52\\headwidth}}{{\\raggedright\\footnotesize {project_name} $|$ {job_number}}}}}
  \\fancyhead[R]{{\\parbox[b]{{0.45\\headwidth}}{{\\raggedleft\\footnotesize {report_date} $|$ {report_version}}}}}
  \\fancyfoot[L]{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \\fancyfoot[R]{{Page \\thepage\\ of \\pageref{{LastPage}}}}
  \\renewcommand{{\\headrule}}{{\\color{{osdagGreen}}\\hrule width\\headwidth height 1pt \\vspace{{2pt}}}}
  \\renewcommand{{\\footrule}}{{%
    \\ifbool{{hasSDonPage}}{{%
      \\hbox to \\headwidth{{\\textcolor{{black}}{{\\footnotesize\\textit{{* Software default value}}}}\\hfil}}%
      \\vspace{{2pt}}%
    }}{{%
      \\vspace{{0pt}}%
    }}%
    \\color{{osdagGreen}}\\hrule width\\headwidth height 1pt \\vspace{{4pt}}%
  }}
}}

\\fancypagestyle{{plain}}{{
  \\fancyhf{{}}
  \\fancyhead[L]{{\\parbox[b]{{0.52\\headwidth}}{{\\raggedright\\footnotesize {project_name} $|$ {job_number}}}}}
  \\fancyhead[R]{{\\parbox[b]{{0.45\\headwidth}}{{\\raggedleft\\footnotesize {report_date} $|$ {report_version}}}}}
  \\fancyfoot[L]{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \\fancyfoot[R]{{Page \\thepage\\ of \\pageref{{LastPage}}}}
  \\renewcommand{{\\headrule}}{{\\color{{osdagGreen}}\\hrule width\\headwidth height 1pt \\vspace{{2pt}}}}
  \\renewcommand{{\\footrule}}{{%
    \\ifbool{{hasSDonPage}}{{%
      \\hbox to \\headwidth{{\\textcolor{{black}}{{\\footnotesize\\textit{{* Software default value}}}}\\hfil}}%
      \\vspace{{2pt}}%
    }}{{%
      \\vspace{{0pt}}%
    }}%
    \\color{{osdagGreen}}\\hrule width\\headwidth height 1pt \\vspace{{4pt}}%
  }}
}}

\\fancypagestyle{{firstpage}}{{
  \\fancyhf{{}}
  \\renewcommand{{\\headrulewidth}}{{0pt}}
  \\fancyfoot[L]{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \\fancyfoot[R]{{Page \\thepage\\ of \\pageref{{LastPage}}}}
  \\renewcommand{{\\footrule}}{{\\color{{osdagGreen}}\\hrule width\\headwidth height 1pt \\vspace{{4pt}}}}
}}
"""

# =============================================================================
# 4. REPEATED LONGTABLE BUILDER HELPER
# =============================================================================
def build_longtable_header(
    caption: str,
    label: str,
    header_rows: str,
    col_count: int,
    continue_caption: Optional[str] = None
) -> str:
    """
    Generates standard, robust LaTeX LongTable header blocks with:
    - \\endfirsthead (initial header with caption)
    - \\endhead (repeated header on all subsequent pages with continuation title)
    - \\endfoot (continuation notice at page bottom)
    - \\endlastfoot (final table bottom rule)
    """
    cont_text = continue_caption or f"{caption} (Continued)"
    # Strip any trailing newlines or hlines from header_rows to normalize
    clean_headers = header_rows.strip()
    if not clean_headers.endswith(r"\hline"):
        clean_headers += r" \\[6pt]" + "\n" + r"\hline"

    return (
        f"\\caption{{\\textbf{{{caption}}}}} \\label{{{label}}} \\\\\n"
        r"\hline" + "\n"
        f"{clean_headers}\n"
        r"\endfirsthead" + "\n\n"
        f"\\multicolumn{{{col_count}}}{{c}}{{\\small\\textit{{{cont_text}}}}} \\\\[4pt]\n"
        r"\hline" + "\n"
        f"{clean_headers}\n"
        r"\endhead" + "\n\n"
        r"\hline" + "\n"
        f"\\multicolumn{{{col_count}}}{{r}}{{\\small\\textit{{Continued on next page...}}}} \\\\\n"
        r"\endfoot" + "\n\n"
        r"\hline" + "\n"
        r"\endlastfoot"
    )

# =============================================================================
# 5. STATUS BADGE RENDERING
# =============================================================================
def render_ur_badge(ur_val: Any, threshold: float = 1.0) -> str:
    """Render a LaTeX color-coded Utilization Ratio value."""
    try:
        f = float(ur_val)
    except (TypeError, ValueError):
        return str(ur_val) if ur_val not in (None, "") else "---"
    
    val_str = f"{f:.2f}"
    if f > threshold:
        return f"\\textcolor{{statusFail}}{{\\textbf{{{val_str}}}}}"
    elif f >= 0.90:
        return f"\\textcolor{{statusWarn}}{{\\textbf{{{val_str}}}}}"
    else:
        return f"\\textcolor{{statusPass}}{{{val_str}}}"

def render_status_text(status: str) -> str:
    """Render a standard PASS / WARN / FAIL status badge."""
    s = str(status).strip().upper()
    if "FAIL" in s:
        return r"\textcolor{statusFail}{\textbf{FAIL}}"
    elif "WARN" in s:
        return r"\textcolor{statusWarn}{\textbf{WARN}}"
    elif "PASS" in s or "OK" in s:
        return r"\textcolor{statusPass}{\textbf{PASS}}"
    return status
