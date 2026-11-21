# =============================================================================
# OsdagBridge — Centralized Report Styling System (Phase 2B)
# =============================================================================
"""
Single source of truth for all LaTeX styling, document geometry, colors,
fonts, table padding, header/footer configuration, column presets, and
chart style parameters across the OsdagBridge design report.
"""

from osdagbridge.core.reports.report_utils import _tex

# ---------------------------------------------------------------------------
# 1. Document & Page Geometry
# ---------------------------------------------------------------------------
DOC_CLASS = "report"
DOC_FONT_SIZE = "12pt"
DOC_PAPER_SIZE = "a4paper"

PAGE_MARGIN = "1in"
PAGE_HEADHEIGHT = "15pt"
PAGE_FOOTSKIP = "30pt"

# Line & paragraph spacing
LINE_STRETCH = "1.15"
PARAGRAPH_SKIP = "0pt"

# ---------------------------------------------------------------------------
# 2. Unified Brand & Status Colors
# ---------------------------------------------------------------------------
# Primary Osdag brand green
COLOR_PRIMARY_HEX = "91B014"
COLOR_PRIMARY_NAME = "osdagGreen"

# Status colors for design checks & tables
COLOR_PASS_HEX = "000000"     # Black for standard passing text
COLOR_FAIL_HEX = "D9534F"     # Red for failing checks (UR > 1.0)
COLOR_WARN_HEX = "337AB7"     # Blue for warnings / info
COLOR_HIGHLIGHT_HEX = "FFFF00"# Yellow for TODOs / highlights

COLOR_PASS_NAME = "black"
COLOR_FAIL_NAME = "red"
COLOR_WARN_NAME = "blue"

# ---------------------------------------------------------------------------
# 3. Table Formatting & Rules
# ---------------------------------------------------------------------------
# Cell padding & row stretching
TABLE_COL_SEP = "6pt"
TABLE_COL_SEP_COMPACT = "3pt"
TABLE_ARRAY_STRETCH = "1.12"
TABLE_RULE_WIDTH = "0.5pt"
TABLE_EXTRA_ROW_HEIGHT = "0.6pt"

# Longtable pre- and post-skips
TABLE_LT_PRE = "0pt"
TABLE_LT_POST = "6pt"

# Caption spacing
CAPTION_ABOVE_SKIP = "2pt"
CAPTION_BELOW_SKIP = "2pt"

# ---------------------------------------------------------------------------
# 4. Page-Break & Spacing Guard (Needspace)
# ---------------------------------------------------------------------------
# Minimum baseline skips required before opening a table or longtable
NEEDSPACE_TABLE = r"5\baselineskip"
NEEDSPACE_LONGTABLE = r"5\baselineskip"
NEEDSPACE_SECTION = r"4\baselineskip"

# ---------------------------------------------------------------------------
# 5. Header & Footer Theme
# ---------------------------------------------------------------------------
HEADER_RULE_WIDTH = "1pt"
HEADER_RULE_GAP = "2pt"

FOOTER_RULE_WIDTH = "1pt"
FOOTER_RULE_GAP = "6pt"

FOOTER_ORG_TEXT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTER_PAGE_TEXT = r"Page \thepage\ of \pageref{LastPage}"
FOOTER_DEFAULT_NOTE = r"* Software default value"

FOOTER_SD_VSPACE_TOP = "-20pt"
FOOTER_SD_VSPACE_BOT = "4pt"
FOOTER_NORMAL_VSPACE = "-8pt"

# ---------------------------------------------------------------------------
# 6. Named Column-Width Presets
# ---------------------------------------------------------------------------
# Standard column widths used across chapters
COL_NARROW = "1.8cm"
COL_MED_SMALL = "2.2cm"
COL_MED = "2.5cm"
COL_MED_LARGE = "3.8cm"
COL_WIDE = "4.5cm"
COL_EXTRA_WIDE = "5.5cm"
COL_VALUE_WIDE = "8.5cm"
COL_VALUE_FULL = "10.0cm"

