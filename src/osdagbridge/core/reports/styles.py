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
    return r"""
\usepackage[a4paper, margin=1in]{geometry}

\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{array}
\usepackage{longtable}
\usepackage{fancyhdr}

\definecolor{osdagGreen}{HTML}{91B014}

\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.12}
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.6pt}

"""