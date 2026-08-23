"""
Centralized style/formatting configuration for OsdagBridge report generation.
Single source of truth for page geometry, colors, spacing, and table rules.
Chapter/generator scripts should import from this module rather than
hardcoding formatting values.
"""

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
PAGE_MARGIN = "1in"
PAGE_SIZE = "a4paper"
FONT_SIZE = "12pt"
LINE_STRETCH = "1.15"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
COLOR_OSDAG_GREEN_HEX = "91B014"
COLOR_TODO_HIGHLIGHT = "yellow"

# ---------------------------------------------------------------------------
# Table styling
# ---------------------------------------------------------------------------
TABLE_COL_SEP = "6pt"
TABLE_ROW_STRETCH = "1.12"
LONGTABLE_PRE_SKIP = "0pt"
LONGTABLE_POST_SKIP = "6pt"
TABLE_RULE_WIDTH = "0.5pt"
TABLE_EXTRA_ROW_HEIGHT = "0.6pt"
TABLE_MIN_SPACE_BEFORE_BREAK = "5\\baselineskip"  # needspace threshold

# ---------------------------------------------------------------------------
# Footer / header text
# ---------------------------------------------------------------------------
FOOTER_ORG_TEXT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
FOOTER_PAGE_TEXT = r"Page \thepage\ of \pageref{LastPage}"
FOOTNOTE_SOFTWARE_DEFAULT = r"* Software default value"

# ---------------------------------------------------------------------------
# LaTeX packages required by the report (single list, order matters)
# ---------------------------------------------------------------------------
PACKAGES = [
    r"\usepackage[a4paper, margin=" + PAGE_MARGIN + r"]{geometry}",
    r"\usepackage{graphicx}",
    r"\usepackage{amsmath}",
    r"\usepackage{amssymb}",
    r"\usepackage{booktabs}",
    r"\usepackage{array}",
    r"\usepackage{tabularx}",
    r"\usepackage{float}",
    r"\usepackage{fancyhdr}",
    r"\usepackage[hidelinks]{hyperref}",
    r"\usepackage{xcolor}",
    r"\usepackage{setspace}",
    r"\usepackage{enumitem}",
    r"\usepackage{caption}",
    r"\usepackage{subcaption}",
    r"\usepackage{multirow}",
    r"\usepackage{colortbl}",
    r"\usepackage{longtable}",
    r"\usepackage{titlesec}",
    r"\usepackage{titletoc}",
    r"\usepackage{lastpage}",
    r"\usepackage{makecell}",
    r"\usepackage{etoolbox}",
    r"\usepackage{needspace}",
]


def get_table_spacing_block():
    """LaTeX commands controlling table/longtable spacing, padding, and
    page-break behaviour. Centralized so all spacing tweaks happen here."""
    return "\n".join([
        r"\setlength{\LTleft}{\fill}",
        r"\setlength{\LTright}{\fill}",
        r"\numberwithin{table}{chapter}",
        r"\numberwithin{figure}{chapter}",
        r"\setlength{\tabcolsep}{" + TABLE_COL_SEP + r"}",
        r"\renewcommand{\arraystretch}{" + TABLE_ROW_STRETCH + r"}",
        r"\setlength{\LTpre}{" + LONGTABLE_PRE_SKIP + r"}",
        r"\setlength{\LTpost}{" + LONGTABLE_POST_SKIP + r"}",
        r"\setlength{\arrayrulewidth}{" + TABLE_RULE_WIDTH + r"}",
        r"\setlength{\extrarowheight}{" + TABLE_EXTRA_ROW_HEIGHT + r"}",
        r"\BeforeBeginEnvironment{table}{\needspace{" + TABLE_MIN_SPACE_BEFORE_BREAK + r"}}",
        r"\BeforeBeginEnvironment{longtable}{\needspace{" + TABLE_MIN_SPACE_BEFORE_BREAK + r"}}",
    ])


def get_color_definitions():
    return r"\definecolor{osdagGreen}{HTML}{" + COLOR_OSDAG_GREEN_HEX + r"}"