# Common table column specifications
TABLE_SPEC_TITLE = r"|L{4cm}|L{10cm}|"
TABLE_SPEC_TWO_COL = r"|L{5.2cm}|L{8.4cm}|"
TABLE_SPEC_GIRDER_SUMMARY = r"|C{2.0cm}|L{7.5cm}|>{\centering\arraybackslash}p{4.5cm}|"
TABLE_SPEC_OVERALL_SUMMARY = r"|C{3.0cm}|L{4.0cm}|C{2.1cm}|C{2.1cm}|>{\centering\arraybackslash}p{1.6cm}|"
TABLE_SPEC_BOQ = r"|C{0.9cm}|L{3.1cm}|C{2.7cm}|C{1.8cm}|C{1.7cm}|C{1.7cm}|C{1.7cm}|"
TABLE_SPEC_DEMANDS = r"|>{\centering\arraybackslash}p{2.5cm}|>{\centering\arraybackslash}p{1.4cm}|>{\centering\arraybackslash}p{1.25cm}|>{\centering\arraybackslash}p{1.1cm}|>{\centering\arraybackslash}p{1.4cm}|>{\centering\arraybackslash}p{1.25cm}|>{\centering\arraybackslash}p{1.1cm}|>{\centering\arraybackslash}p{1.3cm}|>{\centering\arraybackslash}p{1.3cm}|"
TABLE_SPEC_REACTIONS = r"|C{4.4cm}|C{4.4cm}|C{4.4cm}|"
TABLE_SPEC_DEFLECTION = r"|L{5.5cm}|L{8.2cm}|"
TABLE_SPEC_GIRDER_GEN = r"|L{1.5cm}|L{1.6cm}|p{3.0cm}|p{3.3cm}|p{3.3cm}|"
TABLE_SPEC_GIRDER_DIM = r"|L{1.5cm}|L{1.8cm}|L{1.5cm}|p{3.8cm}|p{3.8cm}|"
TABLE_SPEC_GIRDER_REST = r"|C{1.4cm}|L{2.6cm}|L{2.3cm}|L{2.8cm}|L{2.6cm}|L{2.4cm}|"
TABLE_SPEC_CB = r"|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{3.5cm}|C{2.0cm}|"
TABLE_SPEC_ED = r"|L{2.5cm}|L{2.5cm}|L{3.5cm}|L{4.5cm}|"
TABLE_SPEC_GIRDER_CLASS = r"|C{1.8cm}|L{2.8cm}|C{3.2cm}|C{2.2cm}|>{\centering\arraybackslash}p{3.5cm}|"
TABLE_SPEC_GIRDER_CHECK_5COL = r"|C{1.8cm}|C{3.2cm}|C{3.2cm}|>{\centering\arraybackslash}p{3.6cm}|C{1.7cm}|"
TABLE_SPEC_STIFFENER_SUMMARY = r"|C{2.0cm}|L{6.2cm}|>{\arraybackslash}p{6.2cm}|"
TABLE_SPEC_END_PANEL_CHECK = r"|C{1.8cm}|L{3.2cm}|C{3.2cm}|>{\centering\arraybackslash}p{3.6cm}|C{1.7cm}|"
TABLE_SPEC_SERVICEABILITY_5COL = r"|C{1.8cm}|L{3.2cm}|C{3.0cm}|>{\centering\arraybackslash}p{3.2cm}|C{2.2cm}|"
TABLE_SPEC_FATIGUE_5COL = r"|C{1.8cm}|C{3.2cm}|C{3.2cm}|>{\centering\arraybackslash}p{3.0cm}|C{2.2cm}|"
TABLE_SPEC_GIRDER_DCR = r"|C{1.2cm}|>{\centering\arraybackslash}p{2.8cm}|C{2.4cm}|C{1.8cm}|C{1.8cm}|C{1.3cm}|C{1.3cm}|"
TABLE_SPEC_SC_CAPACITY = r"|L{3.2cm}|C{5.0cm}|>{\centering\arraybackslash}p{2.5cm}|L{2.8cm}|"
TABLE_SPEC_SC_SPACING = r"|L{3.0cm}|>{\centering\arraybackslash}p{4.0cm}|>{\centering\arraybackslash}p{4.0cm}|C{2.0cm}|"
TABLE_SPEC_TRANSVERSE_SHEAR = r"|L{4.5cm}|>{\arraybackslash}p{6.8cm}|C{2.0cm}|"
TABLE_SPEC_DECK_FLEXURE = r"|C{2.5cm}|C{3.0cm}|C{2.8cm}|>{\centering\arraybackslash}p{3.5cm}|C{1.6cm}|"
TABLE_SPEC_DECK_CHECK_4COL = r"|L{4.8cm}|C{3.0cm}|>{\centering\arraybackslash}p{4.0cm}|C{1.8cm}|"
TABLE_SPEC_DECK_CRACK = r"|L{6.0cm}|>{\arraybackslash}p{8.0cm}|"
TABLE_SPEC_DECK_DETAILING = r"|L{4.8cm}|>{\centering\arraybackslash}p{3.5cm}|>{\centering\arraybackslash}p{3.5cm}|C{1.6cm}|"
TABLE_SPEC_CB_PROPS = r"|C{1.3cm}|L{2.2cm}|L{2.4cm}|C{2.2cm}|C{1.6cm}|C{1.6cm}|"
TABLE_SPEC_CB_SLENDER = r"|C{1.5cm}|L{2.0cm}|L{2.0cm}|C{2.4cm}|C{2.0cm}|>{\centering\arraybackslash}p{3.0cm}|"
TABLE_SPEC_CB_CAPACITY = r"|C{1.1cm}|L{1.8cm}|C{2.0cm}|C{2.4cm}|C{1.8cm}|C{1.9cm}|C{1.0cm}|C{1.4cm}|"
TABLE_SPEC_VEHICLE_LL = r"|L{4.2cm}|C{2.8cm}|C{3.2cm}|C{3.2cm}|"
TABLE_SPEC_FOOTPATH_LL = r"|L{4.2cm}|C{1.8cm}|C{1.6cm}|C{2.6cm}|C{2.6cm}|"
TABLE_SPEC_LOAD_COMBOS = r"|C{3.5cm}|p{10.5cm}|"

