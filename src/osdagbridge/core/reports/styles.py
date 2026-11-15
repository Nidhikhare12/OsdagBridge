"""Central style configuration for the OsdagBridge PDF design report.

Single source of truth for everything that decides how the document *looks*:
page geometry, colour palette, table presets and the LaTeX fragment builders
used by the chapter modules.

Rules for chapter modules (chap1..chap9, executive_summary):

* never write ``\\setlength`` by hand -- use ``table_setup()`` /
  ``longtable()`` with an override argument
* never write a hex colour -- import the name from this module
* never hand-assemble a ``longtable`` environment -- call ``longtable()``
  so that every table repeats its header row across page breaks

The builders return plain LaTeX strings because the report is assembled by
string concatenation (there is no PyLaTeX dependency in this project).
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

#: Osdag brand green -- used for the header/footer rules.
OSDAG_GREEN = "91B014"

#: Fill for table header rows (reserved for future use).
TABLE_HEADER_BG = "E8F0D0"

#: Fill for alternating table rows (reserved for future use).
TABLE_ZEBRA_BG = "F5F7EF"

#: Rule colour used above/below table bodies (reserved for future use).
RULE_COLOR = "A6C63B"

#: Utilisation-ratio chart colours: demand/capacity <= 1.0 vs > 1.0.
UR_PASS_COLOR = "4E7A0A"
UR_FAIL_COLOR = "C00000"

#: Semantic text colours for values printed inside tables.  ``role`` names are
#: used by :func:`color` so that no chapter module ever writes a colour name.
TEXT_COLORS = {
    "user": "0000CC",      # value entered by the user
    "default": "C00000",   # software / code default
    "code": OSDAG_GREEN,   # clause / code reference
    "pass": UR_PASS_COLOR,
    "fail": UR_FAIL_COLOR,
}

#: LaTeX colour names emitted by :func:`color_defs` for the roles above.
_COLOR_NAMES = {
    "user": "valUser",
    "default": "valDefault",
    "code": "valCode",
    "pass": "urPass",
    "fail": "urFail",
}


# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
#: Options passed to the ``geometry`` package.
#:
#: ``headheight`` / ``headsep`` / ``footskip`` / ``includeheadfoot`` reserve
#: real space for the fancyhdr header and footer so that a table row can never
#: collide with the footer rule at the bottom of a page.
PAGE = {
    "paper": "a4paper",
    "margin": "1in",
    "headheight": "14pt",
    "headsep": "10pt",
    "footskip": "28pt",
    "includeheadfoot": True,
}

#: ``\raggedbottom`` prevents LaTeX from stretching a nearly-empty page and
#: pushing the last table row into the footer.
RAGGED_BOTTOM = True


# ---------------------------------------------------------------------------
# Table presets
# ---------------------------------------------------------------------------
TABLE = {
    "tabcolsep": "4pt",
    "arraystretch": "1.12",
    "ltpre": "0pt",
    "ltpost": "6pt",
    "arrayrulewidth": "0.5pt",
    "extrarowheight": "0.6pt",
    "needspace": "5\\baselineskip",
}

#: Space above/below every caption; overrides LaTeX's default gap.
CAPTION = {"above": "2pt", "below": "2pt"}


# ---------------------------------------------------------------------------
# Preamble fragments
# ---------------------------------------------------------------------------

def geometry_options() -> str:
    """Return the option list for ``\\usepackage[...]{geometry}``."""
    opts = [PAGE["paper"], f"margin={PAGE['margin']}"]
    for key in ("headheight", "headsep", "footskip"):
        value = PAGE.get(key)
        if value:
            opts.append(f"{key}={value}")
    if PAGE.get("includeheadfoot"):
        opts.append("includeheadfoot")
    return ", ".join(opts)


def color_defs() -> str:
    """Return the ``\\definecolor`` block for the report palette."""
    defs = [
        f"\\definecolor{{osdagGreen}}{{HTML}}{{{OSDAG_GREEN}}}",
        f"\\definecolor{{tableHeader}}{{HTML}}{{{TABLE_HEADER_BG}}}",
        f"\\definecolor{{tableZebra}}{{HTML}}{{{TABLE_ZEBRA_BG}}}",
        f"\\definecolor{{tableRule}}{{HTML}}{{{RULE_COLOR}}}",
        f"\\definecolor{{urPass}}{{HTML}}{{{UR_PASS_COLOR}}}",
        f"\\definecolor{{urFail}}{{HTML}}{{{UR_FAIL_COLOR}}}",
    ]
    for role, name in _COLOR_NAMES.items():
        if name in ("urPass", "urFail"):
            continue  # already defined above
        defs.append(f"\\definecolor{{{name}}}{{HTML}}{{{TEXT_COLORS[role]}}}")
    return "\n".join(defs)


def color(role: str, text: str) -> str:
    """Wrap *text* in the semantic colour registered for *role*."""
    name = _COLOR_NAMES.get(role)
    if not name:
        raise KeyError(f"unknown colour role {role!r}")
    return r"\textcolor{" + name + "}{" + text + "}"


def fail_mark(text: str = "FAIL") -> str:
    """Colour a failing status word."""
    return color("fail", text)


def pass_mark(text: str = "PASS") -> str:
    """Colour a passing status word."""
    return color("pass", text)


def caption_setup() -> str:
    """Return the caption spacing block (tight captions, no orphan gap)."""
    return "\n".join([
        f"\\setlength{{\\abovecaptionskip}}{{{CAPTION['above']}}}",
        f"\\setlength{{\\belowcaptionskip}}{{{CAPTION['below']}}}",
    ])


def table_open(tabcolsep: Optional[str] = None,
               arraystretch: Optional[str] = None,
               font: Optional[str] = None,
               full_width: bool = False) -> str:
    """Open a locally-scoped table block with an optional spacing override.

    Returns the ``\\begingroup`` line plus any overrides; close the block with
    :func:`table_close`.  Keeping the ``\\setlength`` calls here is what makes
    this module the single source of truth for table spacing.
    """
    parts = [r"\begingroup"]
    if font:
        parts.append(font)
    if tabcolsep:
        parts.append(r"\setlength{\tabcolsep}{" + tabcolsep + "}")
    if arraystretch:
        parts.append(r"\renewcommand{\arraystretch}{" + arraystretch + "}")
    if full_width:
        parts.append(r"\setlength\LTleft{0pt}")
        parts.append(r"\setlength\LTright{\fill}")
    return "\n".join(parts)


def table_close() -> str:
    """Close a block opened with :func:`table_open`."""
    return r"\endgroup"



def column_types() -> str:
    """Return the project-wide ``\\newcolumntype`` declarations."""
    return "\n".join([
        r"\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}",
        r"\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}",
        r"\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}",
    ])


def table_setup() -> str:
    """Return the global table spacing/rule block for the preamble."""
    needspace = TABLE["needspace"]
    block = "\n".join([
        "% Table layout and spacing: consistent padding, row height, and "
        "longtable pre/post skips",
        f"\\setlength{{\\tabcolsep}}{{{TABLE['tabcolsep']}}}",
        f"\\renewcommand{{\\arraystretch}}{{{TABLE['arraystretch']}}}",
        f"\\setlength{{\\LTpre}}{{{TABLE['ltpre']}}}",
        f"\\setlength{{\\LTpost}}{{{TABLE['ltpost']}}}",
        "% Table rules (outline thickness) and small extra row height for clarity",
        f"\\setlength{{\\arrayrulewidth}}{{{TABLE['arrayrulewidth']}}}",
        f"\\setlength{{\\extrarowheight}}{{{TABLE['extrarowheight']}}}",
        "",
        "% Prevent tables from overflowing past the page bottom:",
        f"% if fewer than 5 baseline-skips remain, break to the next page first.",
        f"\\BeforeBeginEnvironment{{table}}{{\\needspace{{{needspace}}}}}",
        f"\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{needspace}}}}}",
    ])
    if RAGGED_BOTTOM:
        block += "\n\\raggedbottom"
    return block


# ---------------------------------------------------------------------------
# Fragment builders
# ---------------------------------------------------------------------------

def longtable(
    colspec: str,
    headers: Sequence[str],
    body: str,
    caption: Optional[str] = None,
    label: Optional[str] = None,
    cont_caption: Optional[str] = None,
    tabcolsep: Optional[str] = None,
    font: Optional[str] = None,
) -> str:
    """Build a ``longtable`` whose header row repeats on every page.

    Parameters
    ----------
    colspec:
        Column specification, e.g. ``|C{2.0cm}|L{4.0cm}|``.
    headers:
        Header cells, already LaTeX-escaped.
    body:
        Data rows joined by ``\\hline``; must **not** end with a trailing
        ``\\hline`` (the ``\\endlastfoot`` block supplies the closing rule).
    caption:
        Caption text; ``None`` for untitled tables.
    label:
        Optional ``\\label{...}`` key (without the braces).
    cont_caption:
        Text used on continuation pages. Defaults to ``caption (continued)``.
    tabcolsep:
        Per-table override of the global column separation.
    font:
        Optional font-size command applied to the whole table, e.g.
        ``r"\\small"``.

    The four ``\\end*`` markers are what fix the "header disappears after a
    page break" defect -- ``\\endfirsthead`` is page 1, ``\\endhead`` is every
    following page, ``\\endfoot`` every page but the last, ``\\endlastfoot``
    the final page.
    """
    colsep = tabcolsep or TABLE["tabcolsep"]
    header_row = " & ".join(headers) + r" \\"

    if caption:
        first_caption = (r"\caption{" + caption + "}"
                         + (r"\label{" + label + "}" if label else "")
                         + r"\\")
        cont_text = cont_caption or f"{caption} (continued)"
        # Empty optional argument => no duplicate entry in the TOC / List of Tables.
        head_caption = r"\caption[]{" + cont_text + r"}\\"
    else:
        first_caption = r"\label{" + label + r"}\\" if label else ""
        head_caption = ""

    parts = ["\\begingroup"]
    if font:
        parts.append(font)
    parts.append(r"\setlength{\tabcolsep}{" + colsep + "}")
    parts.append(r"\begin{longtable}{" + colspec + "}")
    if first_caption:
        parts.append(first_caption)
    parts.append(r"\hline")
    parts.append(header_row)
    parts.append(r"\hline")
    parts.append(r"\endfirsthead")
    if head_caption:
        parts.append(head_caption)
    parts.append(r"\hline")
    parts.append(header_row)
    parts.append(r"\hline")
    parts.append(r"\endhead")
    parts.append(r"\hline")
    parts.append(r"\endfoot")
    parts.append(r"\hline")
    parts.append(r"\endlastfoot")
    parts.append(body)
    parts.append(r"\end{longtable}")
    parts.append("\\endgroup")
    return "\n".join(parts)


def rows(row_values: Iterable[Sequence[str]]) -> str:
    """Join pre-formatted row cells with ``\\hline`` separators."""
    return "\n\\hline\n".join(" & ".join(row) + r" \\" for row in row_values)


def figure_block(path: str, caption: str,
                 width: str = r"\textwidth",
                 height: Optional[str] = None,
                 placement: str = "H") -> str:
    """Embed a figure saved at *path* (LaTeX-relative).

    Charts are placed inline (centred block, no ``figure`` float) so that a
    chart never gets queued behind a long table and leaves a blank page.
    ``placement`` is accepted for backwards compatibility and ignored.
    """
    opts = "width=" + width
    if height:
        opts += ",height=" + height + ",keepaspectratio"
    return "\n".join([
        r"\begin{center}",
        r"\includegraphics[" + opts + "]{" + path.replace("\\", "/") + "}",
        r"\\[2pt]{\small " + caption + "}",
        r"\end{center}",
    ])
