"""Table helpers for OsdagBridge reports.

add_repeating_headers() post-processes the final LaTeX string and makes every
longtable repeat its header row on continuation pages.

Expected longtable shape (what the chapter files already produce):

    \\begin{longtable}{|l|l|}
    \\caption{...}\\label{...}\\\\
    \\hline
    \\textbf{A} & \\textbf{B} \\\\
    \\hline
    body rows...
    \\end{longtable}

After processing, the header block is followed by:

    \\endfirsthead
    \\hline
    \\textbf{A} & \\textbf{B} \\\\
    \\hline
    \\endhead

Tables are left untouched when they:
  - already contain \\endhead (e.g. Table 2.8 and Table 4.1),
  - have no plain header row (\\hline, row, \\hline) right after the caption,
  - have a header row that uses \\multicolumn (multi-row/merged headers).
"""

import re

_LONGTABLE_RE = re.compile(
    r"\\begin\{longtable\}.*?\\end\{longtable\}", re.DOTALL
)


def _is_hline(line):
    return line.strip().startswith(r"\hline")


def _process_longtable(block):
    """Return the longtable block with a repeating header added, or unchanged."""
    if r"\endhead" in block or r"\endfirsthead" in block:
        return block

    lines = block.split("\n")

    # First \hline after \begin{longtable}: top rule of the header.
    top = next((i for i, ln in enumerate(lines) if i > 0 and _is_hline(ln)), None)
    if top is None:
        return block

    # Header row: next non-empty line after that rule.
    row = top + 1
    while row < len(lines) and not lines[row].strip():
        row += 1
    if row >= len(lines):
        return block

    header = lines[row]
    if not header.rstrip().endswith(r"\\"):
        return block
    if _is_hline(header) or r"\multicolumn" in header:
        return block

    # Closing rule of the header.
    bottom = row + 1
    while bottom < len(lines) and not lines[bottom].strip():
        bottom += 1
    if bottom >= len(lines) or not _is_hline(lines[bottom]):
        return block

    repeated = [
        r"\endfirsthead",
        lines[top],
        header,
        lines[bottom],
        r"\endhead",
    ]
    new_lines = lines[: bottom + 1] + repeated + lines[bottom + 1:]
    return "\n".join(new_lines)


def add_repeating_headers(tex):
    """Add repeating header rows to every eligible longtable in `tex`."""
    return _LONGTABLE_RE.sub(lambda m: _process_longtable(m.group(0)), tex)
