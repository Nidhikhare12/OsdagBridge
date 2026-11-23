"""
Single source of truth for all report layout and visual settings.
Chapter files and the preamble import from here; do not hardcode
fonts, colors, margins, paddings or table widths anywhere else.
"""

# ---------------- Document / page ----------------
DOCUMENT_CLASS_OPTIONS = "12pt,a4paper"
GEOMETRY = ("a4paper, top=1in, bottom=1.15in, left=1in, right=1in, "
            "headheight=15pt, headsep=0.3in, footskip=0.5in")
LINE_STRETCH = "1.15"

# ---------------- Colors (name -> HTML hex) ----------------
COLORS = {
    "osdagGreen": "91B014",
    "headerBg":   "E6EDC8",
    "rowAlt":     "F6F8EC",
    "passGreen":  "2E7D32",
    "failRed":    "C62828",
}

# ---------------- Table layout ----------------
TAB_COL_SEP = "6pt"
ARRAY_STRETCH = "1.12"
EXTRA_ROW_HEIGHT = "0.6pt"
ARRAY_RULE_WIDTH = "0.5pt"
LT_PRE = "0pt"
LT_POST = "6pt"
NEEDSPACE = r"5\baselineskip"

# Standard column widths used by the 2-column parameter/value tables
LABEL_COL = "5.5cm"
VALUE_COL = "10.0cm"

# ---------------- Header / footer ----------------
FOOTER_LEFT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
RULE_THICKNESS = "1pt"

# ---------------- Charts (matplotlib) ----------------
CHART = {
    "figsize": (6.5, 3.6),
    "dpi": 200,
    "threshold_color": "red",
    "threshold_style": "--",
    "bar_colors": ["#1F3A5F", "#2E5C8A", "#6C8EBF", "#A9C2E0"],
    "pass_color": "#2E7D32",
    "fail_color": "#C62828",
}
FIGURE_WIDTH = r"0.9\textwidth"


# ---------------- LaTeX snippet builders ----------------
def geometry_package():
    return r"\usepackage[" + GEOMETRY + r"]{geometry}"


def color_definitions():
    return "\n".join(
        r"\definecolor{" + name + r"}{HTML}{" + hexval + "}"
        for name, hexval in COLORS.items()
    )


def table_layout_block():
    return "\n".join([
        r"\setlength{\tabcolsep}{" + TAB_COL_SEP + "}",
        r"\renewcommand{\arraystretch}{" + ARRAY_STRETCH + "}",
        r"\setlength{\LTpre}{" + LT_PRE + "}",
        r"\setlength{\LTpost}{" + LT_POST + "}",
        r"\setlength{\arrayrulewidth}{" + ARRAY_RULE_WIDTH + "}",
        r"\setlength{\extrarowheight}{" + EXTRA_ROW_HEIGHT + "}",
        r"\BeforeBeginEnvironment{table}{\needspace{" + NEEDSPACE + "}}",
        r"\BeforeBeginEnvironment{longtable}{\needspace{" + NEEDSPACE + "}}",
    ])
