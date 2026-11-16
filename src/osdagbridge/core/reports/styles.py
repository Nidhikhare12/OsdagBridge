"""Shared visual language and LaTex helpers for OsdagBridge reports.

Keeping report-wide layout decisions here prevents chapter modules from slowly
drifting apart.  The helpers intentionally emit plain LaTex so individual
chapters remain easy to read and test without a LaTex installation.
"""
from __future__ import annotations
import re
from functools import wraps

BRAND_GREEN = "91B014"
PASS_GREEN = "2E7D32"
FAIL_RED = "C62828"
PAGE_MARGIN = "0.85in"
TABLE_CELL_PADDING_PT = "5"
TABLE_ROW_STRETCH = "1.10"
BODY_FONT_SIZE_PT = "12"

def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    from .report_utils import _tex
    pn = _tex(project_name)
    jn = _tex(job_number)
    rd = _tex(report_date)
    rv = _tex(report_version)
    return "\n\\documentclass[" + BODY_FONT_SIZE_PT + r"""pt,a4paper]{report}
""" + report_layout_tex() + r"""

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{\scriptsize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{\scriptsize Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{{\color{osdagGreen}\hrule width\headwidth height 1pt} \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{0pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{0pt}%
    }%
    {\color{osdagGreen}\hrule width\headwidth height 1pt} \vspace{6pt}%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{\scriptsize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{\scriptsize Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\headrule}{{\color{osdagGreen}\hrule width\headwidth height 1pt} \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{0pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{0pt}%
    }%
    {\color{osdagGreen}\hrule width\headwidth height 1pt} \vspace{6pt}%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{\scriptsize Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
  \fancyfoot[R]{\scriptsize Page \thepage\ of \pageref{LastPage}}
  \renewcommand{\footrule}{\vspace{0pt}{\color{osdagGreen}\hrule width\headwidth height 1pt} \vspace{6pt}}
}
\pagestyle{main}
\setstretch{1.15}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}

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

\begin{document}
"""


def styled_chapter(function):
    """Apply the same table layout policy to every chapter's rendered output."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        return format_tables(function(*args, **kwargs))
    return wrapped


def _group_end(text, start):
    depth = 0
    for index in range(start, len(text)):
        if text[index] == '{' and (index == 0 or text[index - 1] != '\\'):
            depth += 1
        elif text[index] == '}' and (index == 0 or text[index - 1] != '\\'):
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError('Unbalanced LaTeX group in report table')


def format_tables(text):
    """Size fixed-width columns including padding and repeat each table header.

    This adapter handles the existing hand-written chapter templates. It parses
    balanced column/caption groups, preserving multi-line headers and body rows.
    It does not guess data from text or alter any engineering values.
    """
    def table(match):
        block = match.group(0)
        start = block.index('{', len(r'\begin{longtable}'))
        end = _group_end(block, start)
        spec = block[start + 1:end - 1]
        widths = re.findall(r'\{([0-9.]+)cm\}', spec)
        count = len(widths)
        if widths:
            total = sum(map(float, widths))
            spec = re.sub(r'\{([0-9.]+)cm\}', lambda m:
                '{\\dimexpr ' + f'{float(m[1])/total:.6f}' +
                r'\linewidth-2\tabcolsep-1.6\arrayrulewidth\relax}', spec)
        rest = block[end:]
        if r'\caption{' in rest:
            cap = rest.index(r'\caption{') + len(r'\caption')
            ce = _group_end(rest, cap)
            tail = rest[ce:]
            if not tail.lstrip().startswith(r'\\'):
                rest = rest[:ce] + r'\\' + tail
        # Repair the existing empty continuation header in Chapter 2.
        rest = re.sub(r'\\endfirsthead\s*\\endhead', '', rest)
        if r'\endhead' not in rest:
            first_rule = rest.index(r'\hline')
            head_start = first_rule + len(r'\hline')
            next_rule = rest.index(r'\hline', head_start)
            head = rest[head_start:next_rule].strip()
            if not head.startswith((r'\textbf', r'\multirow')):
                if count != 2:
                    raise ValueError('Missing report table header')
                head = r'\textbf{Parameter} & \textbf{Value} \\'
                body = rest[head_start:]
            else:
                body = rest[next_rule + len(r'\hline'):]
            rest = rest[:first_rule] + repeating_longtable_header(head, columns=count) + body
        return r'\begin{longtable}{' + spec + '}' + rest
    return re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}', table, text, flags=re.S)


def report_layout_tex() -> str:
    """Return the shared packages and safe printable-area settings."""
    return rf"""
\usepackage[a4paper,top={PAGE_MARGIN},bottom=0.95in,left={PAGE_MARGIN},right={PAGE_MARGIN},
            headheight=20pt,headsep=18pt,footskip=36pt]{{geometry}}
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


def repeating_longtable_header(header: str, continuation: str = "Table continued from previous page", columns: int = 2) -> str:
    """Return a complete LongTable header that repeats after each page break."""
    return rf"""\hline
{header}
\hline
\endfirsthead
\multicolumn{{{columns}}}{{l}}{{\small\itshape {continuation}}} \\
\hline
{header}
\hline
\endhead
\hline
\multicolumn{{{columns}}}{{r}}{{\small\itshape Continued on next page}} \\
\endfoot
\hline
\endlastfoot
"""


def chart_tex(path: str, caption: str, width: str = "0.88\\textwidth") -> str:
    """Render a generated chart only when a path was produced."""
    if not path:
        return ""
    from pylatex import Figure, NoEscape
    figure = Figure(position='H')
    figure.add_image(path.replace('\\', '/'), width=NoEscape(width))
    figure.add_caption(caption)
    return '\n' + figure.dumps() + '\n'
