"""Central report styling for the OsdagBridge LaTeX report.

All colors, page geometry, table settings and chart styles live here.
report_generator.py should only import from this file.
"""

# ---------- Page geometry ----------
PAGE = {
    "paper": "a4paper",
    "left": "2.0cm",
    "right": "2.0cm",
    "top": "2.5cm",
    "bottom": "3.0cm",     # extra room so tables never touch the footer
    "headheight": "15pt",
    "headsep": "0.8cm",
    "footskip": "1.2cm",   # footer overlap fix lives here
}

# ---------- Colors (hex, no #) ----------
# TODO: copy exact values from report_generator.py preamble
COLORS = {
    "osdagGreen": "6B8E23",
    "headerGrey": "E6E6E6",
    "rowAlt": "F5F5F5",
    "passGreen": "2E8B57",
    "failRed": "C0392B",
    "ruleGrey": "808080",
}

# ---------- Tables ----------
TABLE = {
    "arraystretch": "1.25",
    "tabcolsep": "4pt",
    "rule_width": "0.4pt",
    "font_size": r"\small",
}

# ---------- Figures / charts ----------
FIGURE = {
    "width": r"0.9\textwidth",
    "chart_figsize": (6.5, 3.5),   # inches, for matplotlib
    "dpi": 200,
}
CHART_COLORS = {
    "bar": "#6B8E23",
    "bar_fail": "#C0392B",
    "limit_line": "#C0392B",
    "grid": "#CCCCCC",
}


# ---------- LaTeX preamble builders ----------
def geometry_block() -> str:
    p = PAGE
    return (
        rf"\usepackage[{p['paper']},left={p['left']},right={p['right']},"
        rf"top={p['top']},bottom={p['bottom']},headheight={p['headheight']},"
        rf"headsep={p['headsep']},footskip={p['footskip']}]{{geometry}}"
    )


def colors_block() -> str:
    lines = [r"\usepackage[table]{xcolor}"]
    for name, hexval in COLORS.items():
        lines.append(rf"\definecolor{{{name}}}{{HTML}}{{{hexval}}}")
    return "\n".join(lines)


def table_block() -> str:
    t = TABLE
    return "\n".join([
        r"\usepackage{longtable,booktabs,array}",
        rf"\renewcommand{{\arraystretch}}{{{t['arraystretch']}}}",
        rf"\setlength{{\tabcolsep}}{{{t['tabcolsep']}}}",
        rf"\setlength{{\arrayrulewidth}}{{{t['rule_width']}}}",
    ])


def header_footer_block(left: str = "OsdagBridge", right: str = "Design Report") -> str:
    return "\n".join([
        r"\usepackage{fancyhdr}",
        r"\pagestyle{fancy}",
        r"\fancyhf{}",
        rf"\fancyhead[L]{{{left}}}",
        rf"\fancyhead[R]{{{right}}}",
        r"\fancyfoot[C]{Page \thepage\ of \pageref{LastPage}}",
        r"\renewcommand{\headrulewidth}{0.4pt}",
        r"\renewcommand{\footrulewidth}{0.4pt}",
    ])


def build_style_preamble() -> str:
    """Everything style-related, in one string for the LaTeX preamble."""
    return "\n".join([
        geometry_block(),
        colors_block(),
        table_block(),
        header_footer_block(),
    ])