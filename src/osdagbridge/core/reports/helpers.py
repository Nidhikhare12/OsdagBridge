# =============================================================================
# OsdagBridge — Report Formatting Helpers (Phase 2B)
# =============================================================================
"""
Reusable LaTeX table and layout helper functions.

Defines `make_longtable` which provides repeated column headers across
multi-page tables via \\endfirsthead and \\endhead.
"""

from typing import List, Optional, Union


def make_longtable(
    col_spec: str,
    caption: str,
    headers: Union[List[str], str],
    rows: Union[List[str], str],
    label: Optional[str] = None,
    continuation_note: str = "Continued on next page",
    note: Optional[str] = None,
    tabcolsep: Optional[str] = None,
    fontsize: Optional[str] = None,
) -> str:
    """
    Construct a professional, multi-page LaTeX longtable with repeated headers.

    Structure generated:
      - \\begin{longtable}{col_spec}
      - \\caption{\\textbf{caption}} \\label{label} \\\\
      - \\hline
      - First-head header row(s)
      - \\hline
      - \\endfirsthead
      - Subsequent page header (Table continuation header)
      - \\hline
      - Subsequent page header row(s)
      - \\hline
      - \\endhead
      - Subsequent page footer (\\endfoot) with continuation note
      - Final page footer (\\endlastfoot)
      - Body rows
      - \\end{longtable}

    Parameters
    ----------
    col_spec : str
        LaTeX column specification, e.g. "|L{3.5cm}|L{8.5cm}|".
    caption : str
        The table caption string.
    headers : Union[List[str], str]
        Either a list of header cell strings, e.g. ["Girder", "Property", "Value"],
        or an already-formatted LaTeX row string.
    rows : Union[List[str], str]
        Body rows as a list of LaTeX row strings or a single pre-joined string.
    label : Optional[str]
        Optional LaTeX label for cross-referencing (e.g. "tab:girder-props").
    continuation_note : str
        Text shown in bottom right on pages before the last.
    note : Optional[str]
        Optional footer text or note below table.
    tabcolsep : Optional[str]
        Optional local tabcolsep, e.g. "3pt" or "4pt".
    fontsize : Optional[str]
        Optional local font size command, e.g. r"\\small" or r"\\footnotesize".

    Returns
    -------
    str
        Raw LaTeX string ready for embedding into report documents.
    """
    # Count columns from col_spec to determine \multicolumn width
    spec_clean = col_spec.strip()
    ncols = 0
    in_bracket = False
    for ch in spec_clean:
        if ch == '{':
            in_bracket = True
        elif ch == '}':
            in_bracket = False
        elif not in_bracket and ch in "LCRpmblcrX":
            ncols += 1
    if ncols == 0:
        ncols = 1

    # Format header row
    if isinstance(headers, (list, tuple)):
        header_tex = " & ".join(
            h if h.strip().startswith(("\\textbf", "\\makecell", "\\multicolumn"))
            else f"\\textbf{{{h}}}"
            for h in headers
        ) + r" \\[6pt]"
    else:
        header_tex = headers.strip()
        if not header_tex.endswith(r"\\") and not header_tex.endswith("}"):
            header_tex += r" \\[6pt]"

    # Format body rows
    if isinstance(rows, (list, tuple)):
        body_tex = "\n".join(rows)
    else:
        body_tex = rows.strip()

    lbl_tex = f"\\label{{{label}}}" if label else ""
    caption_line = f"\\caption{{\\textbf{{{caption}}}}} {lbl_tex} \\\\" if caption else ""
    cont_head = r"\multicolumn{" + str(ncols) + r"}{c}{\textbf{\tablename\ \thetable{} -- continued from previous page}} \\[6pt]"
    cont_foot = r"\multicolumn{" + str(ncols) + r"}{r}{\textit{" + continuation_note + r"}} \\"

    prefix = []
    suffix = []
    if tabcolsep or fontsize:
        prefix.append(r"\begingroup")
        if tabcolsep:
            prefix.append(r"\setlength{\tabcolsep}{" + tabcolsep + r"}")
        if fontsize:
            prefix.append(fontsize)
        suffix.append(r"\endgroup")

    parts = list(prefix)
    parts.append(r"\begin{longtable}{" + col_spec + r"}")
    if caption_line:
        parts.append(caption_line)
    parts.extend([
        r"\hline",
        header_tex,
        r"\hline",
        r"\endfirsthead",
        "",
        cont_head,
        r"\hline",
        header_tex,
        r"\hline",
        r"\endhead",
        "",
        r"\hline",
        cont_foot,
        r"\endfoot",
        "",
        r"\hline",
        r"\endlastfoot",
        "",
        body_tex,
        r"\end{longtable}"
    ])
    parts.extend(suffix)

    if note:
        parts.append(r"\vspace{-4pt}" + "\n" + r"\noindent\textit{" + note + r"}" + "\n")

    return "\n".join(parts) + "\n"
