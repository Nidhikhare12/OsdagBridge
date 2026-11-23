"""Central formatting theme for the OsdagBridge LaTeX report.

Every chapter generator and the report preamble take their colours, status
markup, table geometry, and figure defaults from this module instead of
hard-coding them. To restyle the report, change the values here once.

The constants below intentionally reproduce the markup the report already
emits; helpers exist so that new code never re-derives them by hand.
"""

# ---------------------------------------------------------------------------
# Brand and status colours (LaTeX colour names or HTML hex without '#')
# ---------------------------------------------------------------------------

COLOR_BRAND = "91B014"          # osdagGreen, the Osdag brand green
COLOR_PASS = "black"
COLOR_FAIL = "red"
COLOR_LOG_WARNING = "blue"
COLOR_LOG_ERROR = "red"
COLOR_LOG_INFO = "osdagGreen"   # uses the brand colour defined in the preamble

#: Preamble line defining the brand colour used across the report.
COLOR_DEF_BRAND = (
    "\\definecolor{osdagGreen}{HTML}{" + COLOR_BRAND + "}"
)

# ---------------------------------------------------------------------------
# Body text
# ---------------------------------------------------------------------------

BODY_LINE_STRETCH = "1.15"      # argument to \setstretch

# ---------------------------------------------------------------------------
# Table geometry (values consumed by the preamble)
# ---------------------------------------------------------------------------

TABCOLSEP = "6pt"               # default cell padding
TABCOLSEP_TIGHT = "3.5pt"       # dense data tables (\begingroup-scoped)
ARRAY_STRETCH = "1.12"          # row height multiplier
LT_PRE = "0pt"                  # skip before a longtable
LT_POST = "6pt"                 # skip after a longtable
ARRAY_RULE_WIDTH = "0.5pt"      # table outline thickness
EXTRA_ROW_HEIGHT = "0.6pt"      # small extra row height for clarity
TABLE_MIN_SPACE = "5\\baselineskip"  # page-break guard before tables

#: Preamble block: table/figure numbering and table geometry.
PREAMBLE_TABLE_LAYOUT = (
    "\\numberwithin{table}{chapter}\n"
    "\\numberwithin{figure}{chapter}\n"
    "% Table layout and spacing: consistent padding, row height, and longtable pre/post skips\n"
    "\\setlength{\\tabcolsep}{" + TABCOLSEP + "}\n"
    "\\renewcommand{\\arraystretch}{" + ARRAY_STRETCH + "}\n"
    "\\setlength{\\LTpre}{" + LT_PRE + "}\n"
    "\\setlength{\\LTpost}{" + LT_POST + "}\n"
    "% Table rules (outline thickness) and small extra row height for clarity\n"
    "\\setlength{\\arrayrulewidth}{" + ARRAY_RULE_WIDTH + "}\n"
    "\\setlength{\\extrarowheight}{" + EXTRA_ROW_HEIGHT + "}\n"
    "\n"
    "% Prevent tables from overflowing past the page bottom:\n"
    "% if fewer than 5 baseline-skips remain, break to the next page first.\n"
    "\\BeforeBeginEnvironment{table}{\\needspace{" + TABLE_MIN_SPACE + "}}\n"
    "\\BeforeBeginEnvironment{longtable}{\\needspace{" + TABLE_MIN_SPACE + "}}"
)

#: Preamble block: \nbcline, a page-break-safe replacement for \cline inside
#: \multirow blocks. A \cline rule is an alignment row followed by a negative
#: \vskip, and that skip is a legal page-break point that \\* cannot guard, so
#: a longtable can still split a \multirow block at a \cline and leave the
#: label floating into the footer area. \nbcline draws the same partial rule
#: but shields the skip with a penalty, keeping each block on one page.
PREAMBLE_NBCLINE = (
    r"\makeatletter" "\n"
    r"\def\@nbcline#1-#2\@nil{%" "\n"
    r"  \omit" "\n"
    r"  \@multicnt#1\relax" "\n"
    r"  \advance\@multispan\m@ne" "\n"
    r"  \ifnum\@multicnt=\@ne\@firstofone{&\omit}\fi" "\n"
    r"  \@multicnt#2\relax" "\n"
    r"  \advance\@multicnt-#1\relax" "\n"
    r"  \advance\@multispan\@ne" "\n"
    r"  \leaders\hrule\@height\arrayrulewidth\hfill" "\n"
    r"  \cr" "\n"
    r"  \noalign{\penalty\@M\vskip-\arrayrulewidth}}" "\n"
    r"\newcommand{\nbcline}[1]{\@nbcline#1\@nil}" "\n"
    r"\makeatother"
)

#: Preamble block: caption formatting shared by all figures and tables.
PREAMBLE_CAPTIONS = (
    "\\captionsetup{\n"
    "    labelfont=bf,\n"
    "    justification=raggedright,\n"
    "    singlelinecheck=false,\n"
    "    format=plain\n"
    "}"
)

#: Preamble block: fixed-width paragraph column types used in every table.
PREAMBLE_COLUMN_TYPES = (
    "\\newcolumntype{L}[1]{>{\\raggedright\\arraybackslash}p{#1}}\n"
    "\\newcolumntype{C}[1]{>{\\centering\\arraybackslash}p{#1}}\n"
    "\\newcolumntype{R}[1]{>{\\raggedleft\\arraybackslash}p{#1}}"
)

# ---------------------------------------------------------------------------
# Figure defaults
# ---------------------------------------------------------------------------

