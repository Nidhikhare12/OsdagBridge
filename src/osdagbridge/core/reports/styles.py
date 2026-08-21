"""Central report styling and LaTeX layout helpers.

This module is the single source of truth for document geometry, table spacing,
Osdag colours, chart styling, and repeated ``longtable`` headings.  Chapter
generators should describe content; layout policy belongs here.
"""

from __future__ import annotations

import re


OSDAG_GREEN = "#91B014"
PASS_GREEN = "#6E8F00"
FAIL_RED = "#C62828"
GRID_GREY = "#D9D9D9"
TEXT_GREY = "#333333"
INFO_BLUE = "#1565C0"

CHART_FONT_REGULAR = ("arial.ttf", "Arial.ttf")
CHART_FONT_BOLD = ("arialbd.ttf", "Arial Bold.ttf")
CHART_FONT_SIZE = {
    "overall_title": 36,
    "panel_title": 25,
    "axis_title": 16,
    "axis_tick": 17,
    "limit_label": 17,
    "empty_state": 20,
    "value_label": 17,
    "category_label": 15,
    "quantity_title": 27,
    "quantity_tick": 18,
    "quantity_value": 21,
    "quantity_category": 19,
}

DOCUMENT_CLASS_OPTIONS = "12pt,a4paper"
DOCUMENT_LINE_SPACING = "1.15"
INSTITUTION_FOOTER = "Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"

PAGE_MARGIN_LEFT = "22mm"
PAGE_MARGIN_RIGHT = "22mm"
PAGE_MARGIN_TOP = "22mm"
PAGE_MARGIN_BOTTOM = "30mm"
HEADER_HEIGHT = "16pt"
HEADER_SEPARATION = "12pt"
FOOTER_SEPARATION = "20pt"

TABLE_COLUMN_PADDING = "3.5pt"
TABLE_ROW_STRETCH = "1.16"
TABLE_EXTRA_ROW_HEIGHT = "0.8pt"
TABLE_RULE_WIDTH = "0.5pt"
TABLE_PRE_SKIP = "2pt"
TABLE_POST_SKIP = "8pt"
TABLE_START_RESERVE = 12

CHART_DPI = 180
CHART_FIGSIZE = (10.0, 7.2)


def geometry_options() -> str:
    """Return the canonical A4 geometry options."""
    return (
        "a4paper,"
        f"left={PAGE_MARGIN_LEFT},right={PAGE_MARGIN_RIGHT},"
        f"top={PAGE_MARGIN_TOP},bottom={PAGE_MARGIN_BOTTOM},"
        f"headheight={HEADER_HEIGHT},headsep={HEADER_SEPARATION},"
        f"footskip={FOOTER_SEPARATION}"
    )


def table_layout_latex() -> str:
    """Global table and page-break policy inserted in the preamble."""
    return rf"""
% Centralized table layout policy (see reports/styles.py)
\setlength{{\tabcolsep}}{{{TABLE_COLUMN_PADDING}}}
\renewcommand{{\arraystretch}}{{{TABLE_ROW_STRETCH}}}
\setlength{{\LTpre}}{{{TABLE_PRE_SKIP}}}
\setlength{{\LTpost}}{{{TABLE_POST_SKIP}}}
\setlength{{\LTleft}}{{\fill}}
\setlength{{\LTright}}{{\fill}}
\setlength{{\arrayrulewidth}}{{{TABLE_RULE_WIDTH}}}
\setlength{{\extrarowheight}}{{{TABLE_EXTRA_ROW_HEIGHT}}}
\newcolumntype{{L}}[1]{{>{{\raggedright\arraybackslash}}p{{#1}}}}
\newcolumntype{{C}}[1]{{>{{\centering\arraybackslash}}p{{#1}}}}
\newcolumntype{{R}}[1]{{>{{\raggedleft\arraybackslash}}p{{#1}}}}
\BeforeBeginEnvironment{{table}}{{\needspace{{{TABLE_START_RESERVE}\baselineskip}}}}
\newcommand{{\reportsection}}{{\needspace{{6\baselineskip}}}}
% Named spacing commands keep chapter generators free of layout literals.
\newcommand{{\reportrow}}{{\\[6pt]}}
\newcommand{{\reportrowroomy}}{{\\[8pt]}}
\newcommand{{\reportrowtight}}{{\\[3pt]}}
\newcommand{{\reportspacelarge}}{{\vspace{{1em}}}}
\newcommand{{\reportspacemedium}}{{\vspace{{0.8em}}}}
\newcommand{{\reportspacecompact}}{{\vspace{{0.4em}}}}
\newcommand{{\reportspacesmall}}{{\vspace{{0.3em}}}}
\newcommand{{\reportspacehalf}}{{\vspace{{0.5em}}}}
\newcommand{{\reportspacesix}}{{\vspace{{0.6em}}}}
\newcommand{{\reportspacepoint}}{{\vspace{{4pt}}}}
\newcommand{{\reportspaceform}}{{\vspace{{0.4cm}}}}
\newcommand{{\reportspaceformlarge}}{{\vspace{{0.8cm}}}}
\newcommand{{\reportspaceformhalf}}{{\vspace{{0.5cm}}}}
\newcommand{{\reportspacechaptergap}}{{\vspace{{2.2em}}}}
\newcommand{{\reportspacefigurebefore}}{{\vspace{{-0.5em}}}}
\newcommand{{\reportspacefigureafter}}{{\vspace{{0.5em}}}}
"""


def caption_layout_latex() -> str:
    """Return the canonical caption typography and alignment rules."""
    return r"""
\captionsetup{
    labelfont=bf,
    justification=raggedright,
    singlelinecheck=false,
    format=plain
}
"""


