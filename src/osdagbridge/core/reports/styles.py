# =============================================================================
# OsdagBridge — Centralized Report Styles & Formatting
#
# Single source of truth for:
#   - Document class and font sizing
#   - Page geometry, margins, and header/footer clearance
#   - Header, footer, and rule definitions (fancyhdr)
#   - Color palette (Osdag brand identity)
#   - Table padding, row spacing, and longtable pagination controls
#   - Headings, captions, and TOC styling
# =============================================================================

# --- Geometry & Page Dimensions ---
PAGE_SIZE = "a4paper"
MARGIN_TOP = "1.0in"
MARGIN_BOTTOM = "1.2in"       # Reserved clearance for footrule & multi-line footer
MARGIN_LEFT = "1.0in"
MARGIN_RIGHT = "1.0in"
HEAD_HEIGHT = "18pt"          # Prevents fancyhdr \headheight warnings for 12pt font
HEAD_SEP = "18pt"
FOOT_SKIP = "36pt"            # Adequate spacing between body text bottom and footer

PAGE_WIDTH_CM = 21.0
PAGE_HEIGHT_CM = 29.7
TEXT_WIDTH_CM = 15.92         # A4 width (21.0 cm) - 2 * 1.0 inch (5.08 cm)
SAFE_TABLE_WIDTH_CM = 15.80   # Safe maximum width for tables to prevent horizontal overflow

# --- Color Palette ---
COLOR_OSDAG_GREEN_HEX = "91B014"   # Osdag signature green (#91B014)
COLOR_OSDAG_GREEN_NAME = "osdagGreen"
COLOR_STATUS_PASS = "black"
COLOR_STATUS_FAIL = "red"
COLOR_STATUS_WARN = "orange"
COLOR_UR_THRESHOLD = "red"          # Phase 2 UR=1.0 dashed line

# --- Typography & Document Parameters ---
DOCUMENT_CLASS = "report"
BASE_FONT_SIZE = "12pt"
LINE_STRETCH = "1.15"
FONT_PACKAGES = "\\usepackage[T1]{fontenc}\n\\usepackage{lmodern}"

# --- Header & Footer Settings ---
RULE_THICKNESS = "1pt"
HEAD_RULE_VSPACE = "2pt"
FOOT_RULE_VSPACE = "4pt"

INSTITUTION_FOOTER_TEXT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
SOFTWARE_DEFAULT_TEXT = r"\footnotesize\textit{* Software default value}"

# --- Table Dimensions & Spacing ---
TABCOLSEP_DEFAULT = "6pt"
TABCOLSEP_COMPACT = "4pt"
TABCOLSEP_DENSE = "3.5pt"

ARRAY_STRETCH = "1.12"
ARRAY_RULE_WIDTH = "0.5pt"
EXTRA_ROW_HEIGHT = "0.6pt"

LT_PRE_SKIP = "0pt"
LT_POST_SKIP = "6pt"
NEEDSPACE_THRESHOLD = r"5\baselineskip"

# --- Table Continuation Labels ---
CONTINUED_FROM_PREV_PAGE = r"Table \thetable\ continued from previous page"
CONTINUED_ON_NEXT_PAGE = r"Continued on next page\ldots"


def get_geometry_latex() -> str:
    """Return LaTeX \\usepackage[...]{geometry} declaration."""
    return (
        r"\usepackage["
        rf"a4paper, top={MARGIN_TOP}, bottom={MARGIN_BOTTOM}, "
        rf"left={MARGIN_LEFT}, right={MARGIN_RIGHT}, "
        rf"headheight={HEAD_HEIGHT}, headsep={HEAD_SEP}, footskip={FOOT_SKIP}"
        r"]{geometry}"
    )


def get_color_definitions_latex() -> str:
    """Return LaTeX color declarations."""
    return rf"\definecolor{{{COLOR_OSDAG_GREEN_NAME}}}{{HTML}}{{{COLOR_OSDAG_GREEN_HEX}}}"


def get_table_spacing_latex() -> str:
    """Return global LaTeX table formatting and pagination rules."""
    return (
        rf"\setlength{{\tabcolsep}}{{{TABCOLSEP_DEFAULT}}}" + "\n"
        rf"\renewcommand{{\arraystretch}}{{{ARRAY_STRETCH}}}" + "\n"
        rf"\setlength{{\LTpre}}{{{LT_PRE_SKIP}}}" + "\n"
        rf"\setlength{{\LTpost}}{{{LT_POST_SKIP}}}" + "\n"
        rf"\setlength{{\arrayrulewidth}}{{{ARRAY_RULE_WIDTH}}}" + "\n"
        rf"\setlength{{\extrarowheight}}{{{EXTRA_ROW_HEIGHT}}}" + "\n"
        rf"\BeforeBeginEnvironment{{table}}{{\needspace{{{NEEDSPACE_THRESHOLD}}}}}" + "\n"
        rf"\BeforeBeginEnvironment{{longtable}}{{\needspace{{{NEEDSPACE_THRESHOLD}}}}}"
    )


def get_fancypagestyles_latex(project_name: str, job_number: str, report_date: str, report_version: str) -> str:
    """Return clean fancyhdr pagestyle definitions without negative vertical hacks.
    
    Software default notice is placed cleanly in the left footer above the institution line,
    completely decoupled from the horizontal footrule.
    """
    return r"""
\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + project_name + r""" $|$ """ + job_number + r"""}
  \fancyhead[R]{""" + report_date + r""" $|$ """ + report_version + r"""}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height """ + RULE_THICKNESS + r""" \vspace{""" + HEAD_RULE_VSPACE + r"""}}
  \renewcommand{\footrule}{\color{osdagGreen}\hrule width\headwidth height """ + RULE_THICKNESS + r""" \vspace{""" + FOOT_RULE_VSPACE + r"""}}
  \fancyfoot[L]{%
    \ifbool{hasSDonPage}{%
      \parbox[b]{0.75\linewidth}{\raggedright""" + SOFTWARE_DEFAULT_TEXT + r"""\\[2pt]\normalsize """ + INSTITUTION_FOOTER_TEXT + r"""}%
    }{%
      """ + INSTITUTION_FOOTER_TEXT + r"""%
    }%
  }
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + project_name + r""" $|$ """ + job_number + r"""}
  \fancyhead[R]{""" + report_date + r""" $|$ """ + report_version + r"""}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height """ + RULE_THICKNESS + r""" \vspace{""" + HEAD_RULE_VSPACE + r"""}}
  \renewcommand{\footrule}{\color{osdagGreen}\hrule width\headwidth height """ + RULE_THICKNESS + r""" \vspace{""" + FOOT_RULE_VSPACE + r"""}}
  \fancyfoot[L]{%
    \ifbool{hasSDonPage}{%
      \parbox[b]{0.75\linewidth}{\raggedright""" + SOFTWARE_DEFAULT_TEXT + r"""\\[2pt]\normalsize """ + INSTITUTION_FOOTER_TEXT + r"""}%
    }{%
      """ + INSTITUTION_FOOTER_TEXT + r"""%
    }%
  }
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \renewcommand{\footrule}{\color{osdagGreen}\hrule width\headwidth height """ + RULE_THICKNESS + r""" \vspace{""" + FOOT_RULE_VSPACE + r"""}}
  \fancyfoot[L]{""" + INSTITUTION_FOOTER_TEXT + r"""}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
}
\pagestyle{main}
"""