# ---------------------------------------------------------------------------
# 7. Document Spacing Constants
# ---------------------------------------------------------------------------
SPACE_TITLE_TOP = "1.5cm"
SPACE_LOGOS_GAP = "1cm"
SPACE_TITLE_APP = "0.3cm"
SPACE_APP_REPORT = "1.5cm"
SPACE_REPORT_TABLE = "1.5cm"
SPACE_SECTION_GAP = "0.4cm"
SPACE_TABLE_GAP = "1em"

# ---------------------------------------------------------------------------
# 8. Chart Style Constants (matplotlib)
# ---------------------------------------------------------------------------
CHART_DPI = 300
CHART_FIGSIZE_WIDE = (7.0, 3.8)
CHART_FIGSIZE_BAR = (6.0, 3.5)
CHART_FIGSIZE_DONUT = (5.0, 4.0)

CHART_COLOR_PRIMARY = "#" + COLOR_PRIMARY_HEX   # Osdag brand green
CHART_COLOR_SECONDARY = "#337AB7"               # Accent steel blue
CHART_COLOR_ACCENT = "#5CB85C"                  # Soft green
CHART_COLOR_WARN = "#F0AD4E"                    # Amber
CHART_COLOR_DANGER = "#D9534F"                  # Limit line red (UR = 1.0)
CHART_COLOR_GRID = "#E0E0E0"
CHART_GRID_ALPHA = 0.6


