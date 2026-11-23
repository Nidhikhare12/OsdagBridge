# =============================================================================
# OsdagBridge — LaTeX table / figure builders
# =============================================================================
#
# Thin, PyLaTeX-style helpers (LongTable / Figure equivalents) that emit the
# LaTeX the report needs.  They contain NO formatting constants of their own —
# colours, padding, column layouts, widths and captions all come from
# ``styles.py``.
#
#   longtable()   multi-page table: caption + column header on the FIRST page,
#                 caption "(continued)" + the SAME column header on every
#                 following page (\endfirsthead / \endhead), closing rule at
#                 each page bottom (\endfoot).  Rows that belong together
#                 (e.g. all rows of one girder) are glued with \\* so a page
#                 break can never split them — this is what used to push the
#                 girder label ("G4") into the footer.
#   figure()      [H] figure with caption, or a styled placeholder box.
#   status/UR     PASS / FAIL and utilisation-ratio cell helpers.
# =============================================================================

from __future__ import annotations

import re
from typing import Iterable, List, Optional, Sequence, Union

from osdagbridge.core.reports import styles as S

# ---------------------------------------------------------------------------
# Column layouts
# ---------------------------------------------------------------------------

_ALIGN = {"L": "L", "C": "C", "R": "R"}


def column_spec(layout: Union[str, Sequence]) -> str:
    """LaTeX column spec for a named layout (styles.TABLE_LAYOUTS) or an
    explicit list of (alignment, fraction) pairs.

    Each column is as wide as ``fraction * \\textwidth`` including its padding
    and rule, so the table is exactly text-width and can never overflow.
    """
    cols = S.TABLE_LAYOUTS[layout] if isinstance(layout, str) else list(layout)
    parts = []
    for align, frac in cols:
        width = (r"\dimexpr %.4f\textwidth-2\tabcolsep-\arrayrulewidth\relax" % frac)
        parts.append("%s{%s}" % (_ALIGN[align], width))
    return "|" + "|".join(parts) + "|"


def n_columns(layout: Union[str, Sequence]) -> int:
    return len(S.TABLE_LAYOUTS[layout] if isinstance(layout, str) else layout)


# ---------------------------------------------------------------------------
# Row post-processing
# ---------------------------------------------------------------------------

# "\\[6pt]" row-skips were used all over the old code to fake cell padding;
# padding is now global (styles.TABLE['arraystretch']) so they are dropped.
_ROW_SKIP = re.compile(r"\\\\(\*?)\[\s*[0-9.]+\s*(?:pt|em|cm|mm)\s*\]")
# a row that is followed by \cline belongs to the SAME multirow group
_GROUP_BREAK = re.compile(r"\\\\\*?\s*\\cline")
# sub-heading rows (\multicolumn{n}{|l|}{\textbf{...}} \\) stay with next row
_SUBHEAD = re.compile(r"^(\\multicolumn\{\d+\}\{[^}]*\}\{.*\})[ \t]*\\\\[ \t]*$", re.M)


_MULTIROW = re.compile(r"^\\multirow\{\d+\}\{\*\}\{\\makecell\{(?P<lbl>.*?)\}\}\s*&(?P<rest>.*)$")
_INLINE_CLINE = re.compile(r"(\\\\)\s*\\cline\{[0-9\-]+\}")
_MULTI_HLINE = re.compile(r"(\\hline\s*){2,}")


def _flatten_groups(body: str) -> str:
    r"""Replace ``\multirow`` group labels by a label repeated on every row of
    the group (+ zebra shading per group).

    A \multirow cell that straddles a page break is typeset at the vertical
    centre of rows that now live on the NEXT page, so the label (e.g. "G4")
    ended up below the table, inside the footer.  Repeating the label in each
    row makes every row self-contained: a page break can fall anywhere.
    """
    out, label, gidx = [], None, 0
    body = _INLINE_CLINE.sub(lambda m: m.group(1) + "\n\\cline{0}", body)
    for line in body.split("\n"):
        st = line.strip()
        m = _MULTIROW.match(st)
        if m:
            gidx += 1
            label = m.group("lbl").replace("\\\\", " ").strip()
            line = label + " &" + m.group("rest")
            if gidx % 2 == 0:
                line = "\\grpfill " + line
        elif label is not None and line.startswith(" &"):
            line = label + line
            if gidx % 2 == 0:
                line = "\\grpfill " + line
        elif st.startswith("\\cline"):
            line = "\\hline"
        elif st == "\\hline":
            label = None
        out.append(line)
    return "\n".join(out)


