"""Reusable longtable construction and normalisation helpers."""

from __future__ import annotations

import re
from typing import Iterable, Sequence


def longtable(column_spec: str, caption: str, header: str, rows: Iterable[str]) -> str:
    """Build a safe, repeat-header ``longtable`` from already escaped cells.

    Chapter templates may still use handcrafted tables; ``normalise_longtables``
    below upgrades those during assembly as well.
    """
    body = "\n\\hline\n".join(rows)
    return (
        f"\\begin{{longtable}}{{{column_spec}}}\n"
        f"\\caption{{{caption}}}\\\\\n\\hline\n{header}\\\\\n\\hline\n"
        f"\\endfirsthead\n\\multicolumn{{99}}{{l}}{{\\small\\itshape Table \\thetable\\ continued}}\\\\\n"
        f"\\hline\n{header}\\\\\n\\hline\n\\endhead\n"
        "\\hline\\multicolumn{99}{r}{\\small\\itshape Continued on next page}\\\\\n\\endfoot\n"
        "\\hline\\endlastfoot\n"
        f"{body}\\\\\n\\hline\n\\end{{longtable}}"
    )


_LONGTABLE = re.compile(
    r"(\\begin\{longtable\}\{[^\n]+\}\s*"
    r"(?:\\caption\{.*?\}\\\\\s*)?\\hline\s*)"
    r"(?P<header>.*?\\\\(?:\[[^]]*\])?\s*\\hline)(?!\s*\\endfirsthead)",
    re.DOTALL,
)


def normalise_longtables(tex: str) -> str:
    """Add standard continuation blocks to legacy longtables.

    The operation only targets a table's first header row and leaves tables
    already authored with ``\\endfirsthead`` untouched.  It runs once on the
    assembled document so every chapter benefits without data rewrites.
    """
    def replacement(match: re.Match[str]) -> str:
        header = match.group("header")
        # Header has its trailing hline, which is also the first-head boundary.
        repeated = header.rsplit("\\hline", 1)[0]
        return (
            match.group(1) + header + "\n\\endfirsthead\n"
            "\\hline\n\\multicolumn{99}{l}{\\small\\itshape Table \\thetable\\ continued}\\\\\n"
            + repeated + "\\hline\n\\endhead\n"
            "\\hline\\multicolumn{99}{r}{\\small\\itshape Continued on next page}\\\\\n"
            "\\endfoot\n\\hline\\endlastfoot"
        )
    return _LONGTABLE.sub(replacement, tex)
