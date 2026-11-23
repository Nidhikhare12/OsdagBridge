# =============================================================================
# OsdagBridge — Centralized Report Styling & Formatting
#
# Centralizes all visual styling, typography, page margins, brand colors,
# table formatting constants, longtable header mechanisms, header/footer
# layouts, and Matplotlib chart styling for the OsdagBridge design reports.
# =============================================================================

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# -----------------------------------------------------------------------------
# 1. BRAND COLORS & PALETTE
# -----------------------------------------------------------------------------
COLOR_OSDAG_GREEN       = "#91B014"   # Primary brand green
COLOR_OSDAG_GREEN_DARK  = "#6D850F"   # Dark brand green for accents/text
COLOR_OSDAG_GREEN_LIGHT = "#EBF1D6"   # Light brand green for table headers/shading
COLOR_TEXT_DARK         = "#2C3E50"   # Body text / headers
COLOR_TEXT_MUTED        = "#555555"   # Captions, secondary labels
COLOR_BORDER            = "#B0B0B0"   # Table borders
COLOR_PASS              = "#1B7A2B"   # Status PASS green
COLOR_FAIL              = "#C0392B"   # Status FAIL red
COLOR_THRESHOLD         = "#C0392B"   # Red dashed threshold line (UR = 1.0)
COLOR_GRID              = "#E0E0E0"   # Plot grid lines

# Extended chart palette harmonized with Osdag colors
CHART_PALETTE = [
    "#91B014",  # Osdag Green
    "#2980B9",  # Steel Blue
    "#8E44AD",  # Slate Purple
    "#D35400",  # Rust Orange
    "#16A085",  # Teal Green
    "#2C3E50",  # Midnight Blue
    "#7F8C8D",  # Steel Gray
]

# -----------------------------------------------------------------------------
# 2. PAGE GEOMETRY & LAYOUT CONSTANTS
# -----------------------------------------------------------------------------
# Geometry dimensions tuned to prevent footer and header overlaps
MARGIN_TOP       = "25mm"
MARGIN_BOTTOM    = "30mm"      # 30mm bottom margin prevents text-to-footer collision
MARGIN_LEFT      = "20mm"
MARGIN_RIGHT     = "20mm"
HEAD_HEIGHT      = "24pt"      # Sufficient clearance for 2-line header
HEAD_SEP         = "15pt"
FOOT_SKIP        = "25pt"      # Proper separation between body text and footer rule

FONT_SIZE        = "11pt"
LINE_STRETCH     = 1.15

# Table spacing & padding
TABCOLSEP        = "5pt"
ARRAYSTRETCH     = "1.15"
ARRAYRULEWIDTH   = "0.5pt"
EXTRAROWHEIGHT   = "0.8pt"
LTPRE            = "0pt"
LTPOST           = "6pt"

