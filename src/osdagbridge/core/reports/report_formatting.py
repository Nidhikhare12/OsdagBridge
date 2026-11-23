# =============================================================================
# Centralized Report Formatting
# Shared LaTeX formatting utilities and style configuration.
# =============================================================================

REPORT_TABLE_VSPACE = r"\vspace{0.8em}"
REPORT_TABLE_ROW_GAP = r"\\[6pt]"

REPORT_STANDARD_TABLE_COLUMNS = r"|L{5.5cm}|p{10.0cm}|"
REPORT_WIDE_TABLE_COLUMNS = r"|C{4.0cm}|p{11.5cm}|"

REPORT_TABLE_HEADER_PARAMETER = r"\textbf{Parameter}"
REPORT_TABLE_HEADER_VALUE = r"\textbf{Value}"
REPORT_TABLE_RULE = r"\hline"


def escape_latex(value):
    """Escape plain text for safe insertion into LaTeX."""
    if value is None:
        return ""

    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "{": r"\{",
        "}": r"\}",
        "_": r"\_\allowbreak{}",
        "~": r"\textasciitilde{}",
        "^": r"\^{}",
    }

    pieces = []
    for char in str(value):
        if char == "×":
            pieces.append(r"\ensuremath{\times}")
        elif char == "∠":
            pieces.append(r"\ensuremath{\angle}")
        elif char == "ⅹ":
            pieces.append("x")
        else:
            pieces.append(replacements.get(char, char))
    return "".join(pieces)


def render_value(source_dict, key, unit=""):
    """Read and safely format a dictionary value, appending trusted LaTeX unit text."""
    if not isinstance(source_dict, dict):
        return ""
    value = source_dict.get(key)
    if value in (None, ""):
        return ""
    return escape_latex(value) + (unit or "")


def format_table_caption(caption):
    return escape_latex(caption)


def format_table_cell(value):
    return escape_latex(value)


def standard_table_start(caption, columns=None):
    """Return a standard longtable opening with a repeatable first-page header."""
    columns = columns or REPORT_STANDARD_TABLE_COLUMNS
    safe_caption = format_table_caption(caption)
    return (
        REPORT_TABLE_VSPACE + "\n"
        + r"\begin{longtable}{" + columns + "}\n"
        + r"\caption{\textbf{" + safe_caption + r"}}\\"
        + "\n"
        + REPORT_TABLE_RULE + "\n"
        + REPORT_TABLE_HEADER_PARAMETER + " & "
        + REPORT_TABLE_HEADER_VALUE + r" \\"
        + "\n"
        + REPORT_TABLE_RULE + "\n"
        + r"\endfirsthead" + "\n"
        + r"\multicolumn{2}{c}{\tablename\ \thetable{} -- continued}\\"
        + "\n"
        + REPORT_TABLE_RULE + "\n"
        + REPORT_TABLE_HEADER_PARAMETER + " & "
        + REPORT_TABLE_HEADER_VALUE + r" \\"
        + "\n"
        + REPORT_TABLE_RULE + "\n"
        + r"\endhead" + "\n"
    )


def standard_table_end():
    return r"\end{longtable}"


def format_table_row(label, value):
    return (
        format_table_cell(label) + " & " + format_table_cell(value)
        + " " + REPORT_TABLE_ROW_GAP + "\n"
        + REPORT_TABLE_RULE + "\n"
    )

# Document-wide layout tokens consumed by report_generator.preamble(). Keep
# page geometry, table rhythm and the palette here so chapters do not redefine
# the global report theme independently.
REPORT_PAGE_GEOMETRY_OPTIONS = (
    "a4paper, left=1in, right=1in, top=0.85in, bottom=0.95in, "
    "includeheadfoot, headheight=32pt, headsep=18pt, footskip=38pt"
)
REPORT_TABLE_STYLE_LATEX = r"""
\newcommand{\ReportTopicBreak}{\clearpage}
\newcommand{\ReportTablePadding}{2.5pt}
\newcommand{\ReportCompactTablePadding}{2pt}
\newcommand{\ReportTightTablePadding}{1pt}
\newcommand{\ReportDenseTablePadding}{1.5pt}
\newcommand{\ReportTableStretch}{1.15}
\newcommand{\ReportDenseTableStretch}{1.25}
\newcommand{\ReportFailText}[1]{\textcolor{red}{#1}}
\newcommand{\ReportPassText}[1]{\textcolor{green!45!black}{#1}}
\newcommand{\ReportMutedText}[1]{\textcolor{gray}{#1}}
\newcommand{\ReportInfoText}[1]{\textcolor{blue}{#1}}
\newcommand{\ReportWarningText}[1]{\textcolor{red}{#1}}
\newcommand{\ReportBrandText}[1]{\textcolor{osdagGreen}{#1}}
\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}
\setlength{\tabcolsep}{\ReportTablePadding}
\renewcommand{\arraystretch}{\ReportTableStretch}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\setlength{\LTpre}{0.4em}
\setlength{\LTpost}{0.6em}
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{1pt}
\setlength{\LTcapwidth}{\textwidth}
\setcounter{LTchunksize}{40}
\emergencystretch=2em
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000
\interfootnotelinepenalty=10000
\setlength{\textfloatsep}{12pt plus 2pt minus 2pt}
\setlength{\intextsep}{10pt plus 2pt minus 2pt}
\BeforeBeginEnvironment{table}{\needspace{5\baselineskip}}
\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}
"""
REPORT_COLOR_STYLE_LATEX = r"\definecolor{osdagGreen}{HTML}{91B014}"
REPORT_HEADER_FOOTER_METRICS_LATEX = r"""
\setlength{\headheight}{32pt}
\setlength{\headsep}{18pt}
\setlength{\footskip}{38pt}
"""
