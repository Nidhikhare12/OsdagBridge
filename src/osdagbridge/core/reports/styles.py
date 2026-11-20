"""Centralized styling configuration for OsdagBridge LaTeX Design Reports.

Defines standard page dimensions, margins, header/footer geometry,
brand color palettes, table styling rules, and reusable layout macros.
"""

from typing import Optional


# ==============================================================================
# 1. PAGE GEOMETRY & DIMENSIONS (A4 Paper)
# ==============================================================================
PAGE_SIZE = "a4paper"
MARGIN_TOP = "25mm"
MARGIN_BOTTOM = "28mm"       # Ample space to prevent any table/footer collision
MARGIN_LEFT = "25mm"
MARGIN_RIGHT = "25mm"
HEAD_HEIGHT = "18pt"         # Eliminates fancyhdr \headheight warnings (min 17.5pt required)
HEAD_SEP = "8mm"             # Clean separation between header rule and body text
FOOT_SKIP = "14mm"           # Dedicated footer zone separated from printable body

# Usable text dimensions:
# Total A4 width: 210mm - 2 * 25mm = 160mm (~455pt / 16.0cm)
# Total A4 height: 297mm - (25mm + 28mm) = 244mm (~692pt / 24.4cm)
TEXT_WIDTH_MM = 160
TEXT_WIDTH_CM = 16.0


# ==============================================================================
# 2. BRAND COLOR PALETTE (Hex values for xcolor HTML model)
# ==============================================================================
COLOR_OSDAG_GREEN = "91B014"        # Primary Osdag brand green
COLOR_OSDAG_DARK_GREEN = "6E8A0E"   # Dark green for accents / section headers
COLOR_STATUS_PASS = "2E7D32"        # Accessible dark green for PASS badges
COLOR_STATUS_FAIL = "D32F2F"        # Accessible dark red for FAIL badges
COLOR_STATUS_WARN = "ED6C02"        # Orange for warnings / intermediate checks
COLOR_GRAY = "666666"               # Metadata / subtitle text
COLOR_LIGHT_GRAY = "F5F5F5"         # Alternating table row fill / header background
COLOR_BORDER = "CCCCCC"             # Subtle border tint


# ==============================================================================
# 3. TABLE SPACING & SIZING RULES
# ==============================================================================
TABCOLSEP_PT = 6                    # Intercolumn padding: 6pt on each side (total 12pt per column)
ARRAYSTRETCH = 1.15                 # Comfortable row height multiplier
ARRAYRULEWIDTH_PT = 0.5             # Table border rule width
EXTRAROWHEIGHT_PT = 0.6             # Extra vertical breathing room in cells
LTPRE_PT = 0                        # Vertical space before longtable
LTPOST_PT = 6                       # Vertical space after longtable
NEEDSPACE_BASELINES = 6             # Require at least 6 baselines before starting a table


# ==============================================================================
# 4. LATEX CONFIGURATION FRAGMENTS
# ==============================================================================

def get_geometry_latex() -> str:
    """Return the LaTeX geometry package inclusion with validated margins and header/footer spacing."""
    return rf"""\usepackage[
    {PAGE_SIZE},
    top={MARGIN_TOP},
    bottom={MARGIN_BOTTOM},
    left={MARGIN_LEFT},
    right={MARGIN_RIGHT},
    headheight={HEAD_HEIGHT},
    headsep={HEAD_SEP},
    footskip={FOOT_SKIP}
]{{geometry}}"""