def prepare_body(body: str, keep_groups: bool = True) -> str:
    """Normalise table-body TeX: drop ad-hoc row skips, flatten multirow
    groups (see _flatten_groups), keep sub-heading rows with the row below."""
    body = _ROW_SKIP.sub(lambda m: "\\\\" + m.group(1), body)
    if keep_groups:
        body = _flatten_groups(body)
        body = _SUBHEAD.sub(lambda m: m.group(1) + " \\\\*", body)
    body = _MULTI_HLINE.sub(lambda m: "\\hline\n", body)
    body = body.strip("\n")
    if not body.rstrip().endswith("\\hline"):
        body += "\n\\hline"
    return body


def _hdr_cell(c: str) -> str:
    c = c.strip()
    if not c:
        return r"\hcell{}"
    if c.startswith((r"\textbf", r"\hcell", r"\multicolumn", r"\multirow", r"\makecell")):
        return c
    return r"\hcell{" + c + "}"


def _header_row(headers: Union[None, str, Sequence[str]]) -> str:
    """One or many header rows -> TeX (each row terminated by \\\\ ; shaded)."""
    if not headers:
        return ""
    if isinstance(headers, str):               # raw (possibly multi-row) TeX
        raw = headers.strip()
        if not raw.endswith("\\hline"):
            raw += "\n\\hline"
        return r"\hdrfill " + raw
    return r"\hdrfill " + " & ".join(_hdr_cell(h) for h in headers) + " \\\\\n\\hline"


# ---------------------------------------------------------------------------
# Public table builder
# ---------------------------------------------------------------------------

def longtable(layout: Union[str, Sequence], caption: Optional[str],
              headers: Union[None, str, Sequence[str]] = None, body: str = "",
              *, label: Optional[str] = None, keep_groups: bool = True,
              small: bool = True, bold_caption: bool = False) -> str:
    """Build a LaTeX ``longtable`` with repeating headers.

    Parameters
    ----------
    layout   name in ``styles.TABLE_LAYOUTS`` (or explicit column list)
    caption  table caption (already LaTeX-escaped); ``None`` = no caption/number
    headers  list of header cell strings, OR raw multi-row header TeX
    body     body rows (``a & b \\\\`` lines + ``\\hline``)
    """
    spec = column_spec(layout)
    ncol = n_columns(layout)
    head = _header_row(headers)
    body = prepare_body(body, keep_groups)
    cont = S.TABLE["continued_suffix"]

    if caption:
        first_cap = r"\caption{" + caption + "}" + (r"\label{" + label + "}" if label else "") + "\\\\"
        cont_cap = (r"\caption*{\textcolor{osdagGreenDark}{Table~\thetable:}~" + caption + cont + "}\\\\")
    else:
        first_cap = cont_cap = ""

    first_head = "\n".join(x for x in (first_cap, r"\hline", head) if x)
    cont_head = "\n".join(x for x in (cont_cap, r"\hline", head) if x)

    # No page-bottom footer: every body row already ends with \hline, and an
    # explicit footer produced a stray "continued" line when a table started
    # at the very bottom of a page.
    foot = "\\endfoot\n\\endlastfoot"

    out = (
        (r"\begingroup" + S.TABLE["table_font"] + "\n" if small else r"\begingroup" + "\n")
        + r"\begin{longtable}{" + spec + "}\n"
        + first_head + "\n\\endfirsthead\n"
        + cont_head + "\n\\endhead\n"
        + foot + "\n"
        + body + "\n"
        + r"\end{longtable}" + "\n"
        + r"\endgroup" + "\n"
    )
    return out


