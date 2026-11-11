# =============================================================================
# OsdagBridge — Centralized Styles and Formatting Configuration
# Single Source of Truth for LaTeX Layout Rules, Geometry, Color Palettes,
# Table Formatting, and Typography across all report generation modules.
# =============================================================================

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# ── Color Palettes (Single Source of Truth) ──────────────────────────────────
# Required Milestones Color Palette (SSOT)
NAVY_PRIMARY    = "#1A365D"
STEEL_BLUE      = "#2B6CB0"
CHARCOAL_TEXT   = "#2D3748"
ZEBRA_FILL      = "#F7FAFC"
BORDER_RULE     = "#CBD5E0"
ALERT_RED       = "#E53E3E"
SUCCESS_GREEN   = "#38A169"

# Osdag Branding Palettes (backward compatibility & Osdag theme)
OSDAG_GREEN             = "#91B014"
COLOR_PRIMARY_HEX       = "91B014"   # Osdag Green (#91B014)
COLOR_PRIMARY_DARK_HEX  = "64850C"   # Darker accent for titles and headings
COLOR_PRIMARY_LIGHT_HEX = "EBF1D5"   # Subtle tint for table headers
COLOR_ZEBRA_HEX         = "F9FAF5"   # Subtle alternating row background
COLOR_BORDER_HEX        = "B0C080"   # Table grid and rule border color
COLOR_TEXT_HEX          = "212121"   # Deep charcoal body text

# Engineering Status / Limit State Visual Colors
COLOR_PASS_HEX          = "2E7D32"   # Forest Green: Safe (UR <= 0.85)
COLOR_WARN_HEX          = "F57C00"   # Amber Orange: Critical (0.85 < UR <= 1.0)
COLOR_FAIL_HEX          = "D32F2F"   # Crimson Red: Failing / Violation (UR > 1.0)
COLOR_THRESHOLD_HEX     = "FF0000"   # Red dashed line for UR = 1.0 limit state

# Chart Palettes (Hex values for matplotlib)
CHART_PRIMARY_COLOR      = f"#{COLOR_PRIMARY_HEX}"
CHART_DARK_COLOR         = f"#{COLOR_PRIMARY_DARK_HEX}"
CHART_LIGHT_COLOR        = f"#{COLOR_PRIMARY_LIGHT_HEX}"
CHART_PASS_COLOR         = f"#{COLOR_PASS_HEX}"
CHART_WARN_COLOR         = f"#{COLOR_WARN_HEX}"
CHART_FAIL_COLOR         = f"#{COLOR_FAIL_HEX}"
CHART_THRESHOLD_COLOR    = f"#{COLOR_THRESHOLD_HEX}"
CHART_STEEL_COLORS       = ["#3949AB", "#1E88E5", "#00ACC1", "#43A047", "#7CB342"]

# ── Document Geometry Margins (A4 Specifications) ───────────────────────────
MARGIN_TOP               = "20mm"
MARGIN_BOTTOM            = "20mm"
MARGIN_LEFT              = "20mm"
MARGIN_RIGHT             = "20mm"
HEAD_HEIGHT              = "52pt"
HEADHEIGHT               = "52pt"
FOOT_SKIP                = "30pt"
FOOTSKIP                 = "30pt"
HEAD_SEP                 = "12pt"
HEADSEP                  = "12pt"

# Table Spacing & Formatting Constants
TABCOLSEP                = "6pt"
ARRAYSTRETCH             = 1.18
ARRAYRULEWIDTH           = "0.5pt"
EXTRAROWHEIGHT           = "1.0pt"
LTPRE                    = "6pt"
LTPOST                   = "6pt"

# Explicit inclusion of head and foot ensures table contents never overlap margins.
GEOMETRY_CONFIG = {
    "paper": "a4paper",
    "top": MARGIN_TOP,
    "bottom": MARGIN_BOTTOM,
    "left": MARGIN_LEFT,
    "right": MARGIN_RIGHT,
    "headheight": HEAD_HEIGHT,
    "headsep": HEAD_SEP,
    "footskip": FOOT_SKIP,
    "includehead": True,
    "includefoot": True,
}

