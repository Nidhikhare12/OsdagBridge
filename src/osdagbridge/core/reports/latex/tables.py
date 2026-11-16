"""Structured LaTeX table builders with repeated headers (Requirement R1).

All multipage tables are constructed via PyLaTeX LongTable with standard
\\endfirsthead, \\endhead, \\endfoot, \\endlastfoot directives,
ensuring repeated table headers across page breaks without footer overlap.
"""

from __future__ import annotations
import re
from typing import Sequence, Any, Tuple
import pylatex
from pylatex.utils import NoEscape

from osdagbridge.core.reports.theme import Theme, get_active_theme


def _count_cols(col_spec: str) -> int:
    """Parse a LaTeX column specification to count the number of columns."""
    clean = re.sub(r">\{[^}]*\}|<\{[^}]*\}", "", col_spec)
    matches = re.findall(r"[LCRpmblcr](?:\{[^}]+\})?", clean)
    if matches:
        return len(matches)
    pipes = col_spec.count("|")
    return max(1, pipes - 1 if pipes > 1 else pipes)


class ReportTable:
    """Standard multipage longtable with repeated headers and pagination rules."""

    def __init__(
        self,
        columns: int | str | Sequence[str],
        caption: str,
        label: str | None = None,
        header_rows: Sequence[Sequence[Any]] | Sequence[Any] | None = None,
        header_tex: str | None = None,
        preset: Sequence[str] | None = None,
        theme: Theme | None = None,
    ):
        self.theme = theme or get_active_theme()
        self.caption = caption
        self.label = label
        self.header_tex = header_tex

        # Resolve column specification and width
        if preset is not None:
            self.ncols = len(preset)
            self.col_spec = "|" + "|".join(f"L{{{w}}}" for w in preset) + "|"
        elif isinstance(columns, int):
            self.ncols = columns
            if columns == 2:
                p = self.theme.columns.KEY_VALUE
                self.col_spec = f"|L{{{p[0]}}}|L{{{p[1]}}}|"
            else:
                self.col_spec = "|" + "|".join(["l"] * columns) + "|"
        elif isinstance(columns, str):
            self.col_spec = columns
            self.ncols = _count_cols(columns)
        elif isinstance(columns, (list, tuple)):
            self.ncols = len(columns)
            self.col_spec = "|" + "|".join(f"L{{{w}}}" for w in columns) + "|"
        else:
            raise TypeError(f"Invalid columns argument: {type(columns)}")

        self._table = pylatex.LongTable(self.col_spec, width=self.ncols)

        # Normalize header rows
        if header_rows is not None and len(header_rows) > 0:
            if isinstance(header_rows[0], (str, NoEscape)) or not isinstance(header_rows[0], (list, tuple)):
                self.header_list = [header_rows]
            else:
                self.header_list = list(header_rows)
        else:
            self.header_list = []

        self._build_header_structure()

    def _build_header_structure(self) -> None:
        r"""Construct caption and repeated header blocks (\endfirsthead / \endhead)."""
        t = self.theme
        tbl = t.table

        # 1. First-page caption and label
        label_cmd = f"\\label{{{self.label}}}" if self.label else ""
        if self.caption:
            self._table.append(NoEscape(rf"\caption{{{self.caption}}}{label_cmd}\\"))

        def _render_headers():
            if self.header_tex:
                self._table.append(NoEscape(self.header_tex))
            else:
                self._table.add_hline()
                for hrow in self.header_list:
                    if isinstance(hrow, str):
                        self._table.append(NoEscape(hrow))
                    else:
                        formatted_cells = [
                            NoEscape(rf"\textbf{{{c}}}") if (tbl.header_bold and "\\textbf" not in str(c)) else NoEscape(str(c))
                            for c in hrow
                        ]
                        self._table.add_row(formatted_cells)
                        self._table.add_hline()

        # 2. First-page header row(s)
        _render_headers()

        # 3. End first head
        self._table.append(NoEscape(r"\endfirsthead"))

        # 4. Continuation head (shown at top of subsequent pages)
        if self.caption:
            cont_caption = f"{self.caption} {tbl.continued_label}"
            self._table.append(NoEscape(rf"\caption[]{{{cont_caption}}}\\"))

        _render_headers()

        # 5. End regular head
        self._table.append(NoEscape(r"\endhead"))

        # 6. Regular foot (shown at bottom of pages continuing onto next page)
        self._table.append(
            NoEscape(
                rf"\hline\multicolumn{{{self.ncols}}}{{r}}{{\footnotesize\itshape {tbl.continues_label}}}\\"
            )
        )
        self._table.append(NoEscape(r"\endfoot"))

        # 7. Last foot (shown on final page of table)
        self._table.add_hline()
        self._table.append(NoEscape(r"\endlastfoot"))

    def add_row(self, cells: Sequence[Any], pad: bool = True, hline: bool = True) -> None:
        """Add a table body row with validation and optional hline."""
        if len(cells) != self.ncols:
            raise ValueError(f"Row has {len(cells)} cells, expected {self.ncols}")

        escaped_cells = [NoEscape(str(c)) for c in cells]
        self._table.add_row(escaped_cells)
        if hline:
            self._table.add_hline()

    def add_span_row(self, text: str, ncols: int | None = None, align: str = "|l|") -> None:
        """Add a span row (e.g. section separator) across all columns."""
        n = ncols or self.ncols
        self._table.append(NoEscape(rf"\multicolumn{{{n}}}{{{align}}}{{\textbf{{{text}}}}} \\"))
        self._table.add_hline()

    def add_group_row(self, label: str) -> None:
        """Add a member/girder group row and keep with next rows."""
        self.add_span_row(label)
        self._table.append(NoEscape(r"\nopagebreak"))

    def keep_group(self, rows: Sequence[Sequence[Any]]) -> None:
        """Emit a sequence of rows kept together via \\nopagebreak."""
        for i, row in enumerate(rows):
            self.add_row(row)
            if i < len(rows) - 1:
                self._table.append(NoEscape(r"\nopagebreak"))

    def add_hline(self) -> None:
        """Explicitly add a horizontal line."""
        self._table.add_hline()

    def add_raw_rows(self, raw_rows_tex: str) -> None:
        """Append pre-formatted LaTeX row strings (e.g. multirow blocks) directly to table body."""
        clean = raw_rows_tex.strip()
        if clean:
            self._table.append(NoEscape(clean))

    def dumps(self) -> str:
        """Render the complete LaTeX representation of the table."""
        return self._table.dumps()


