"""Centralized formatting & style system for the OsdagBridge LaTeX report.

Single source of truth for every visual/layout rule used by the report
generator: document geometry, fonts, colors, spacing, table metrics,
header/footer theme, and status markers.  Chapter modules must consume
formatting exclusively through this module — never hardcode LaTeX styling
literals in chapter files.

Two consumption styles are provided:

* ``preamble()`` / ``title_page()`` / ``toc_section()`` emit the LaTeX
  document scaffolding (used by ``report_generator.py``).
* Semantic spacing/font macros (``\\OsdagVspace*``, ``\\Osdag*``) are defined
  once in the preamble so chapter files can reference them inside their
  LaTeX strings without repeating dimensions.
* Python helpers (``PASS``, ``FAIL``, ``status()``, ``sd()`` ...) return
  ready-made LaTeX fragments for dynamic content.
"""

#: Osdag brand green (HTML hex, consumed by \definecolor{osdagGreen}).
OSDAG_GREEN_HTML = "91B014"

#: LaTeX color names referenced by \textcolor / \color.
COLOR_OSDAG_GREEN = "osdagGreen"
COLOR_PASS = "green"
COLOR_FAIL = "red"
COLOR_INFO = "blue"
COLOR_MUTED = "black"
COLOR_HIGHLIGHT = "yellow"  # used by the \todo debug macro only

# =============================================================================
# SEMANTIC SPACING / FONT MACROS
#
# Each entry maps a macro name to the LaTeX fragment it expands to.  The
# preamble emits one \newcommand per entry; chapter files then write e.g.
# ``\\OsdagVspaceOneEm`` inside their strings instead of ``\\vspace{1em}``.
# =============================================================================

SPACING_MACROS = {
    # Vertical spacing — em based
    "OsdagVspaceOneEm":    r"\vspace{1em}",
    "OsdagVspacePointFourEm": r"\vspace{0.4em}",
    "OsdagVspacePointEightEm": r"\vspace{0.8em}",
    "OsdagVspacePointSixEm":   r"\vspace{0.6em}",
    "OsdagVspacePointFiveEm":  r"\vspace{0.5em}",
    "OsdagVspacePointThreeEm": r"\vspace{0.3em}",
    "OsdagVspaceTwoPointTwoEm": r"\vspace{2.2em}",
    # Vertical spacing — absolute
    "OsdagVspaceTwoPt":     r"\vspace{2pt}",
    "OsdagVspaceFourPt":    r"\vspace{4pt}",
    "OsdagVspaceSixPt":     r"\vspace{6pt}",
    "OsdagVspaceNegEightPt":  r"\vspace{-8pt}",
    "OsdagVspaceNegTwentyPt": r"\vspace{-20pt}",
    "OsdagVspaceNegHalfEm":   r"\vspace{-0.5em}",
    "OsdagVspacePointFourCm": r"\vspace{0.4cm}",
    "OsdagVspacePointEightCm": r"\vspace{0.8cm}",
    "OsdagVspacePointFiveCm":  r"\vspace{0.5cm}",
    "OsdagVspaceTwoCm":        r"\vspace{2cm}",
    # Horizontal spacing
    "OsdagHspaceOneEm":     r"\hspace{1em}",
    # Font size / shape commands used inside generated content
    "OsdagHuge":        r"\Huge",
    "OsdagLarge":       r"\Large",
    "OsdagLargeFont":   r"\large",
    "OsdagSmall":       r"\small",
    "OsdagFootnotesize": r"\footnotesize",
    "OsdagNormalsize":  r"\normalsize",
    "OsdagBFSeries":    r"\bfseries",
    "OsdagITShape":     r"\itshape",
    # Table cell padding overrides used inside chapter tables
    "OsdagTabcolsepFourPt":   r"\setlength{\tabcolsep}{4pt}",
    "OsdagTabcolsepThreePt":  r"\setlength{\tabcolsep}{3pt}",
    "OsdagTabcolsepThreePtFive": r"\setlength{\tabcolsep}{3.5pt}",
    "OsdagTabcolsepSixPt":    r"\setlength{\tabcolsep}{6pt}",
    "OsdagExtrarowheight":    r"\setlength{\extrarowheight}{0.6pt}",
    "OsdagCaptionSkipAbove":  r"\setlength{\abovecaptionskip}{2pt}",
    "OsdagCaptionSkipBelow":  r"\setlength{\belowcaptionskip}{2pt}",
}

def text_colored(color: str, body: str) -> str:
    """Wrap ``body`` in a \\textcolor of the given LaTeX color name."""
    return r"\textcolor{%s}{%s}" % (color, body)

#: Plain PASS marker.
PASS = "PASS"

#: FAIL marker rendered in the fail color.
FAIL = text_colored(COLOR_FAIL, "PASS".replace("PASS", "FAIL"))

#: Black PASS marker (used where PASS must stay neutral, e.g. ch5 utilization).
PASS_BLACK = text_colored(COLOR_MUTED, "PASS")

def status(ok: bool, *, muted_pass: bool = False) -> str:
    """Return the standard PASS/FAIL cell content for a boolean check."""
    if ok:
        return PASS_BLACK if muted_pass else PASS
    return FAIL

def colored_status(value, *, fail_threshold=None, muted_pass: bool = False):
    """Color a numeric/string status red when it fails.

    ``fail_threshold``: values strictly greater than it are failures
    (utilization-ratio style).  When omitted, any string containing
    ``FAIL`` is colored red.
    """
    s = str(value)
    if fail_threshold is not None:
        try:
            bad = float(s) > float(fail_threshold)
        except (TypeError, ValueError):
            bad = "FAIL" in s.upper()
    else:
        bad = "FAIL" in s.upper()
    if bad:
        return text_colored(COLOR_FAIL, s)
    return text_colored(COLOR_MUTED, s) if muted_pass else s