def param_table(caption: str, rows, *, label: Optional[str] = None,
                layout: str = "param_value", headers=("parameter", "value")) -> str:
    """Two-column parameter / value table.  rows = [(parameter, value_tex)]"""
    body = "\n".join(r"\textnormal{" + p + r"} & " + v + r" \\" + "\n\\hline" for p, v in rows)
    return longtable(layout, caption, list(headers), body, label=label)


def note(text: str) -> str:
    """Italic table note placed directly under a table."""
    return (r"\par\vspace{-4pt}\noindent{" + S.FONT["note_size"] + r"\color{noteGrey}\textit{"
            + text + r"}}\par\vspace{6pt}" + "\n")


def table_note(text: str) -> str:   # alias — reads better in chapter files
    return note(text)


# ---------------------------------------------------------------------------
# Status / utilisation-ratio cells
# ---------------------------------------------------------------------------

PASS_TEX = r"\passtxt{}"
FAIL_TEX = r"\failtxt{}"
NA_TEX = S.STATUS["na_text"]


def status_cell(ok: Optional[bool]) -> str:
    """True -> PASS, False -> FAIL, None -> '---'."""
    if ok is None:
        return NA_TEX
    return PASS_TEX if ok else FAIL_TEX


def ur_cell(value, nd: int = 2) -> str:
    """Utilisation ratio, red + bold when above the limit."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return NA_TEX
    s = f"{f:.{nd}f}"
    return (r"\textcolor{failRed}{\textbf{" + s + "}}") if f > S.STATUS["ur_limit"] else s


def status_from_ur(value) -> str:
    try:
        return status_cell(float(value) <= S.STATUS["ur_limit"])
    except (TypeError, ValueError):
        return NA_TEX


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _placeholder_box(text: str, width: str) -> str:
    return (r"\fcolorbox{ruleGrey}{placeholderFill}{\parbox[c][3.2cm][c]{" + width + r"}{\centering\textit{["
            + S.FIGURE["placeholder_text"] + ": " + text + r" ]}}}")


def figure(path: Optional[str], caption: str, *, width: Optional[str] = None,
           label: Optional[str] = None, height: Optional[str] = None,
           placeholder: bool = True, numbered: bool = True) -> str:
    """Floating figure (``[H]``) with caption; placeholder box if no image."""
    width = width or S.FIGURE["default_width"]
    cap_cmd = r"\caption" if numbered else r"\caption*"
    lab = (r"\label{" + label + "}") if label else ""
    if path:
        opts = "width=" + width
        if height:
            opts += ",height=" + height + ",keepaspectratio"
        body = r"\includegraphics[" + opts + "]{" + path.replace("\\", "/") + "}"
    elif placeholder:
        body = _placeholder_box(caption, r"0.9\linewidth")
    else:
        return ""
    return (r"\begin{figure}[" + S.FIGURE["placement"] + "]\n"
            r"\centering" + "\n" + body + "\n"
            + cap_cmd + "{" + caption + "}" + lab + "\n"
            r"\end{figure}" + "\n")


def figure_row(items: Iterable[tuple], *, cols: int = 3) -> str:
    """Side-by-side figures: items = (path, caption, label)."""
    items = list(items)
    w = "%.3f" % (0.98 / cols - 0.01)
    cells = []
    for path, cap, lab in items:
        if path:
            img = r"\includegraphics[width=\linewidth]{" + path.replace("\\", "/") + "}"
        else:
            img = _placeholder_box(cap, r"0.95\linewidth")
        cells.append(
            r"\begin{minipage}[t]{" + w + r"\textwidth}\centering" + "\n" + img + "\n"
            r"\captionof{figure}{" + cap + "}" + (r"\label{" + lab + "}" if lab else "") + "\n"
            r"\end{minipage}")
    return "\\noindent\n" + "\n\\hfill\n".join(cells) + "\n"
