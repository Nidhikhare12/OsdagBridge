"""
Centralized LaTeX report styling for OsdagBridge reports.
"""

OSDAG_GREEN = "91B014"

PAGE_SETTINGS = {
    "paper": "a4paper",
    "margin": "1in",
}

TABLE_SETTINGS = {
    "column_padding": "6pt",
    "row_height": "1.12",
    "extra_row_height": "0.6pt",
    "rule_width": "0.5pt",
}


def latex_style_preamble():
    """Return the single source of truth for report layout and table styles."""
    return (
        r"""\usepackage[""" + PAGE_SETTINGS["paper"]
        + r""", margin=""" + PAGE_SETTINGS["margin"] + r"""]{geometry}

\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{array}
\usepackage{longtable}
\usepackage{fancyhdr}

\definecolor{osdagGreen}{HTML}{""" + OSDAG_GREEN + r"""}

\setlength{\tabcolsep}{""" + TABLE_SETTINGS["column_padding"] + r"""}
\renewcommand{\arraystretch}{""" + TABLE_SETTINGS["row_height"] + r"""}
\setlength{\arrayrulewidth}{""" + TABLE_SETTINGS["rule_width"] + r"""}
\setlength{\extrarowheight}{""" + TABLE_SETTINGS["extra_row_height"] + r"""}

"""
    )