def sd() -> str:
    """Software-default marker (also flags the page footer asterisk)."""
    return r"\sdstar"

def _macro_definitions() -> str:
    lines = [r"\newcommand{\%s}{%s}" % (name, frag)
             for name, frag in SPACING_MACROS.items()]
    return "\n".join(lines)

def geometry_and_packages() -> str:
    """Document class options, package list and global table/layout metrics."""
    return r"""
\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{graphicx}
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
% Table layout and spacing: consistent padding, row height, and longtable pre/post skips
\setlength{\tabcolsep}{6pt}
\renewcommand{\arraystretch}{1.12}
\setlength{\LTpre}{0pt}
\setlength{\LTpost}{6pt}
% Table rules (outline thickness) and small extra row height for clarity
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.6pt}

% Prevent tables from overflowing past the page bottom:
% if fewer than 5 baseline-skips remain, break to the next page first.
\BeforeBeginEnvironment{table}{\needspace{5\baselineskip}}
\BeforeBeginEnvironment{longtable}{\needspace{5\baselineskip}}
"""

def color_and_page_styles(project_name: str, job_number: str,
                           report_date: str, report_version: str) -> str:
    """Brand color, fancyhdr page styles and semantic macro definitions."""
    pn = _escape_tex(project_name)
    jn = _escape_tex(job_number)
    rd = _escape_tex(report_date)
    rv = _escape_tex(report_version)
    return r"""
\definecolor{osdagGreen}{HTML}{""" + OSDAG_GREEN_HTML + r"""}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
}
\pagestyle{main}
\setstretch{1.15}

% Semantic spacing/font macros — single source for chapter-level layout.
""" + _macro_definitions() + r"""

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1}{\colorbox{yellow}{TODO: #1}}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

% Software-default asterisk
\newcommand{\sdstar}{\textsuperscript{*}}
\newbool{hasSDonPage}
\boolfalse{hasSDonPage}
\newcommand{\markSD}{\global\booltrue{hasSDonPage}}
\renewcommand{\sdstar}{\textsuperscript{*}\markSD{}}
\AddToHook{shipout/before}{\global\boolfalse{hasSDonPage}}
"""

def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    """Full LaTeX preamble through \\begin{document}."""
    return (
        geometry_and_packages()
        + color_and_page_styles(project_name, job_number, report_date,
                                report_version)
        + r"""
\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

\begin{document}
"""
    )

def title_page(m, osdag_logo, org_logo):
    """Title page with logos and project metadata table."""
    from .report_utils import _tex
    if osdag_logo:
        lhs = r'\includegraphics[width=\linewidth,keepaspectratio]{' + osdag_logo.replace('\\', '/') + r'}'
    else:
        lhs = r'\textit{(Osdag Logo)}'

    if org_logo:
        rhs = r'\includegraphics[width=\linewidth,height=2.2cm,keepaspectratio]{' + org_logo.replace('\\', '/') + r'}'
    else:
        rhs = r''

    logos_tex = r"""\noindent
\begin{minipage}[c]{0.6\textwidth}
\raggedright
""" + lhs + r"""
\end{minipage}%
\hfill
\begin{minipage}[c]{0.35\textwidth}
\raggedleft
""" + rhs + r"""
\end{minipage}
\\[1cm]
"""

    return r"""
\begin{titlepage}
\thispagestyle{firstpage}
\centering
\vspace*{1.5cm}
""" + logos_tex + r"""
{\Huge \textbf{OsdagBridge}}\\[0.3cm]
{\large Open Source Software for Steel Girder Bridge Design}\\[1.5cm]
{\Large Design Report}\\[1.5cm]
\begin{tabular}{|L{4cm}|L{10cm}|}
\hline
\textbf{Project Name} & """ + _tex(m.project_name) + r""" \\
\hline
\textbf{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\textbf{Author / Designer} & """ + _tex(m.designer) + r""" \\
\hline
\textbf{Reviewer} & """ + _tex(m.reviewer) + r""" \\
\hline
\textbf{Organization} & """ + _tex(m.company) + r""" \\
\hline
\textbf{Client Name and Organization} & """ + _tex(m.client) + r""" \\
\hline
\textbf{Job Number} & """ + _tex(m.job_number) + r""" \\
\hline
\textbf{Date} & """ + _tex(m.report_date) + r""" \\
\hline
\textbf{Report Version} & """ + (_tex(m.subtitle) if m.subtitle else '') + r""" \\
\hline
\end{tabular}
\end{titlepage}
"""

def toc_section() -> str:
    """Table-of-contents styling and \tableofcontents."""
    return r"""
% Chapter / TOC Formatting
\titleformat{\chapter}[block]
  {\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{0pt}{10pt}
\setcounter{tocdepth}{2}

% TOC styling using titletoc
\titlecontents{chapter}[1.5em]
  {\normalfont\vspace{2pt}}
  {\contentslabel{1.5em}}
  {\hspace*{-1.5em}}
  {\hfill\contentspage}

\titlecontents{section}[3.8em]
  {\normalfont}
  {\contentslabel{2.3em}}
  {\hspace*{-2.3em}}
  {\hfill\contentspage}

\titlecontents{subsection}[7.0em]
  {\normalfont}
  {\contentslabel{3.2em}}
  {\hspace*{-3.2em}}
  {\hfill\contentspage}

\newpage
\renewcommand{\contentsname}{\centering\Large\bfseries Table of Contents}
\tableofcontents
"""

def _escape_tex(value) -> str:
    """Local escape mirroring report_utils._tex without a hard dependency."""
    try:
        from .report_utils import _tex
        return _tex(value)
    except Exception:
        return str(value or "")
