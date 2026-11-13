"""Single source of truth for OsdagBridge report presentation.

The values in this module deliberately describe LaTeX, rather than exposing a
second formatting DSL to chapter modules.  This keeps a report reproducible
when it is compiled outside the desktop application.
"""

from __future__ import annotations

PAGE_GEOMETRY = "a4paper,left=20mm,right=20mm,top=22mm,bottom=24mm,headheight=15pt,headsep=10pt,footskip=28pt"
PRIMARY_COLOR = "0B2E4F"
SECONDARY_COLOR = "2E6F95"
TABLE_HEADER_COLOR = "DCE6F1"
TABLE_ALT_COLOR = "F5F7FA"
FAIL_COLOR = "B3261E"
TABLE_FONT = r"\small"
FIGURE_WIDTH = r"0.92\textwidth"


def latex_style_definitions() -> str:
    """Return the report-wide geometry, typography, table and caption setup."""
    return rf"""
\usepackage[{PAGE_GEOMETRY}]{{geometry}}
\definecolor{{ReportNavy}}{{HTML}}{{{PRIMARY_COLOR}}}
\definecolor{{ReportSteelBlue}}{{HTML}}{{{SECONDARY_COLOR}}}
\definecolor{{ReportTableHeader}}{{HTML}}{{{TABLE_HEADER_COLOR}}}
\definecolor{{ReportTableAlt}}{{HTML}}{{{TABLE_ALT_COLOR}}}
\definecolor{{ReportFail}}{{HTML}}{{{FAIL_COLOR}}}
\setlength{{\tabcolsep}}{{5pt}}
\renewcommand{{\arraystretch}}{{1.10}}
\setlength{{\LTpre}}{{0pt}}
\setlength{{\LTpost}}{{5pt}}
\setlength{{\arrayrulewidth}}{{0.4pt}}
\setlength{{\extrarowheight}}{{0.8pt}}
\setlength{{\parskip}}{{0.35em}}
\setlength{{\parindent}}{{0pt}}
\captionsetup{{font=small,labelfont={{bf,color=ReportNavy}},textfont=color=black,
    justification=raggedright,singlelinecheck=false,format=plain}}
\titleformat{{\chapter}}[block]{{\normalfont\Large\bfseries\color{{ReportNavy}}\centering}}{{\thechapter}}{{1em}}{{}}
\titleformat{{\section}}{{\normalfont\large\bfseries\color{{ReportSteelBlue}}}}{{\thesection}}{{0.75em}}{{}}
\titlespacing*{{\chapter}}{{0pt}}{{0pt}}{{10pt}}
"""
