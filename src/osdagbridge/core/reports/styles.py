"""Shared report typography, page boxes, table spacing, footer and chart theme.

Column widths remain with their table schemas; visual policy lives here.
"""
from functools import wraps

# Single colour palette: LaTeX \definecolor names and chart colours both come from here.
PALETTE = {
    "osdagGreen": "91B014",   # brand rules in header/footer
    "reportPass": "688510",   # passing bars (darker green for contrast on white)
    "reportFail": "C43C39",   # failing values, UR = 1.0 reference line
    "reportInfo": "245A81",   # neutral bars (quantities)
    "reportMissing": "777777",
}
CHART = {"pass": "#" + PALETTE["reportPass"], "fail": "#" + PALETTE["reportFail"],
         "neutral": "#" + PALETTE["reportInfo"], "missing": "#" + PALETTE["reportMissing"],
         "dpi": 160, "font_size": 10}
FIGURE_WIDTH = r"0.94\textwidth"

# Symbols that design check names and messages may contain (e.g. "Leg ≤ H_limit").
# pdfLaTeX stops with "Unicode character not set up" on any of these, so map them
# once here rather than escaping in every chapter.
UNICODE_SYMBOLS = {
    "≤": r"\ensuremath{\le}", "≥": r"\ensuremath{\ge}", "≠": r"\ensuremath{\neq}",
    "≈": r"\ensuremath{\approx}", "±": r"\ensuremath{\pm}", "·": r"\ensuremath{\cdot}",
    "→": r"\ensuremath{\rightarrow}", "←": r"\ensuremath{\leftarrow}", "√": r"\ensuremath{\surd}",
    "∞": r"\ensuremath{\infty}", "−": r"\ensuremath{-}", "…": r"\ldots{}",
    "α": r"\ensuremath{\alpha}", "β": r"\ensuremath{\beta}", "γ": r"\ensuremath{\gamma}",
    "δ": r"\ensuremath{\delta}", "Δ": r"\ensuremath{\Delta}", "ε": r"\ensuremath{\varepsilon}",
    "η": r"\ensuremath{\eta}", "θ": r"\ensuremath{\theta}", "λ": r"\ensuremath{\lambda}",
    "μ": r"\ensuremath{\mu}", "ρ": r"\ensuremath{\rho}", "σ": r"\ensuremath{\sigma}",
    "Σ": r"\ensuremath{\Sigma}", "τ": r"\ensuremath{\tau}", "φ": r"\ensuremath{\phi}",
    "ϕ": r"\ensuremath{\phi}", "χ": r"\ensuremath{\chi}", "ψ": r"\ensuremath{\psi}",
    "ω": r"\ensuremath{\omega}", "✓": r"\ensuremath{\checkmark}", "✗": r"\ensuremath{\times}",
}


def unicode_declarations():
    return "\n".join(r"\DeclareUnicodeCharacter{%04X}{%s}" % (ord(ch), tex)
                     for ch, tex in UNICODE_SYMBOLS.items())


def report_section(function):
    """Apply the shared body style at each chapter entry point."""
    @wraps(function)
    def render(*args, **kwargs):
        return r"\ReportSectionStyle" + "\n" + function(*args, **kwargs)
    return render


def _column_count(spec):
    """Number of columns in a tabular/longtable column specification."""
    count, i = 0, 0
    while i < len(spec):
        ch = spec[i]
        if ch in '>@<!':                      # >{..} <{..} @{..} !{..}: no column
            i = _skip_group(spec, i + 1)
            continue
        if ch in 'LCRpmb':                    # width columns take one {..} argument
            count += 1
            i = _skip_group(spec, i + 1)
            continue
        if ch in 'lcrX':
            count += 1
        i += 1
    return count


def _skip_group(spec, i):
    """Index just after the balanced {..} group starting at spec[i]."""
    if i >= len(spec) or spec[i] != '{':
        return i
    depth = 0
    for j in range(i, len(spec)):
        depth += {'{': 1, '}': -1}.get(spec[j], 0)
        if depth == 0:
            return j + 1
    return len(spec)


def continued_tables(tex):
    """Add page-break notices and a closing rule to every longtable.

    The continuation head gets "Table N continued from previous page" (or an
    unnumbered notice when the table has no caption); every page except the
    last gets a closing rule and "Continued on next page". The rule is drawn
    one rule-width higher, so it overlaps a row's own \\hline instead of
    doubling it.
    """
    out, pos = [], 0
    begin = r'\begin{longtable}'
    while True:
        start = tex.find(begin, pos)
        if start < 0:
            out.append(tex[pos:])
            return ''.join(out)
        spec_open = start + len(begin)
        spec_close = _skip_group(tex, spec_open)
        end = tex.find(r'\end{longtable}', spec_close)
        first = tex.find(r'\endfirsthead', spec_close, end)
        head = tex.find(r'\endhead', spec_close, end)
        if end < 0 or first < 0 or head < 0 or r'\endfoot' in tex[spec_close:end]:
            out.append(tex[pos:spec_close])
            pos = spec_close
            continue
        n = _column_count(tex[spec_open + 1:spec_close - 1])
        notice_from = (r'\ReportContinuedFromNumbered' if r'\caption' in tex[spec_close:first]
                       else r'\ReportContinuedFrom')
        head_start = first + len(r'\endfirsthead')
        head_end = head + len(r'\endhead')
        out.append(tex[pos:head_start])
        out.append('\n\\multicolumn{%d}{@{}l}{%s}\\\\' % (n, notice_from))
        out.append(tex[head_start:head_end])
        out.append('\n\\noalign{\\vskip-\\arrayrulewidth}\\hline\n'
                   '\\multicolumn{%d}{@{}r@{}}{\\ReportContinuedOn}\\\\\n\\endfoot\n\\endlastfoot' % n)
        pos = head_end


