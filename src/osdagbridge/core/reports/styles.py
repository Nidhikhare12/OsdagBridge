"""Centralized formatting and style configuration for OsdagBridge reports.

This module is the **single source of truth** for every visual attribute of
the generated design report: page geometry, colour palette, table padding and
rules, header/footer theme, float placement and the Matplotlib style used by
the generated charts.

Chapter modules should import their layout rules from here instead of
hard-coding them.  :func:`apply_global_styles` is called once on the fully
assembled LaTeX source, so even legacy chapters that still contain raw LaTeX
pick up the global table-header and page-break rules.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Document / page geometry
# ---------------------------------------------------------------------------
DOCUMENT_CLASS_OPTIONS = "12pt,a4paper"
PAPER_SIZE = "a4paper"
PAGE_MARGIN = "1in"
DOCUMENT_STRETCH = 1.15

# Minimum number of baseline skips that must remain before a long table or a
# section heading.  This is the page-bottom threshold that keeps content from
# bleeding into the footer box.
PAGE_BOTTOM_THRESHOLD_LINES = 8

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
COLOR_OSDAG_GREEN_HEX = "91B014"
COLOR_UR_PASS = "#2E7D32"
COLOR_UR_FAIL = "#C62828"
COLOR_THRESHOLD_RED = "#C00000"
COLOR_STEEL = "#546E7A"
COLOR_CONCRETE = "#90A4AE"
COLOR_REBAR = "#8D6E63"
COLOR_TEXT = "#222222"
COLOR_GRID = "#DDDDDD"
COLOR_AXIS = "#666666"
COLOR_TABLE_HEAD_HEX = "EAF2D6"
COLOR_RULE_HEX = "B7C9A0"

LATEX_COLOR_DEFINITIONS = (
    r"\definecolor{osdagGreen}{HTML}{" + COLOR_OSDAG_GREEN_HEX + "}" "\n"
    r"\definecolor{urPass}{HTML}{2E7D32}" "\n"
    r"\definecolor{urFail}{HTML}{C62828}" "\n"
    r"\definecolor{thresholdRed}{HTML}{C00000}" "\n"
    r"\definecolor{tableHead}{HTML}{" + COLOR_TABLE_HEAD_HEX + "}" "\n"
    r"\definecolor{tableRule}{HTML}{" + COLOR_RULE_HEX + "}"
)

LATEX_CAPTION_SETTINGS = (
    r"\captionsetup{font=small,labelfont=bf,labelsep=period,skip=6pt,"
    r"justification=raggedright,singlelinecheck=false}"
)

LATEX_SECTION_SETTINGS = (
    r"\titleformat{\section}{\Large\bfseries\color{osdagGreen}}"
    r"{\thesection}{1em}{}" "\n"
    r"\titlespacing*{\section}{0pt}{12pt}{6pt}" "\n"
    r"\titleformat{\subsection}{\large\bfseries\color{osdagGreen}}"
    r"{\thesubsection}{1em}{}" "\n"
    r"\titlespacing*{\subsection}{0pt}{8pt}{4pt}"
)

# ---------------------------------------------------------------------------
# Table layout
# ---------------------------------------------------------------------------
TAB_COLSEP = "6pt"
ARRAY_STRETCH = 1.12
ARRAY_RULE_WIDTH = "0.5pt"
EXTRA_ROW_HEIGHT = "0.6pt"
LT_PRE = "0pt"
LT_POST = "6pt"
TABLE_TOP_SKIP = r"\vspace{1em}"
SECTION_SKIP = r"\vspace{0.4cm}"
FIGURE_SKIP = r"\vspace{4pt}"

LATEX_TABLE_SETTINGS = (
    r"\setlength{\tabcolsep}{" + TAB_COLSEP + "}" "\n"
    r"\renewcommand{\arraystretch}{" + f"{ARRAY_STRETCH}" + "}" "\n"
    r"\setlength{\LTpre}{" + LT_PRE + "}" "\n"
    r"\setlength{\LTpost}{" + LT_POST + "}" "\n"
    r"\setlength{\arrayrulewidth}{" + ARRAY_RULE_WIDTH + "}" "\n"
    r"\setlength{\extrarowheight}{" + EXTRA_ROW_HEIGHT + "}" "\n"
    r"\arrayrulecolor{tableRule}"
)

# Header/footer theme shared by every page style in report_generator.preamble.
HEADER_RULE = (
    r"\renewcommand{\headrule}{\color{osdagGreen}\hrule width\headwidth height 1pt \vspace{2pt}}"
)
FOOTER_TEXT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"


# ---------------------------------------------------------------------------
# Helpers used by chapter generators
# ---------------------------------------------------------------------------
def table_header_row(*labels: str) -> str:
    """Return a bold header row for a longtable, using the global rule style."""
    cells = " & ".join(r"\textbf{" + str(label) + "}" for label in labels)
    return cells + r" \\[6pt]" + "\n" + r"\hline" + "\n"


def figure_block(path: str, caption: str, label: str,
                 width: str = r"0.92\linewidth") -> str:
    """Return a LaTeX ``figure`` block for an embedded chart asset."""
    safe = path.replace("\\", "/")
    return (
        r"\begin{figure}[htbp]" "\n"
        r"\centering" "\n"
        r"\includegraphics[width=" + width + r"]{" + safe + "}" "\n"
        r"\caption{" + caption + "}" "\n"
        r"\label{" + label + "}" "\n"
        r"\end{figure}" "\n"
    )


def matplotlib_rc() -> dict:
    """Return the global Matplotlib rcParams used for every generated chart."""
    return {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelcolor": COLOR_TEXT,
        "axes.edgecolor": COLOR_AXIS,
        "axes.facecolor": "#FAFAFA",
        "axes.grid": True,
        "grid.color": COLOR_GRID,
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "xtick.color": COLOR_TEXT,
        "ytick.color": COLOR_TEXT,
        "figure.facecolor": "white",
        "legend.frameon": False,
    }


# ---------------------------------------------------------------------------
# Global post-processing of the assembled LaTeX source
# ---------------------------------------------------------------------------
_LONGTABLE_RE = re.compile(
    r"(\\begin\{longtable\}\{.*?\}\s*\n)(.*?)(\\end\{longtable\})",
    re.DOTALL,
)
_HEADER_RULE_RE = re.compile(r"^\s*\\(?:hline|toprule)\b")
_FOLLOW_RULE_RE = re.compile(r"^\s*\\(?:hline|midrule|bottomrule)\b")
_HEADER_END_RE = re.compile(r"\\\\\s*(?:\[[^\]]*\])?\s*$")


def _repeat_longtable_headers(tex: str) -> str:
    """Insert ``\\endfirsthead``/``\\endhead`` into every longtable that lacks
    them, so the column header row is repeated on each page of a split table.
    """
    def _fix(match: "re.Match[str]") -> str:
        begin, body, end = match.group(1), match.group(2), match.group(3)
        if r"\endhead" in body:
            return begin + body + end

        lines = body.splitlines(keepends=True)
        first_rule = next(
            (i for i, line in enumerate(lines) if _HEADER_RULE_RE.match(line)),
            None,
        )
        if first_rule is None:
            return begin + body + end

        i = first_rule
        header: list[str] = []
        while i < len(lines):
            header.append(lines[i])
            if _HEADER_END_RE.search(lines[i].rstrip()):
                i += 1
                break
            i += 1
        if i >= len(lines) or not header:
            return begin + body + end
        if i < len(lines) and _FOLLOW_RULE_RE.match(lines[i]):
            header.append(lines[i])
            i += 1

        # Shade the header row (both first page and continuation) without
        # touching multi-line \makecell arguments or rule lines.
        def _shade(header_lines):
            shaded = []
            for line in header_lines:
                stripped = line.rstrip()
                if (_HEADER_END_RE.search(stripped)
                        and r"\rowcolor" not in line
                        and r"\makecell" not in line
                        and r"\caption" not in line
                        and line.count("{") == line.count("}")):
                    indent = line[:len(line) - len(line.lstrip())]
                    line = (indent + r"\rowcolor{tableHead} "
                            + line[len(indent):])
                shaded.append(line)
            return shaded

        first_header = "".join(_shade(header))
        repeat = "".join(_shade(header))
        fixed_body = (
            "".join(lines[:first_rule])
            + first_header
            + r"\endfirsthead" + "\n"
            + repeat
            + r"\endhead" + "\n"
            + "".join(lines[i:])
        )
        return begin + fixed_body + end

    return _LONGTABLE_RE.sub(_fix, tex)


def _protect_headings(tex: str) -> str:
    """Keep section/chapter headings away from the footer margin."""
    need = r"\needspace{" + str(PAGE_BOTTOM_THRESHOLD_LINES) + r"\baselineskip}" "\n"
    # A callable replacement is required: a plain string would make re.sub
    # interpret "\n"/"\b" inside the LaTeX command as escape sequences.
    return re.sub(
        r"(?m)^(\\(?:chapter|section|subsection)\{)",
        lambda match: need + match.group(1),
        tex,
    )


def apply_global_styles(tex: str) -> str:
    """Apply all cross-cutting layout rules to the assembled report source."""
    return _protect_headings(_repeat_longtable_headers(tex))