class KeyValueTable:
    """Specialized two-column key-value parameter table builder."""

    def __init__(
        self,
        caption: str,
        rows: Sequence[Tuple[Any, Any]] | None = None,
        headers: Tuple[str, str] = ("Parameter", "Value"),
        preset: Sequence[str] | None = None,
        label: str | None = None,
        theme: Theme | None = None,
    ):
        t = theme or get_active_theme()
        col_preset = preset or t.columns.KEY_VALUE
        self._table = ReportTable(
            columns=2,
            caption=caption,
            label=label,
            header_rows=[headers] if headers else None,
            preset=col_preset,
            theme=t,
        )
        if rows:
            for k, v in rows:
                self.add_row(k, v)

    def add_row(self, key: Any, value: Any, pad: bool = True, hline: bool = True) -> None:
        self._table.add_row([key, value], pad=pad, hline=hline)

    def dumps(self) -> str:
        return self._table.dumps()


class SimpleTable:
    """Non-breaking tabular environment builder for short metadata/title sections."""

    def __init__(
        self,
        col_spec: str | Sequence[str],
        rows: Sequence[Sequence[Any]] | None = None,
        theme: Theme | None = None,
    ):
        self.theme = theme or get_active_theme()
        if isinstance(col_spec, (list, tuple)):
            self.col_spec = "|" + "|".join(f"L{{{w}}}" for w in col_spec) + "|"
        else:
            self.col_spec = col_spec

        self.rows: list[list[Any]] = []
        if rows:
            for r in rows:
                self.add_row(r)

    def add_row(self, cells: Sequence[Any]) -> None:
        self.rows.append(list(cells))

    def dumps(self) -> str:
        lines = [rf"\begin{{tabular}}{{{self.col_spec}}}", r"\hline"]
        for row in self.rows:
            formatted = " & ".join(str(c) for c in row) + r" \\"
            lines.append(formatted)
            lines.append(r"\hline")
        lines.append(r"\end{tabular}")
        return "\n".join(lines)