def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    from .report_utils import _tex
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)
    head_left = pn + (r" $|$ " + jn if str(job_number or '').strip() else "")
    colours = "\n".join(r"\definecolor{%s}{HTML}{%s}" % item for item in PALETTE.items())
    return r"""
\documentclass[12pt,a4paper]{report}

% Packages
\usepackage[a4paper,left=20mm,right=20mm,top=26mm,bottom=32mm,includeheadfoot,headheight=28pt,headsep=8mm,footskip=18mm]{geometry}
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
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
\setlength{\LTpre}{0pt}
\setlength{\LTpost}{6pt}
% Table rules (outline thickness) and small extra row height for clarity
\setlength{\arrayrulewidth}{0.5pt}
\setlength{\extrarowheight}{0.6pt}

% Prevent tables from overflowing past the page bottom:
% if fewer than 7 baseline-skips remain, break to the next page first.
\BeforeBeginEnvironment{table}{\Needspace{7\baselineskip}}
\BeforeBeginEnvironment{longtable}{\Needspace{7\baselineskip}}

""" + colours + "\n" + unicode_declarations() + r"""
\newcommand{\ReportSectionStyle}{\small\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.15}}
\newcommand{\ReportCompactTable}{\setlength{\tabcolsep}{2pt}}
\newcommand{\ReportCaptionStyle}{\setlength{\abovecaptionskip}{2pt}\setlength{\belowcaptionskip}{2pt}}
\newcommand{\ReportWideRows}{\renewcommand{\arraystretch}{1.25}}

\newcommand{\ReportBrandFont}{\Huge}
\newcommand{\ReportCoverTopSpace}{\vspace*{1.5cm}}
\newcommand{\ReportTableGap}{\vspace{1em}}
\newcommand{\ReportMinorGap}{\vspace{0.4em}}
\newcommand{\ReportSectionGap}{\vspace{1.5em}}
\newcommand{\ReportMajorGap}{\vspace{2em}}
% Extra space after a table row (\\[\ReportRowGap]) and inside multi-line cells
\newlength{\ReportRowGap}\setlength{\ReportRowGap}{6pt}
\newlength{\ReportRowGapLarge}\setlength{\ReportRowGapLarge}{8pt}
\newlength{\ReportCellLineGap}\setlength{\ReportCellLineGap}{3pt}
\newlength{\ReportTitleLineGap}\setlength{\ReportTitleLineGap}{0.3cm}
\newlength{\ReportTitleBlockGap}\setlength{\ReportTitleBlockGap}{1.5cm}
\newlength{\ReportTitleLogoGap}\setlength{\ReportTitleLogoGap}{1cm}
% Check status labels
\newcommand{\ReportPass}{PASS}
\newcommand{\ReportFail}{\textcolor{reportFail}{FAIL}}
% Page-break notices for long tables (added to every longtable by continued_tables)
\newcommand{\ReportContinuedFromNumbered}{\ReportFootnoteFont\textit{\tablename~\thetable{} continued from previous page}}
\newcommand{\ReportContinuedFrom}{\ReportFootnoteFont\textit{Continued from previous page}}
\newcommand{\ReportContinuedOn}{\ReportFootnoteFont\textit{Continued on next page}}
\newcommand{\ReportSmallFont}{\small}
\newcommand{\ReportFootnoteFont}{\footnotesize}
\newcommand{\ReportNormalFont}{\normalsize}
\newcommand{\ReportLargeFont}{\large}
\newcommand{\ReportHeadingFont}{\Large}
\newcommand{\ReportTableLeft}{\setlength{\LTleft}{0pt}\setlength{\LTright}{\fill}}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + head_left + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{\scriptsize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{\scriptsize Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{0pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{0pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + head_left + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{\scriptsize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{\scriptsize Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{0pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{0pt}%
    }%
    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{\scriptsize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{\scriptsize Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\footrule}{\vspace{0pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}
}
\pagestyle{main}
\setstretch{1.15}
\setlength{\emergencystretch}{2em}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
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

\title{\Large\textbf{OsdagBridge} \\ \normalsize Open Source Software for Steel Girder Bridge Design \\ \vspace{2cm} \large Design Report}
\author{}
\date{}

% Chapter / TOC Formatting
\titleformat{\chapter}[block]
  {\normalfont\Large\bfseries\centering}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{0pt}{10pt}
\setcounter{tocdepth}{2}

\begin{document}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ═══════════════════════════════════════════════════════════════════════════════


def toc_section():
    return r"""

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