def get_pagestyle_block(style_name, project_name_tex, job_number_tex,
                         report_date_tex, report_version_tex):
    """Build a fancyhdr pagestyle block (used for 'main' and 'plain' styles,
    which are currently identical). Centralizing this avoids the duplicate
    definitions that existed before."""
    return (
        r"\fancypagestyle{" + style_name + r"}{" + "\n"
        r"  \fancyhf{}" + "\n"
        r"  \fancyhead[L]{" + project_name_tex + r" $|$ " + job_number_tex + r"}" + "\n"
        r"  \fancyhead[R]{" + report_date_tex + r" $|$ " + report_version_tex + r"}" + "\n"
        r"  \fancyfoot[L]{" + FOOTER_ORG_TEXT + r"}" + "\n"
        r"  \fancyfoot[R]{" + FOOTER_PAGE_TEXT + r"}" + "\n"
        r"  \renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}" + "\n"
        r"  \renewcommand{\footrule}{%" + "\n"
        r"    \ifbool{hasSDonPage}{%" + "\n"
        r"      \vspace{-20pt}%" + "\n"
        r"      \hbox to \headwidth{\textcolor{black}{\footnotesize\textit{" + FOOTNOTE_SOFTWARE_DEFAULT + r"}}\hfil}%" + "\n"
        r"      \vspace{4pt}%" + "\n"
        r"    }{%" + "\n"
        r"      \vspace{-8pt}%" + "\n"
        r"    }%" + "\n"
        r"    \color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}%" + "\n"
        r"  }" + "\n"
        r"}"
    )


def get_firstpage_style_block():
    return (
        r"\fancypagestyle{firstpage}{" + "\n"
        r"  \fancyhf{}" + "\n"
        r"  \renewcommand{\headrulewidth}{0pt}" + "\n"
        r"  \fancyfoot[L]{" + FOOTER_ORG_TEXT + r"}" + "\n"
        r"  \fancyfoot[R]{" + FOOTER_PAGE_TEXT + r"}" + "\n"
        r"  \renewcommand{\footrule}{\vspace{-8pt}\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{6pt}}" + "\n"
        r"}"
    )


def get_custom_commands():
    return "\n".join([
        r"\newcommand{\placeholder}[1]{\textit{\textless #1\textgreater}}",
        r"\newcommand{\todo}[1]{\colorbox{" + COLOR_TODO_HIGHLIGHT + r"}{TODO: #1}}",
        r"\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}",
    ])


import re

# ---------------------------------------------------------------------------
# Longtable repeat-header post-processor  (Phase 2, Requirement 1)
# ---------------------------------------------------------------------------
# All report tables already use the `longtable` environment (good — that's
# what allows page-breaking), but none of them define \endfirsthead /
# \endhead / \endfoot, so LaTeX treats the caption+header block as a
# one-time first row instead of a repeating one. Rather than hand-edit each
# of the ~30 table call sites in chap3.py / chap5.py (error-prone, and this
# is exactly the kind of cross-cutting formatting rule that belongs here per
# the single-source-of-truth requirement), this function is run once on the
# fully-assembled .tex string and mechanically rewrites every matching
# longtable block to repeat its header on every page.
#
# Matches the consistent pattern used throughout the codebase:
#   \begin{longtable}{<colspec>}
#   \caption{<caption>}
#   \hline
#   <header row> \\[optional-spacing]
#   \hline
#   <body...>
#   \end{longtable}
#
# Tables that don't match this exact shape are left untouched (non-destructive).

