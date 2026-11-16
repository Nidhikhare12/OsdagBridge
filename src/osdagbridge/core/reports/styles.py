# ---------------------------------------------------------------------------
# Document and page geometry
# ---------------------------------------------------------------------------
DOCUMENT_CLASS = r"\documentclass[12pt,a4paper]{report}"
PAGE_GEOMETRY = r"\usepackage[a4paper, margin=1in]{geometry}"
LINE_STRETCH = "1.15"

# ---------------------------------------------------------------------------
# Colours (HTML hex, no '#')
# ---------------------------------------------------------------------------
OSDAG_GREEN_HEX = "91B014"
PASS_COLOR = "black"
FAIL_COLOR = "red"

# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
TABLE_TABCOLSEP = "6pt"
TABLE_ARRAYSTRETCH = "1.12"
TABLE_LT_PRE = "0pt"
TABLE_LT_POST = "6pt"
TABLE_RULE_WIDTH = "0.5pt"
TABLE_EXTRA_ROW_HEIGHT = "0.6pt"
# Break to a new page first if fewer than this many baseline-skips remain.
TABLE_NEEDSPACE_LINES = 5

# ---------------------------------------------------------------------------
# Header / footer
# ---------------------------------------------------------------------------
RULE_HEIGHT = "1pt"
FOOTER_LEFT_TEXT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTER_RIGHT_TEXT = r"Page \thepage\ of \pageref{LastPage}"


# ---------------------------------------------------------------------------
# LaTeX preamble builders
# ---------------------------------------------------------------------------
def _packages_block() -> str:
    return (
        "% Packages\n"
        + PAGE_GEOMETRY + "\n"
        + r"""\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{array}
\usepackage{tabularx}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{setspace}
\usepackage{enumitem}
\usepackage{caption}

\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
\usepackage{subcaption}
\usepackage{multirow}
\usepackage{colortbl}
\usepackage{longtable}
\setlength{\LTleft}{\fill}
\setlength{\LTright}{\fill}
\usepackage{titlesec}
\usepackage{titletoc}
\usepackage{lastpage}
\usepackage{makecell}
\usepackage{etoolbox}
\usepackage{needspace}

\numberwithin{table}{chapter}
\numberwithin{figure}{chapter}
"""
    )


def _table_layout_block() -> str:
    n = TABLE_NEEDSPACE_LINES
    return (
        "% Table layout and spacing: consistent padding, row height, and longtable pre/post skips\n"
        + rf"\setlength{{\tabcolsep}}{{{TABLE_TABCOLSEP}}}" + "\n"
        + rf"\renewcommand{{\arraystretch}}{{{TABLE_ARRAYSTRETCH}}}" + "\n"
        + rf"\setlength{{\LTpre}}{{{TABLE_LT_PRE}}}" + "\n"
        + rf"\setlength{{\LTpost}}{{{TABLE_LT_POST}}}" + "\n"
        + "% Table rules (outline thickness) and small extra row height for clarity\n"
        + rf"\setlength{{\arrayrulewidth}}{{{TABLE_RULE_WIDTH}}}" + "\n"
        + rf"\setlength{{\extrarowheight}}{{{TABLE_EXTRA_ROW_HEIGHT}}}" + "\n"
        + "\n"
        + "% Prevent tables from overflowing past the page bottom:\n"
        + "% Prevent floating tables from overflowing past the page bottom:\n"
        + f"% if fewer than {n} baseline-skips remain, break to the next page first.\n"
        + "% Not applied to longtable: it splits across pages by itself, and a forced\n"
        + "% break before it duplicates the repeated header at the top of the page.\n"
        + rf"\BeforeBeginEnvironment{{table}}{{\needspace{{{n}\baselineskip}}}}" + "\n"
    )


def _colors_block() -> str:
    return rf"\definecolor{{osdagGreen}}{{HTML}}{{{OSDAG_GREEN_HEX}}}" + "\n"

def _head_block(project: str, job: str, date: str, version: str) -> str:
    # Join with a separator only between non-empty parts, so an empty project
    # name / job number does not leave a lone "|" in the page header.
    left = " $|$ ".join(x for x in (project, job) if x)
    right = " $|$ ".join(x for x in (date, version) if x)
    return (
        rf"  \fancyhead[L]{{{left}}}" + "\n"
        + rf"  \fancyhead[R]{{{right}}}" + "\n"
    )


def _footer_block() -> str:
    return (
        rf"  \fancyfoot[L]{{{FOOTER_LEFT_TEXT}}}" + "\n"
        + rf"  \fancyfoot[R]{{{FOOTER_RIGHT_TEXT}}}" + "\n"
    )


def _page_style(name: str, project: str, job: str, date: str, version: str) -> str:
    """The 'main' and 'plain' page styles are identical, so build them once here."""
    h = RULE_HEIGHT
    return (
        rf"\fancypagestyle{{{name}}}{{" + "\n"
        + r"  \fancyhf{}" + "\n"
        + _head_block(project, job, date, version)
        + _footer_block()
        + rf"  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height {h} \vspace{{2pt}}}}" + "\n"
        + r"""  \renewcommand{\footrule}{%
    \ifsdonpage{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
"""
        + rf"    \color{{osdagGreen}}\hrule width\headwidth height {h} \vspace{{6pt}}%" + "\n"
        + "  }\n}\n"
    )


def _first_page_style() -> str:
    h = RULE_HEIGHT
    return (
        r"\fancypagestyle{firstpage}{" + "\n"
        + r"  \fancyhf{}" + "\n"
        + r"  \renewcommand{\headrulewidth}{0pt}" + "\n"
        + _footer_block()
        + rf"  \renewcommand{{\footrule}}{{\vspace{{-8pt}}\color{{osdagGreen}}\hrule width\headwidth height {h} \vspace{{6pt}}}}" + "\n"
        + "}\n"
    )


def _custom_commands_block() -> str:
    return (
        r"""\pagestyle{main}
"""
        + rf"\setstretch{{{LINE_STRETCH}}}" + "\n"
        + r"""
% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk. Each star writes the page it is printed on to the .aux
% file (the page number is expanded at shipout, so it is the real page, even for
% longtable rows). The footer shows the note only on pages listed there.
% Like \pageref{LastPage}, this needs two LaTeX runs.
\makeatletter
\newcommand{\sdonpage}[1]{\global\@namedef{sd@page@#1}{}}
\newcommand{\sdstar}{\textsuperscript{*}\protected@write\@auxout{}{\string\sdonpage{\thepage}}}
\newcommand{\ifsdonpage}[2]{\ifcsname sd@page@\thepage\endcsname #1\else #2\fi}
\makeatother

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""
    )


def build_preamble(project: str, job: str, date: str, version: str) -> str:
    """Full LaTeX preamble. The four arguments must already be LaTeX-escaped."""
    return (
        "\n"
        + DOCUMENT_CLASS + "\n\n"
        + _packages_block()
        + _table_layout_block()
        + "\n"
        + _colors_block()
        + "\n"
        + _page_style("main", project, job, date, version)
        + _page_style("plain", project, job, date, version)
        + _first_page_style()
        + _custom_commands_block()
    )