def latex_color_definitions() -> str:
    """Return all named LaTeX colours used by report generators."""
    colors = {
        "osdagGreen": OSDAG_GREEN,
        "reportPass": PASS_GREEN,
        "reportFail": FAIL_RED,
        "reportGrid": GRID_GREY,
        "reportText": TEXT_GREY,
        "reportInfo": INFO_BLUE,
    }
    return "\n".join(
        rf"\definecolor{{{name}}}{{HTML}}{{{value.lstrip('#')}}}"
        for name, value in colors.items()
    )


def header_footer_latex(
    project_name: str,
    job_number: str,
    report_date: str,
    report_version: str,
) -> str:
    """Return the canonical report header/footer page styles."""
    common = rf"""
  \fancyhf{{}}
  \fancyhead[L]{{{project_name} $|$ {job_number}}}
  \fancyhead[R]{{{report_date} $|$ {report_version}}}
  \fancyfoot[L]{{{INSTITUTION_FOOTER}}}
  \fancyfoot[C]{{}}
  \fancyfoot[R]{{Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\headrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt \vspace{{2pt}}}}
  \renewcommand{{\footrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt}}
"""
    return rf"""
\fancypagestyle{{main}}{{{common}}}
\fancypagestyle{{plain}}{{{common}}}
\fancypagestyle{{firstpage}}{{
  \fancyhf{{}}
  \renewcommand{{\headrulewidth}}{{0pt}}
  \fancyfoot[L]{{{INSTITUTION_FOOTER}}}
  \fancyfoot[R]{{Page \thepage\ of \pageref{{LastPage}}}}
  \renewcommand{{\footrule}}{{\color{{osdagGreen}}\hrule width\headwidth height 1pt}}
}}
\pagestyle{{main}}
\setstretch{{{DOCUMENT_LINE_SPACING}}}
"""


def _inject_header_into_longtable(match: re.Match[str]) -> str:
    r"""Add ``endfirsthead/endhead`` to one longtable when it lacks them.

    Every report table follows the same opening convention: optional caption,
    first ``\hline``, column-heading row, second ``\hline``.  Repeating that
    small header block is safer and more maintainable than duplicating it in
    dozens of chapter strings.
    """
    block = match.group(0)
    # ``multirow`` cannot split safely across longtable pages: its label can
    # remain anchored on the previous page and extend into the footer (the
    # reported G4 failure).  Keep the label in the first ordinary cell and let
    # the following rows break normally.
    block = re.sub(
        r"\\multirow\{\d+\}\{\*\}\{(\\makecell\{.*?\})\}",
        r"\1",
        block,
    )
    # A longtable caption is a row and must end with ``\\``.  Older chapter
    # templates omitted it, which could put a continuation heading above the
    # first-page caption and intrude into the running header.
    block = re.sub(
        r"(?m)^(\\caption\{.*\})\s*$",
        lambda caption: caption.group(1) + r"\\",
        block,
        count=1,
    )
    reserve = rf"\par\Needspace{{{TABLE_START_RESERVE}\baselineskip}}" + "\n"
    begin_end = block.find("\n")
    if begin_end < 0:
        return reserve + block
    first_hline = block.find(r"\hline", begin_end)
    if first_hline < 0:
        return reserve + block
    second_hline = block.find(r"\hline", first_hline + len(r"\hline"))
    if second_hline < 0:
        return reserve + block
    second_end = second_hline + len(r"\hline")
    header = block[first_hline:second_end]
    caption = re.search(r"\\caption\{(?:\\textbf\{)?([^}\n]+)", block)
    table_name = caption.group(1) if caption else "unnamed longtable"
    if r"\textbf" not in header:
        raise ValueError(
            f"{table_name} must define an explicit bold column-heading row "
            "between its first two \\hline commands"
        )
    if r"\endhead" in block:
        if r"\endfirsthead" not in block:
            raise ValueError(f"{table_name} defines \\endhead without \\endfirsthead")
        prefix, remainder = block.split(r"\endfirsthead", 1)
        repeated_header, suffix = remainder.split(r"\endhead", 1)
        if r"\textbf" not in repeated_header:
            block = prefix + r"\endfirsthead" + "\n" + header + "\n" + r"\endhead" + suffix
        return reserve + block
    repeated = "\n\\endfirsthead\n" + header + "\n\\endhead"
    return reserve + block[:second_end] + repeated + block[second_end:]


_LONGTABLE_RE = re.compile(
    r"\\begin\{longtable\}.*?\\end\{longtable\}",
    flags=re.DOTALL,
)


def ensure_repeated_longtable_headers(latex: str) -> str:
    """Apply centralized chapter-page and longtable layout normalization."""
    latex = _LONGTABLE_RE.sub(_inject_header_into_longtable, latex)
    # The report class forces chapter openings to the ``plain`` style, whose
    # header baseline is unreliable with custom geometry on bundled TeX Live.
    # Reapply the canonical style immediately after every chapter heading.
    return re.sub(
        r"(?m)^(\\chapter\{.*\})$",
        lambda chapter: chapter.group(1) + "\n" + r"\thispagestyle{main}",
        latex,
    )


def report_figure(path: str | None, caption: str, label: str, width: str = "0.96\\textwidth") -> str:
    """Return a consistent report figure block, or an empty string."""
    if not path:
        return ""
    normalized = str(path).replace("\\", "/")
    return rf"""
\begin{{figure}}[H]
\centering
\includegraphics[width={width}]{{{normalized}}}
\caption{{\textbf{{{caption}}}}}
\label{{{label}}}
\end{{figure}}
"""