# ── Table Layout and Spacing Parameters ────────────────────────────────────
TABLE_CONFIG = {
    "tabcolsep": TABCOLSEP,          # Column horizontal padding
    "arraystretch": ARRAYSTRETCH,    # Vertical row height multiplier
    "arrayrulewidth": ARRAYRULEWIDTH,# Table border line width
    "extrarowheight": EXTRAROWHEIGHT,# Extra vertical space per row
    "LTpre": LTPRE,                  # Space before longtable
    "LTpost": LTPOST,                # Space after longtable
    "needspace_lines": 12,            # Minimum remaining lines to begin table
}

# ── Typography & Line Spacing ──────────────────────────────────────────────
TYPOGRAPHY_CONFIG = {
    "base_font_size": "12pt",
    "line_spacing": 1.15,
}

# ── LaTeX Preamble Generator ───────────────────────────────────────────────
def get_latex_preamble(project_name: str, job_number: str, report_date: str, report_version: str = 'Rev 0') -> str:
    """
    Generate the centralized LaTeX document preamble using defined style constants.
    """
    from osdagbridge.core.reports.report_utils import _tex
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)

    return rf"""
\documentclass[{TYPOGRAPHY_CONFIG['base_font_size']},a4paper]{{report}}

% ── Geometry and Layout ─────────────────────────────────────────
\usepackage[a4paper, top={GEOMETRY_CONFIG['top']}, bottom={GEOMETRY_CONFIG['bottom']}, left={GEOMETRY_CONFIG['left']}, right={GEOMETRY_CONFIG['right']}, headheight={GEOMETRY_CONFIG['headheight']}, headsep={GEOMETRY_CONFIG['headsep']}, footskip={GEOMETRY_CONFIG['footskip']}, includehead, includefoot]{{geometry}}

% ── Core Packages ─────────────────────────────────────────────
\usepackage{{graphicx}}
\usepackage{{amsmath}}
\usepackage{{amssymb}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{tabularx}}
\usepackage{{float}}
\usepackage{{fancyhdr}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{xcolor}}
\usepackage{{setspace}}
\usepackage{{enumitem}}
\usepackage{{caption}}
\usepackage{{subcaption}}
\usepackage{{multirow}}
\usepackage{{colortbl}}
\usepackage{{longtable}}
\usepackage{{titlesec}}
\usepackage{{titletoc}}
\usepackage{{lastpage}}
\usepackage{{makecell}}
\usepackage{{etoolbox}}
\usepackage{{needspace}}
\setlength{{\emergencystretch}}{{2em}}

% ── Color Definitions ─────────────────────────────────────────
\definecolor{{osdagGreen}}{{HTML}}{{{COLOR_PRIMARY_HEX}}}
\definecolor{{osdagDarkGreen}}{{HTML}}{{{COLOR_PRIMARY_DARK_HEX}}}
\definecolor{{tableHeaderBg}}{{HTML}}{{{COLOR_PRIMARY_LIGHT_HEX}}}
\definecolor{{tableRowZebra}}{{HTML}}{{{COLOR_ZEBRA_HEX}}}
\definecolor{{tableBorder}}{{HTML}}{{{COLOR_BORDER_HEX}}}
\definecolor{{urFailRed}}{{HTML}}{{{COLOR_FAIL_HEX}}}
\definecolor{{urPassGreen}}{{HTML}}{{{COLOR_PASS_HEX}}}

% Palettes SSOT
\definecolor{{navyPrimary}}{{HTML}}{{{NAVY_PRIMARY.lstrip('#')}}}
\definecolor{{steelBlue}}{{HTML}}{{{STEEL_BLUE.lstrip('#')}}}
\definecolor{{charcoalText}}{{HTML}}{{{CHARCOAL_TEXT.lstrip('#')}}}
\definecolor{{zebraFill}}{{HTML}}{{{ZEBRA_FILL.lstrip('#')}}}
\definecolor{{borderRule}}{{HTML}}{{{BORDER_RULE.lstrip('#')}}}
\definecolor{{alertRed}}{{HTML}}{{{ALERT_RED.lstrip('#')}}}
\definecolor{{successGreen}}{{HTML}}{{{SUCCESS_GREEN.lstrip('#')}}}

% ── Caption Styling ───────────────────────────────────────────
\captionsetup{{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}}

% ── Numbering and Floats ────────────────────────────────────────
\numberwithin{{table}}{{chapter}}
\numberwithin{{figure}}{{chapter}}

% ── Centralized Table Spacing and Geometry Rules ────────────────
\setlength{{\tabcolsep}}{{{TABLE_CONFIG['tabcolsep']}}}
\renewcommand{{\arraystretch}}{{{TABLE_CONFIG['arraystretch']}}}
\setlength{{\arrayrulewidth}}{{{TABLE_CONFIG['arrayrulewidth']}}}
\setlength{{\extrarowheight}}{{{TABLE_CONFIG['extrarowheight']}}}
\setlength{{\LTpre}}{{{TABLE_CONFIG['LTpre']}}}
\setlength{{\LTpost}}{{{TABLE_CONFIG['LTpost']}}}
\setlength{{\LTleft}}{{\fill}}
\setlength{{\LTright}}{{\fill}}

% Buffer control: prevent orphan tables and margin bleed
\BeforeBeginEnvironment{{table}}{{\Needspace{{{TABLE_CONFIG['needspace_lines']}\baselineskip}}}}
\BeforeBeginEnvironment{{longtable}}{{\Needspace{{{TABLE_CONFIG['needspace_lines']}\baselineskip}}}}

% ── Running Headers and Footers ─────────────────────────────────
\fancypagestyle{{main}}{{
  \fancyhf{{}}
  \fancyhead[L]{{\parbox[b]{{0.60\headwidth}}{{\raggedright\footnotesize\textsf{{{pn} $|$ {jn}}}}}}}
  \fancyhead[R]{{\parbox[b]{{0.36\headwidth}}{{\raggedleft\footnotesize\textsf{{{rd} $|$ {rv}}}}}}}
  \fancyfoot[L]{{\footnotesize\textsf{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}}}
  \fancyfoot[R]{{\footnotesize\textsf{{Page \thepage\ of \pageref{{LastPage}}}}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \hbox to \headwidth{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}}}\hfil}}%
      \vspace{{2pt}}%
    }}{{}}%
    \color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{4pt}}%
  }}
}}

\fancypagestyle{{plain}}{{
  \fancyhf{{}}
  \fancyhead[L]{{\parbox[b]{{0.60\headwidth}}{{\raggedright\footnotesize\textsf{{{pn} $|$ {jn}}}}}}}
  \fancyhead[R]{{\parbox[b]{{0.36\headwidth}}{{\raggedleft\footnotesize\textsf{{{rd} $|$ {rv}}}}}}}
  \fancyfoot[L]{{\footnotesize\textsf{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}}}
  \fancyfoot[R]{{\footnotesize\textsf{{Page \thepage\ of \pageref{{LastPage}}}}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \hbox to \headwidth{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}}}\hfil}}%
      \vspace{{2pt}}%
    }}{{}}%
    \color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{4pt}}%
  }}
}}

\fancypagestyle{{firstpage}}{{
  \fancyhf{{}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \fancyfoot[L]{{\footnotesize\textsf{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}}}
  \fancyfoot[R]{{\footnotesize\textsf{{Page \thepage\ of \pageref{{LastPage}}}}}}
  \renewcommand{{\footrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{4pt}}}}
}}

\pagestyle{{main}}
\setstretch{{{TYPOGRAPHY_CONFIG['line_spacing']}}}

% ── Custom Column Definitions ─────────────────────────────────
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\newcolumntype{{C}}[1]{{>{{\centering\arraybackslash}}p{{#1}}}}
\newcolumntype{{R}}[1]{{>{{\raggedleft\arraybackslash}}p{{#1}}}}

% ── Software-default Marker ───────────────────────────────────
\newcommand{{\placeholder}}[1]{{\textit{{\textless #1\textgreater}}}}
\newcommand{{\todo}}[1]{{\colorbox{{yellow}}{{TODO: #1}}}}
\newcommand{{\sdstar}}{{\textsuperscript{{*}}}}
\newbool{{hasSDonPage}}
\boolfalse{{hasSDonPage}}
\newcommand{{\markSD}}{{\global\booltrue{{hasSDonPage}}}}
\renewcommand{{\sdstar}}{{\textsuperscript{{*}}\markSD{{}}}}
\AddToHook{{shipout/before}}{{\global\boolfalse{{hasSDonPage}}}}

\title{{\Large\textbf{{OsdagBridge}} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{{2cm}} \large Design Report}}
\author{{}}
\date{{}}

\begin{{document}}
"""

