"""Make every generated ``longtable`` well-formed and header-repeating.

The chapter generators write tables as::

    \\begin{longtable}{spec}
    \\caption{...}
    \\hline
    header row \\\\
    \\hline
    body rows ...

Two problems follow from that pattern:

* ``longtable`` needs ``\\\\`` after a ``\\caption``; without it LaTeX raises
  "Misplaced \\noalign" and drops the rule under the caption.
* The header row is not repeated when the table breaks across pages.

``normalize_longtables`` fixes both for the whole document in one pass. The
caption stays in ``\\endfirsthead`` only, so captions and column headings
are never reordered. Tables that already define ``\\endhead`` or
``\\endfirsthead`` are left untouched, and the function is idempotent.
"""

from __future__ import annotations

import logging
import re

from osdagbridge.core.reports import styles

logger = logging.getLogger(__name__)

_BEGIN = r"\begin{longtable}"
_END = r"\end{longtable}"
_HLINE = r"\hline"
_CAPTION = re.compile(r"(\s*)(\\caption\*?)(\[[^\]]*\])?\{")
_LABEL = re.compile(r"\s*\\label\{[^}]*\}")
_ROW_END = re.compile(r"\s*\\\\")
_LEADING_HLINE = re.compile(r"\s*\\hline")
_HEADER_MARKERS = (r"\textbf", r"\multicolumn")


def _group_end(text: str, start: int) -> int:
    """Return the index just after the brace group opening at ``start``.

    Args:
        text: Text containing the group.
        start: Index of the opening ``{``.

    Returns:
        Index of the character following the matching ``}``.

    Raises:
        ValueError: If the braces are unbalanced.
    """
    depth = 0
    i = start
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("Unbalanced braces in LaTeX group")


def _column_count(spec: str) -> int:
    """Count the columns declared by a ``longtable`` column specification.

    Args:
        spec: The text between the outer braces, e.g. ``|L{5cm}|C{2cm}|``.

    Returns:
        Number of data columns.
    """
    count = 0
    i = 0
    while i < len(spec):
        char = spec[i]
        i += 1
        if char in "lcr":
            count += 1
        elif char in "pmbLCRX":
            count += 1
            if i < len(spec) and spec[i] == "{":
                i = _group_end(spec, i)
        elif char in ">@<!" and i < len(spec) and spec[i] == "{":
            i = _group_end(spec, i)
    return count


def _terminate_caption(rest: str) -> tuple[str, str, bool]:
    """Split a leading caption off ``rest`` and make sure it ends in ``\\\\``.

    Args:
        rest: Table text following the column specification.

    Returns:
        ``(caption_part, remainder, has_caption)``.
    """
    match = _CAPTION.match(rest)
    if match is None:
        return "", rest, False
    end = _group_end(rest, match.end() - 1)
    caption, tail = rest[:end], rest[end:]
    label = _LABEL.match(tail)
    if label:
        caption += tail[: label.end()]
        tail = tail[label.end():]
    if not _ROW_END.match(tail):
        caption += r"\\"
    return caption, tail, True


def _fix_table(table: str) -> str:
    """Normalize one table, given from ``\\begin{longtable}`` to its body end.

    Args:
        table: Table text excluding the closing ``\\end{longtable}``.

    Returns:
        The corrected table text.
    """
    if r"\endhead" in table or r"\endfirsthead" in table:
        return table
    i = len(_BEGIN)
    if table[i:i + 1] == "[":
        i = table.index("]", i) + 1
    spec_start = table.index("{", i)
    spec_end = _group_end(table, spec_start)
    columns = _column_count(table[spec_start + 1: spec_end - 1])

    caption, tail, has_caption = _terminate_caption(table[spec_end:])
    prefix = table[:spec_end] + caption

    opening = _LEADING_HLINE.match(tail)
    if opening is None:
        return prefix + tail
    block_start = opening.end()
    block_end = tail.find(_HLINE, block_start)
    if block_end == -1:
        return prefix + tail
    block = tail[block_start:block_end]
    if r"\\" not in block or not any(m in block for m in _HEADER_MARKERS):
        return prefix + tail

    continued = ""
    if has_caption:
        continued = (
            r"\multicolumn{" + str(columns) + r"}{l}{\small\textit{"
            r"\tablename~\thetable{} (continued)}} \\[\rowgaplabel]" + "\n"
        )
    repeat = (
        "\n" + r"\endfirsthead" + "\n" + continued + _HLINE + block
        + _HLINE + "\n" + r"\endhead"
    )
    after = block_end + len(_HLINE)
    return prefix + tail[:after] + repeat + tail[after:]


_GUARDED = re.compile(r"\\needspace\{[^}]*\}\s*$")


def _guard_if_headerless(table: str, preceding: str) -> str:
    """Keep a table without a repeating header from starting at a page foot.

    Tables with a repeating header keep it with the first row, so they need
    no guard. A guard in front of them is harmful: combined with
    ``\\endhead`` it produced a duplicated header when the table was pushed
    to the next page. Other tables get ``\\needspace`` instead.

    Args:
        table: Table text, from ``\\begin{longtable}`` to its body end.
        preceding: Text before the table, used to avoid a second guard.

    Returns:
        ``table``, prefixed by a ``\\needspace`` request when needed.
    """
    if r"\endfirsthead" in table or r"\endhead" in table:
        return table
    if _GUARDED.search(preceding):
        return table
    lines = styles.TABLE.needspace_lines
    return rf"\needspace{{{lines}\baselineskip}}" + "\n" + table


def normalize_longtables(latex: str) -> str:
    """Terminate captions and repeat header rows in every ``longtable``.

    Args:
        latex: A complete LaTeX document or fragment.

    Returns:
        The corrected LaTeX. Text outside ``longtable`` environments is
        returned unchanged.
    """
    parts: list[str] = []
    pos = 0
    while True:
        begin = latex.find(_BEGIN, pos)
        if begin == -1:
            break
        end = latex.find(_END, begin)
        if end == -1:
            break
        parts.append(latex[pos:begin])
        table = latex[begin:end]
        try:
            table = _fix_table(table)
        except ValueError:
            logger.warning("Skipping malformed longtable near offset %d",
                           begin)
        parts.append(_guard_if_headerless(table, latex[pos:begin]))
        pos = end
    parts.append(latex[pos:])
    return "".join(parts)