# ---------------------------------------------------------------------------
# 9. LaTeX Preamble Generator
# ---------------------------------------------------------------------------
def generate_preamble(project_name: str, job_number: str, report_date: str, report_version: str = 'Rev 0') -> str:
    """
    Generate the complete LaTeX document preamble using centralized style constants.
    """
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)

    # Clean up report_version for header: drop "Final Design Report - " since title page states it
    clean_rv = rv
    for prefix in ["Final Design Report - ", "Final Design Report: ", "Final Design Report "]:
        if clean_rv.startswith(prefix):
            clean_rv = clean_rv[len(prefix):].strip()
    if clean_rv == "Final Design Report":
        clean_rv = ""
    clean_rv = clean_rv.strip("() ")

    # Constrain header string lengths: truncate excessively long strings to preserve clean layout
    pn_hdr = (pn[:42] + "...") if len(pn) > 45 else pn
    if clean_rv:
        rv_hdr = (clean_rv[:28] + "...") if len(clean_rv) > 30 else clean_rv
        right_hdr_text = jn + r""" \quad$\vert$\quad """ + rd + r""" \quad$\vert$\quad """ + rv_hdr
    else:
        right_hdr_text = jn + r""" \quad$\vert$\quad """ + rd

    return (
        r"""
\documentclass[""" + DOC_FONT_SIZE + r""",""" + DOC_PAPER_SIZE + r"""]{""" + DOC_CLASS + r"""}

% Packages
\usepackage[""" + DOC_PAPER_SIZE + r""", top=1.0in, bottom=1.25in, left=1.0in, right=1.0in, headheight=30pt, headsep=10pt, footskip=28pt]{geometry}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}

\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}
% Table layout and spacing: consistent padding, row height, and longtable pre/post skips
\setlength{\tabcolsep}{""" + TABLE_COL_SEP + r"""}
\renewcommand{\arraystretch}{""" + str(TABLE_ARRAY_STRETCH) + r"""}
\setlength{\LTpre}{""" + TABLE_LT_PRE + r"""}
\setlength{\LTpost}{""" + TABLE_LT_POST + r"""}
% Table rules (outline thickness) and small extra row height for clarity
\setlength{\arrayrulewidth}{""" + TABLE_RULE_WIDTH + r"""}
\setlength{\extrarowheight}{""" + TABLE_EXTRA_ROW_HEIGHT + r"""}

% Prevent tables from overflowing past the page bottom:
% if fewer than 5 baseline-skips remain, break to the next page first.
\BeforeBeginEnvironment{table}{\needspace{""" + NEEDSPACE_TABLE + r"""}}
\BeforeBeginEnvironment{longtable}{\needspace{""" + NEEDSPACE_LONGTABLE + r"""}}

\definecolor{""" + COLOR_PRIMARY_NAME + r"""}{HTML}{""" + COLOR_PRIMARY_HEX + r"""}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{\parbox[b]{0.32\headwidth}{\raggedright\small\textsf{""" + pn_hdr + r"""}}}
  \fancyhead[R]{\parbox[b]{0.66\headwidth}{\raggedleft\footnotesize\textsf{""" + right_hdr_text + r"""}}}
  \fancyfoot[L]{""" + FOOTER_ORG_TEXT + r"""}
  \fancyfoot[R]{""" + FOOTER_PAGE_TEXT + r"""}
  \renewcommand{\headrulewidth}{""" + HEADER_RULE_WIDTH + r"""}
  \renewcommand{\headrule}{\color{""" + COLOR_PRIMARY_NAME + r"""}\hrule width\headwidth height """ + HEADER_RULE_WIDTH + r""" \vskip """ + HEADER_RULE_GAP + r"""}
  \renewcommand{\footrulewidth}{""" + FOOTER_RULE_WIDTH + r"""}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vskip -12pt%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{""" + FOOTER_DEFAULT_NOTE + r"""}}\hfil}%
      \vskip 4pt%
    }{%
      \vskip -4pt%
    }%
    \color{""" + COLOR_PRIMARY_NAME + r"""}\hrule width\headwidth height """ + FOOTER_RULE_WIDTH + r""" \vskip """ + FOOTER_RULE_GAP + r"""%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{\parbox[b]{0.32\headwidth}{\raggedright\small\textsf{""" + pn_hdr + r"""}}}
  \fancyhead[R]{\parbox[b]{0.66\headwidth}{\raggedleft\footnotesize\textsf{""" + right_hdr_text + r"""}}}
  \fancyfoot[L]{""" + FOOTER_ORG_TEXT + r"""}
  \fancyfoot[R]{""" + FOOTER_PAGE_TEXT + r"""}
  \renewcommand{\headrulewidth}{""" + HEADER_RULE_WIDTH + r"""}
  \renewcommand{\headrule}{\color{""" + COLOR_PRIMARY_NAME + r"""}\hrule width\headwidth height """ + HEADER_RULE_WIDTH + r""" \vskip """ + HEADER_RULE_GAP + r"""}
  \renewcommand{\footrulewidth}{""" + FOOTER_RULE_WIDTH + r"""}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vskip -12pt%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{""" + FOOTER_DEFAULT_NOTE + r"""}}\hfil}%
      \vskip 4pt%
    }{%
      \vskip -4pt%
    }%
    \color{""" + COLOR_PRIMARY_NAME + r"""}\hrule width\headwidth height """ + FOOTER_RULE_WIDTH + r""" \vskip """ + FOOTER_RULE_GAP + r"""%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{""" + FOOTER_ORG_TEXT + r"""}
  \fancyfoot[R]{}
  \renewcommand{\footrule}{\vskip -4pt\color{""" + COLOR_PRIMARY_NAME + r"""}\hrule width\headwidth height """ + FOOTER_RULE_WIDTH + r""" \vskip """ + FOOTER_RULE_GAP + r"""}
}
\pagestyle{main}
\setstretch{""" + str(LINE_STRETCH) + r"""}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""
    )