# ── Reusable Table Header Helper ───────────────────────────────────────────
def make_longtable_headers(col_spec: str, caption_text: str, label_text: str, header_cols: list, col_widths: list = None) -> str:
    """
    Construct a clean PyLaTeX LongTable header block with:
    - Initial caption and header row
    - \\endfirsthead
    - Continued caption and repeated header row
    - \\endhead
    - Continued on next page \\endfoot
    - Final \\endlastfoot
    """
    num_cols = len(header_cols)
    formatted_headers = " & ".join([rf"\textbf{{{c}}}" for c in header_cols])
    
    return rf"""\begin{{longtable}}{{{col_spec}}}
\caption{{\textbf{{{caption_text}}}}} \label{{{label_text}}} \\
\hline
\rowcolor{{tableHeaderBg}} {formatted_headers} \\[5pt]
\hline
\endfirsthead

\multicolumn{{{num_cols}}}{{c}}{{\bfseries \tablename\ \thetable{{}} -- Continued from previous page}} \\[6pt]
\hline
\rowcolor{{tableHeaderBg}} {formatted_headers} \\[5pt]
\hline
\endhead

\hline
\multicolumn{{{num_cols}}}{{r}}{{\footnotesize \textit{{Continued on next page\ldots}}}} \\
\endfoot

\hline
\endlastfoot
"""