FIG_WIDTH = "0.9\\textwidth"        # default includegraphics width
FIG_WIDTH_FULL = "\\textwidth"      # wide drawings
FIG_PLACEHOLDER_WIDTH = "0.97\\textwidth"  # fbox placeholder width

# ---------------------------------------------------------------------------
# Status and log markup helpers
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
DASH = "---"


def tex_color(color, text):
    """Wrap text in a \\textcolor command."""
    return "\\textcolor{" + color + "}{" + str(text) + "}"


def status(ok, colored_pass=False):
    """PASS/FAIL markup for design checks.

    ok=True renders PASS (plain, or in COLOR_PASS when colored_pass=True),
    ok=False renders FAIL in COLOR_FAIL.
    """
    if ok:
        return tex_color(COLOR_PASS, PASS) if colored_pass else PASS
    return tex_color(COLOR_FAIL, FAIL)


def status_or_dash(ok, colored_pass=False):
    """status() that tolerates an unknown result (None) as a dash."""
    if ok is None:
        return DASH
    return status(ok, colored_pass=colored_pass)


def colorize_result(text):
    """Recolour an existing PASS/FAIL string: red for FAIL, else unchanged."""
    s = str(text)
    if FAIL in s.upper():
        return tex_color(COLOR_FAIL, s)
    return s


def ur_markup(value, fmt="{:.2f}"):
    """Format a utilisation ratio; red when it exceeds 1.0."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ""
    s = fmt.format(f)
    return tex_color(COLOR_FAIL, s) if f > 1.0 else s


def log_line_color(line):
    """Colour name for a design-log line, or None to skip the line."""
    upper = line.upper()
    if "WARNING" in upper:
        return COLOR_LOG_WARNING
    if "ERROR" in upper:
        return COLOR_LOG_ERROR
    if "INFO" in upper:
        return COLOR_LOG_INFO
    return None


# ---------------------------------------------------------------------------
# Longtable repeating headers
# ---------------------------------------------------------------------------

def repeated_header(header_rows):
    """Repeat longtable header rows on every continuation page.

    header_rows is the header block including its trailing \\\\ and \\hline
    lines. The returned block prints the header at the top of the first page
    (\\endfirsthead) and again at the top of every page the table breaks onto
    (\\endhead).
    """
    return header_rows + "\n\\endfirsthead\n" + header_rows + "\n\\endhead"


# Chapter heading variants used by the contents and the main report body.
def chapter_heading(before="-30pt"):
    return (r"\titleformat{\chapter}[block]{\normalfont\Large\bfseries\centering}"
            r"{\thechapter}{1em}{}" "\n"
            r"\titlespacing*{\chapter}{0pt}{" + before + r"}{10pt}")


def table_padding(size):
    return r"\setlength{\tabcolsep}{" + size + "}"


TABCOLSEP_COMPACT = "4pt"
TABCOLSEP_ANALYSIS = "3pt"
ANALYSIS_ARRAY_STRETCH = "1.25"


def document_preamble(pn, jn, rd, rv):
    """Full document layout; arguments are already LaTeX-escaped."""
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

""" + PREAMBLE_CAPTIONS + r"""
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

""" + PREAMBLE_TABLE_LAYOUT + r"""

""" + PREAMBLE_NBCLINE + r"""

""" + COLOR_DEF_BRAND + r"""

% Footer rule: fancyhdr sets \footrule above the footer text, so an unscoped
% \color{osdagGreen} leaks into the text. Each rule colour is grouped in braces.
% Footer text shared by all page styles
\newcommand{\osdagFootL}{Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay}
% Total comes from LastPage, so it only matches the PDF page count while the
% page counter runs unbroken from the cover (see the setcounter after titlepage).
\newcommand{\osdagFootR}{Page \thepage\ of \pageref{LastPage}}

\fancypagestyle{main}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{\osdagFootL}
  \fancyfoot[R]{\osdagFootR}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    {\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}%
  }
}
\fancypagestyle{plain}{
  \fancyhf{}
  \fancyhead[L]{""" + pn + r""" $|$ """ + jn + r"""}
  \fancyhead[R]{""" + rd + r""" $|$ """ + rv + r"""}
  \fancyfoot[L]{\osdagFootL}
  \fancyfoot[R]{\osdagFootR}
  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}
  \renewcommand{\footrule}{%
    \ifbool{hasSDonPage}{%
      \vspace{-20pt}%
      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{* Software default value}}\hfil}%
      \vspace{4pt}%
    }{%
      \vspace{-8pt}%
    }%
    {\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}%
  }
}
\fancypagestyle{firstpage}{
  \fancyhf{}
  \renewcommand{\headrulewidth}{0pt}
  \fancyfoot[L]{\osdagFootL}
  \fancyfoot[R]{\osdagFootR}
  \renewcommand{\footrule}{\vspace{-8pt}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}}
}
\pagestyle{main}
\setstretch{""" + BODY_LINE_STRETCH + r"""}

% Custom Commands
\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}
\newcommand{\todo}[1]{\colorbox{yellow}{TODO: #1}}
""" + PREAMBLE_COLUMN_TYPES + r"""

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


def contents_layout():
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



def chapter_title(title, numbered=True):
    """Shared chapter command; title is report-authored LaTeX."""
    return (r"\chapter{" if numbered else r"\chapter*{") + title + "}"


FIG_WIDTH_DRAWING = r"0.85\textwidth"