_LONGTABLE_HEAD_RE = re.compile(
    # Colspec is captured up to the last '}' on its own line — greedy match
    # is required here because column macros like L{5.5cm} contain their
    # own nested braces, so a naive [^}]* would stop at the wrong '}'.
    r"\\begin\{longtable\}\{(?P<colspec>[^\n]*)\}[ \t]*\n"
    # Caption line optionally ends with a stray '\\' (seen in a few tables).
    r"\\caption\{(?P<caption>.*?)\}(?P<trailing_slashes>[ \t]*\\\\)?[ \t]*\n"
    r"\\hline[ \t]*\n"
    # Header is a tempered dot: it can span multiple lines (some header
    # rows wrap), but is explicitly forbidden from ever crossing a \hline.
    # Without this, when the trailing negative lookahead below rejects an
    # already-instrumented table, the engine can backtrack and let this
    # group's .*? swallow straight past that table's own \hline/\endhead
    # markers hunting for a later position that satisfies the lookahead —
    # producing a match that starts in the right place but ends many rows
    # too far in. Reproduced and confirmed against the real document.
    r"(?P<header>(?:(?!\\hline).)*?\\\\(?:\[[^\]]*\])?)[ \t]*\n"
    r"\\hline[ \t]*\n"
    # Negative lookahead: skip tables that already have a manual
    # \endfirsthead/\endhead stub (found in one table sourced from a module
    # outside chap3.py/chap5.py) so we never double-inject repeat-header
    # markup into an already-instrumented table.
    r"(?!\s*\\end(?:firsthead|head))",
    re.DOTALL,
)


def _count_columns(colspec: str) -> int:
    """Count column definitions in a longtable colspec like
    '|C{2.0cm}|L{2.0cm}|L{2.2cm}|'. Splitting on '|' is safe here because
    none of the column type macros used in this codebase (C{}, L{}, p{},
    >{\\centering\\arraybackslash}p{}, etc.) contain a literal '|'."""
    return len([c for c in colspec.split("|") if c.strip()])


def _inject_repeat_head(match: "re.Match") -> str:
    colspec = match.group("colspec")
    caption = match.group("caption")
    header = match.group("header").strip()
    ncols = _count_columns(colspec) or 1

    # Check if the matched caption line already ends in \\
    if match.group("trailing_slashes"):
        return match.group(0)

    cont_prev = (
        r"\multicolumn{" + str(ncols) + r"}{l}{\small\itshape "
        r"continued from previous page} \\"
    )
    cont_next = (
        r"\multicolumn{" + str(ncols) + r"}{r}{\small\itshape "
        r"continued on next page} \\"
    )

    # Standard longtable repeat-header/footer idiom. (An earlier version of
    # this function dropped \endfirsthead/\endfoot/\endlastfoot after
    # appearing to reproduce a compile failure in isolated testing — that
    # turned out to be a pre-existing TeX-Live-version quirk in the
    # sandbox used to test this, reproduced identically by the untouched,
    # already-known-good Report-Before.tex with zero changes applied. It is
    # not something this transform introduces. Re-verify end-to-end on the
    # actual OsdagBridge build environment before merging.)
    lines = [
        r"\begin{longtable}{" + colspec + "}",
        r"\caption{" + caption + r"} \\",
        r"\hline",
        header,
        r"\hline",
        r"\endfirsthead",
        cont_prev,
        r"\hline",
        header,
        r"\hline",
        r"\endhead",
        r"\hline",
        cont_next,
        r"\endfoot",
        r"\hline",
        r"\endlastfoot",
        "",  # trailing newline before table body resumes
    ]
    return "\n".join(lines)


def add_longtable_repeat_headers(tex: str) -> str:
    """Rewrite every longtable in the given LaTeX source so its caption +
    header row repeats on every page it spans. Call this once on the fully
    assembled document (after all chapters are concatenated), not on
    individual chapter fragments, since it's a cheap single regex pass and
    keeps chapter modules free of layout boilerplate."""
    return _LONGTABLE_HEAD_RE.sub(_inject_repeat_head, tex)


def build_preamble(pn, jn, rd, rv):
    """Full LaTeX preamble, single source of truth for document class,
    packages, table spacing, colors, header/footer, and custom commands.
    pn/jn/rd/rv = project name / job number / report date / report version
    (already LaTeX-escaped by the caller)."""
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

\definecolor{osdagGreen}{HTML}{91B014}

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

\begin{document}
"""