def make_longtable_environment(
    col_spec: str,
    caption_text: str,
    label_text: str,
    header_cols: list,
    data_rows: list[list[str]],
    row_height: str = "6pt"
) -> str:
    """
    Build a complete LongTable LaTeX environment string with repeated headers
    and formatted data rows.
    """
    header_block = make_longtable_headers(col_spec, caption_text, label_text, header_cols)
    formatted_rows = []
    for row in data_rows:
        row_str = " & ".join(row) + rf" \\[{row_height}]"
        formatted_rows.append(row_str)
        formatted_rows.append(r"\hline")
    body = "\n".join(formatted_rows)
    return f"{header_block}\n{body}\n\\end{{longtable}}\n"

def create_pylatex_longtable(col_spec: str, caption: str, label: str, header_cols: list):
    """
    Helper for PyLaTeX Table / LongTable generation if PyLaTeX objects are used.
    """
    try:
        from pylatex import LongTable, MultiColumn, NoEscape
        lt = LongTable(col_spec)
        lt.add_caption(caption)
        lt.append(NoEscape(rf"\label{{{label}}} \\ \hline"))
        # Header row
        lt.add_row([NoEscape(rf"\textbf{{{c}}}") for c in header_cols], color="tableHeaderBg")
        lt.append(NoEscape(r"\hline\endfirsthead"))
        # Continuation header
        lt.append(NoEscape(rf"\multicolumn{{{len(header_cols)}}}{{c}}{{\bfseries \tablename\ \thetable{{}} -- Continued from previous page}} \\[6pt] \hline"))
        lt.add_row([NoEscape(rf"\textbf{{{c}}}") for c in header_cols], color="tableHeaderBg")
        lt.append(NoEscape(r"\hline\endhead"))
        # Footer
        lt.append(NoEscape(rf"\hline \multicolumn{{{len(header_cols)}}}{{r}}{{\footnotesize \textit{{Continued on next page\ldots}}}} \\ \endfoot"))
        lt.append(NoEscape(r"\hline\endlastfoot"))
        return lt
    except ImportError:
        return None


def fit_table_columns(spec):
    """Fit fixed-width table columns to the text area, including rules and padding."""
    import re
    pattern = re.compile(r"([pLCR])\{([0-9.]+)cm\}")
    widths = [float(m.group(2)) for m in pattern.finditer(spec)]
    if not widths or sum(widths) < 14:
        return spec
    count, total = len(widths), sum(widths)
    def replace(match):
        share = float(match.group(2)) / total
        return (match.group(1) + r"{\dimexpr" + f"{share:.6f}" + r"\linewidth-2\tabcolsep-"
                + f"{(count + 1) / count:.6f}" + r"\arrayrulewidth\relax}")
    return pattern.sub(replace, spec)