def get_color_definitions_latex() -> str:
    """Return standard LaTeX xcolor color definitions."""
    return rf"""% Osdag Brand and Status Colors
\definecolor{{osdagGreen}}{{HTML}}{{{COLOR_OSDAG_GREEN}}}
\definecolor{{osdagDarkGreen}}{{HTML}}{{{COLOR_OSDAG_DARK_GREEN}}}
\definecolor{{osdagPass}}{{HTML}}{{{COLOR_STATUS_PASS}}}
\definecolor{{osdagFail}}{{HTML}}{{{COLOR_STATUS_FAIL}}}
\definecolor{{osdagWarn}}{{HTML}}{{{COLOR_STATUS_WARN}}}
\definecolor{{osdagGray}}{{HTML}}{{{COLOR_GRAY}}}
\definecolor{{osdagLightGray}}{{HTML}}{{{COLOR_LIGHT_GRAY}}}
\definecolor{{osdagBorder}}{{HTML}}{{{COLOR_BORDER}}}
"""


def get_table_styling_latex() -> str:
    """Return standard table formatting and spacing commands."""
    return rf"""% Table layout and spacing
\setlength{{\tabcolsep}}{{{TABCOLSEP_PT}pt}}
\renewcommand{{\arraystretch}}{{{ARRAYSTRETCH}}}
\setlength{{\LTpre}}{{{LTPRE_PT}pt}}
\setlength{{\LTpost}}{{{LTPOST_PT}pt}}
\setlength{{\arrayrulewidth}}{{{ARRAYRULEWIDTH_PT}pt}}
\setlength{{\extrarowheight}}{{{EXTRAROWHEIGHT_PT}pt}}
\setlength{{\LTleft}}{{\fill}}
\setlength{{\LTright}}{{\fill}}

% Guard against orphaned tables or tables starting too close to the bottom
\BeforeBeginEnvironment{{table}}{{\needspace{{{NEEDSPACE_BASELINES}\baselineskip}}}}
\BeforeBeginEnvironment{{longtable}}{{\needspace{{{NEEDSPACE_BASELINES}\baselineskip}}}}
"""


def get_caption_setup_latex() -> str:
    """Return standard caption styling."""
    return r"""\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
"""


def get_column_definitions_latex() -> str:
    """Return custom LaTeX column type definitions with automatic ragged alignment."""
    return r"""% Custom Column Types with ragged boundaries to prevent overfull hboxes
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}
"""


def get_header_footer_latex(
    project_name: str,
    job_number: str,
    report_date: str,
    report_version: str = "Rev 0"
) -> str:
    """Return clean fancyhdr configuration with zero negative vspace hacks.

    The bottom margin (28mm) and footskip (14mm) provide a dedicated footer zone
    positioned 14mm above the paper edge. Body text terminates at 28mm from paper edge,
    guaranteeing at least 14mm of white space buffer. Tables cannot collide with the footer.
    """
    return rf"""\fancypagestyle{{main}}{{
  \fancyhf{{}}
  \fancyhead[L]{{{project_name} $|$ {job_number}}}
  \fancyhead[R]{{{report_date} $|$ {report_version}}}
  \fancyfoot[L]{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \fancyfoot[R]{{Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vskip 2pt}}
  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \hbox to \headwidth{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}}}\hfil}}%
      \vskip 3pt%
    }}{{}}%
    \color{{osdagGreen}}\hrule width\headwidth height 1pt \vskip 4pt%
  }}
}}

\fancypagestyle{{plain}}{{
  \fancyhf{{}}
  \fancyhead[L]{{{project_name} $|$ {job_number}}}
  \fancyhead[R]{{{report_date} $|$ {report_version}}}
  \fancyfoot[L]{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \fancyfoot[R]{{Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vskip 2pt}}
  \renewcommand{{\footrule}}{{%
    \ifbool{{hasSDonPage}}{{%
      \hbox to \headwidth{{\textcolor{{black}}{{\footnotesize\textit{{* Software default value}}}}\hfil}}%
      \vskip 3pt%
    }}{{}}%
    \color{{osdagGreen}}\hrule width\headwidth height 1pt \vskip 4pt%
  }}
}}

\fancypagestyle{{firstpage}}{{
  \fancyhf{{}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \fancyfoot[L]{{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}}
  \fancyfoot[R]{{Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\footrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vskip 4pt}}
}}
"""