# -----------------------------------------------------------------------------
# 3. LATEX PREAMBLE & STYLESHEET GENERATOR
# -----------------------------------------------------------------------------
def get_latex_preamble(project_name: str, job_number: str, report_date: str, report_version: str = "Rev 0") -> str:
    """
    Generate the complete LaTeX document preamble with centralized geometry,
    colors, typography, table packages, orphan control, and fancyhdr styles.
    """
    from osdagbridge.core.reports.report_utils import _tex
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)

    return rf"""
\documentclass[{FONT_SIZE},a4paper]{{report}}

% Geometry with generous bottom margin to eliminate footer overlap
\usepackage[
  a4paper,
  top={MARGIN_TOP},
  bottom={MARGIN_BOTTOM},
  left={MARGIN_LEFT},
  right={MARGIN_RIGHT},
  headheight={HEAD_HEIGHT},
  headsep={HEAD_SEP},
  footskip={FOOT_SKIP}
]{{geometry}}

% Core packages
\usepackage[utf8]{{inputenc}}
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

% Common Unicode symbols that may appear in engineering input/output text.
% Explicit declarations keep pdfLaTeX from failing on otherwise valid report data.
\DeclareUnicodeCharacter{{2264}}{{\ensuremath{{\leq}}}}
\DeclareUnicodeCharacter{{2265}}{{\ensuremath{{\geq}}}}
\DeclareUnicodeCharacter{{2260}}{{\ensuremath{{\neq}}}}
\DeclareUnicodeCharacter{{00D7}}{{\ensuremath{{\times}}}}
\DeclareUnicodeCharacter{{00B1}}{{\ensuremath{{\pm}}}}
\DeclareUnicodeCharacter{{00B0}}{{\ensuremath{{^\circ}}}}
\DeclareUnicodeCharacter{{03B1}}{{\ensuremath{{\alpha}}}}
\DeclareUnicodeCharacter{{03B2}}{{\ensuremath{{\beta}}}}

% Orphan and widow prevention
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000

% Caption styling
\captionsetup{{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain,
    skip=4pt
}}

\numberwithin{{table}}{{chapter}}
\numberwithin{{figure}}{{chapter}}

% Table layout and spacing
\setlength{{\tabcolsep}}{{{TABCOLSEP}}}
\renewcommand{{\arraystretch}}{{{ARRAYSTRETCH}}}
\setlength{{\LTleft}}{{\fill}}
\setlength{{\LTright}}{{\fill}}
\setlength{{\LTpre}}{{{LTPRE}}}
\setlength{{\LTpost}}{{{LTPOST}}}
\setlength{{\arrayrulewidth}}{{{ARRAYRULEWIDTH}}}
\setlength{{\extrarowheight}}{{{EXTRAROWHEIGHT}}}

% Prevent tables from breaking across pages with fewer than 5 baseline skips
\BeforeBeginEnvironment{{table}}{{\needspace{{5\baselineskip}}}}
\BeforeBeginEnvironment{{longtable}}{{\needspace{{5\baselineskip}}}}

% Brand Colors
\definecolor{{osdagGreen}}{{HTML}}{{91B014}}
\definecolor{{osdagGreenDark}}{{HTML}}{{6D850F}}
\definecolor{{osdagGreenLight}}{{HTML}}{{EBF1D6}}
\definecolor{{passGreen}}{{HTML}}{{1B7A2B}}
\definecolor{{failRed}}{{HTML}}{{C0392B}}

% Header and Footer styling
\fancypagestyle{{main}}{{
  \fancyhf{{}}
  \fancyhead[L]{{\small\textbf{{{pn}}} $|$ {jn}}}
  \fancyhead[R]{{\small {rd} $|$ {rv}}}
  \fancyfoot[L]{{%
    \ifbool{{hasSDonPage}}{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}\newline}}}}{{}}%
    \footnotesize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay%
  }}
  \fancyfoot[R]{{\footnotesize Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
}}

\fancypagestyle{{plain}}{{
  \fancyhf{{}}
  \fancyhead[L]{{\small\textbf{{{pn}}} $|$ {jn}}}
  \fancyhead[R]{{\small {rd} $|$ {rv}}}
  \fancyfoot[L]{{%
    \ifbool{{hasSDonPage}}{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}\newline}}}}{{}}%
    \footnotesize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay%
  }}
  \fancyfoot[R]{{\footnotesize Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
}}

\fancypagestyle{{firstpage}}{{
  \fancyhf{{}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \fancyfoot[L]{{\footnotesize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \fancyfoot[R]{{\footnotesize Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\footrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
}}

\pagestyle{{main}}
\setstretch{{{LINE_STRETCH}}}

% Custom Column Types
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\newcolumntype{{C}}[1]{{>{{\centering\arraybackslash}}p{{#1}}}}
\newcolumntype{{R}}[1]{{>{{\raggedleft\arraybackslash}}p{{#1}}}}

% Software-default asterisk tracker
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

# -----------------------------------------------------------------------------
# 4. LONGTABLE HEADER MECHANISM
# -----------------------------------------------------------------------------
def format_longtable(
    col_spec: str,
    caption: str,
    header_rows: str,
    body_rows: str,
    ncols: int,
    label: str = "",
    note: str = ""
) -> str:
    r"""
    Format a PyLaTeX LongTable block with complete, standard header repetition
    mechanisms (\endfirsthead, \endhead, \endfoot, \endlastfoot).
    
    Guarantees:
      1. First page: Displays caption, optional label, and column headers.
      2. Continuation pages: Displays table title 'Continued from previous page'
         and repeats the exact column headers.
      3. Bottom of continuing pages: Displays 'Continued on next page...'.
      4. Final page bottom: Clean closing rule and optional footer note.
    """
    lbl_tag = f"\\label{{{label}}}" if label else ""
    note_tag = f"\n\\noindent{{\\textit{{{note}}}}}\n" if note else ""

    tex = rf"""
\begin{{longtable}}{{{col_spec}}}
\caption{{\textbf{{{caption}}}}}{lbl_tag} \\
\hline
{header_rows} \\[4pt]
\hline
\endfirsthead

\multicolumn{{{ncols}}}{{c}}{{\small\bfseries Table \thetable\ --- Continued from previous page}} \\[4pt]
\hline
{header_rows} \\[4pt]
\hline
\endhead

\hline
\multicolumn{{{ncols}}}{{r}}{{\footnotesize\textit{{Continued on next page\ldots}}}} \\
\endfoot

\hline
\endlastfoot

{body_rows}
\end{{longtable}}
{note_tag}"""
    return tex

# -----------------------------------------------------------------------------
# 5. MATPLOTLIB CENTRALIZED CHART THEME
# -----------------------------------------------------------------------------
def configure_plot_style():
    """Apply centralized styling defaults to matplotlib global state."""
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
    plt.rcParams['axes.edgecolor'] = COLOR_BORDER
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['axes.labelsize'] = 9.5
    plt.rcParams['axes.titlesize'] = 11.0
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['xtick.labelsize'] = 8.5
    plt.rcParams['ytick.labelsize'] = 8.5
    plt.rcParams['grid.color'] = COLOR_GRID
    plt.rcParams['grid.linestyle'] = '--'
    plt.rcParams['grid.alpha'] = 0.5
    plt.rcParams['figure.autolayout'] = False
