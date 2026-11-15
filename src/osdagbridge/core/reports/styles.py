"""Shared visual language and LaTex helpers for OsdagBridge reports.

Keeping report-wide layout decisions here prevents chapter modules from slowly
drifting apart.  The helpers intentionally emit plain LaTex so individual
chapters remain easy to read and test without a LaTex installation.
"""
from __future__ import annotations

BRAND_GREEN = "91B014"
PASS_GREEN = "2E7D32"
FAIL_RED = "C62828"
PAGE_MARGIN = "0.85in"
TABLE_CELL_PADDING_PT = "5"
TABLE_ROW_STRETCH = "1.10"


def report_layout_tex() -> str:
    """Return the shared packages and safe printable-area settings."""
    return rf"""
\usepackage[a4paper,top={PAGE_MARGIN},bottom=0.95in,left={PAGE_MARGIN},right={PAGE_MARGIN},
            headheight=16pt,headsep=18pt,footskip=30pt]{{geometry}}
\usepackage{{graphicx,amsmath,amssymb,booktabs,array,tabularx,float}}
\usepackage{{fancyhdr,hyperref,xcolor,setspace,enumitem,caption,subcaption}}
\usepackage{{multirow,colortbl,longtable,titlesec,titletoc,lastpage,makecell}}
\usepackage{{etoolbox,needspace}}
\captionsetup{{labelfont=bf,justification=raggedright,singlelinecheck=false,format=plain}}
\numberwithin{{table}}{{chapter}}
\numberwithin{{figure}}{{chapter}}
\setlength{{\tabcolsep}}{{{TABLE_CELL_PADDING_PT}pt}}
\renewcommand{{\arraystretch}}{{{TABLE_ROW_STRETCH}}}
\setlength{{\LTpre}}{{0pt}}
\setlength{{\LTpost}}{{6pt}}
\setlength{{\arrayrulewidth}}{{0.5pt}}
\setlength{{\extrarowheight}}{{0.6pt}}
% Do not start a table where it could collide with the footer.
\BeforeBeginEnvironment{{table}}{{\needspace{{6\baselineskip}}}}
\BeforeBeginEnvironment{{longtable}}{{\needspace{{6\baselineskip}}}}
\definecolor{{osdagGreen}}{{HTML}}{{{BRAND_GREEN}}}
\definecolor{{reportPass}}{{HTML}}{{{PASS_GREEN}}}
\definecolor{{reportFail}}{{HTML}}{{{FAIL_RED}}}
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\newcolumntype{{C}}[1]{{>{{\centering\arraybackslash}}p{{#1}}}}
\newcolumntype{{R}}[1]{{>{{\raggedleft\arraybackslash}}p{{#1}}}}
"""


def repeating_longtable_header(header: str, continuation: str = "Table continued from previous page") -> str:
    """Return a complete LongTable header that repeats after each page break."""
    return rf"""\hline
{header}
\hline
\endfirsthead
\multicolumn{{99}}{{l}}{{\small\itshape {continuation}}} \\
\hline
{header}
\hline
\endhead
\hline
\multicolumn{{99}}{{r}}{{\small\itshape Continued on next page}} \\
\endfoot
\hline
\endlastfoot
"""


def chart_tex(path: str, caption: str, width: str = "0.88\\textwidth") -> str:
    """Render a generated chart only when a path was produced."""
    if not path:
        return ""
    return rf"""
\begin{{figure}}[H]
\centering
\includegraphics[width={width}]{{{path.replace('\\', '/')}}}
\caption{{{caption}}}
\end{{figure}}
"""
