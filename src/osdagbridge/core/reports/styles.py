"""Single source of truth for OsdagBridge report styling.

Every layout rule, color and table setting used by the report generator
lives here. Chapter files and report_generator.preamble() import from this
module, so a global style change is a one-line edit.
"""

# ---- Page and font ----
DOC_CLASS = "report"
FONT_SIZE = "12pt"
PAPER = "a4paper"
MARGIN = "1in"
LINE_STRETCH = "1.15"

# ---- Colors (HTML hex, no '#') ----
COLORS = {
    "osdagGreen": "91B014",
}

# ---- Tables ----
TABLE = {
    "tabcolsep": "6pt",
    "arraystretch": "1.12",
    "arrayrulewidth": "0.5pt",
    "extrarowheight": "0.6pt",
    "LTpre": "0pt",
    "LTpost": "6pt",
    "needspace_lines": 5,
}


# ---- LaTeX snippet builders ----
def documentclass():
    return rf"\documentclass[{FONT_SIZE},{PAPER}]{{{DOC_CLASS}}}"


def geometry():
    return rf"\usepackage[{PAPER}, margin={MARGIN}]{{geometry}}"


def color_definitions():
    return "\n".join(
        rf"\definecolor{{{name}}}{{HTML}}{{{hexval}}}"
        for name, hexval in COLORS.items()
    )


def table_settings():
    t = TABLE
    n = t["needspace_lines"]
    return "\n".join([
        rf"\setlength{{\tabcolsep}}{{{t['tabcolsep']}}}",
        rf"\renewcommand{{\arraystretch}}{{{t['arraystretch']}}}",
        rf"\setlength{{\LTpre}}{{{t['LTpre']}}}",
        rf"\setlength{{\LTpost}}{{{t['LTpost']}}}",
        rf"\setlength{{\arrayrulewidth}}{{{t['arrayrulewidth']}}}",
        rf"\setlength{{\extrarowheight}}{{{t['extrarowheight']}}}",
        rf"\BeforeBeginEnvironment{{table}}{{\needspace{{{n}\baselineskip}}}}",
        rf"\BeforeBeginEnvironment{{longtable}}{{\needspace{{{n}\baselineskip}}}}",
    ])