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


def _parse_width_pt(val_str: str, unit: str) -> float:
    v = float(val_str)
    unit = unit.lower()
    if unit == "cm":
        return v * 28.45275
    elif unit == "mm":
        return v * 2.845275
    elif unit == "in":
        return v * 72.27
    elif unit == "pt":
        return v
    return v * 28.45275


def _fit_col_spec(col_spec: str, ncols: int, theme: Theme) -> Tuple[str, bool]:
    """Check if table width exceeds text_width_pt and scale column widths if necessary.

    Returns (fitted_col_spec, is_dense).
    """
    page = theme.page
    tbl = theme.table
    text_width_pt = page.text_width_pt
    is_dense = ncols >= tbl.dense_min_cols
    tabcolsep_pt = tbl.dense_col_sep_pt if is_dense else 6.0
    arrayrulewidth_pt = 0.4
    overhead_pt = (2 * ncols * tabcolsep_pt) + ((ncols + 1) * arrayrulewidth_pt)
    avail_cols_pt = max(50.0, text_width_pt - overhead_pt - 25.0)

    # Find all explicit widths e.g. L{3.5cm}, C{2.0cm}, p{1.5cm}
    matches = list(re.finditer(r"([LCRpmb])\{([0-9.]+)\s*(cm|mm|in|pt)\}", col_spec))
    if matches and len(matches) == ncols:
        widths_pt = [_parse_width_pt(m.group(2), m.group(3)) for m in matches]
        total_cols_pt = sum(widths_pt)
        if total_cols_pt > avail_cols_pt:
            scale = avail_cols_pt / total_cols_pt
            new_spec = col_spec
            for m, w_pt in reversed(list(zip(matches, widths_pt))):
                scaled_w_cm = (w_pt * scale) / 28.45275
                replacement = f"{m.group(1)}{{{scaled_w_cm:.2f}cm}}"
                new_spec = new_spec[: m.start()] + replacement + new_spec[m.end() :]
            return new_spec, is_dense

    # Handle bare columns when ncols > tbl.max_bare_cols
    if ncols > tbl.max_bare_cols and not matches:
        w_each_cm = (avail_cols_pt / ncols) / 28.45275
        new_spec = "|" + "|".join([f"L{{{w_each_cm:.2f}cm}}"] * ncols) + "|"
        return new_spec, is_dense

    return col_spec, is_dense


class ReportTable:
    """Standard multipage longtable with repeated headers and pagination rules."""

    def __init__(
        self,
        columns: int | str | Sequence[str] | None = None,
        caption: str = "",
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

        self.col_spec, self._is_dense = _fit_col_spec(self.col_spec, self.ncols, self.theme)
        self._table = pylatex.LongTable(self.col_spec, width=self.ncols)
        self._row_count = 0

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
        self._row_count += 1
        if hline:
            self._table.add_hline()

    def add_span_row(self, text: str, ncols: int | None = None, align: str = "|l|") -> None:
        """Add a span row (e.g. section separator) across all columns."""
        n = ncols or self.ncols
        self._table.append(NoEscape(rf"\multicolumn{{{n}}}{{{align}}}{{\textbf{{{text}}}}} \\"))
        self._table.add_hline()
        self._row_count += 1

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
            self._row_count += max(1, clean.count(r"\\"))

    def dumps(self) -> str:
        """Render the complete LaTeX representation of the table."""
        t = self.theme
        tbl = t.table
        header_rows_count = len(self.header_list) if self.header_list else 1
        total_rows = getattr(self, "_row_count", 0)
        n_lines = (
            tbl.needspace_caption_lines
            + (tbl.needspace_lines_per_header_row * header_rows_count)
            + (min(total_rows, tbl.needspace_min_body_rows) if total_rows > 0 else tbl.needspace_min_body_rows)
            + tbl.needspace_foot_lines
        )
        prefix = f"\\par\\Needspace*{{{n_lines}\\baselineskip}}\n"
        if getattr(self, "_is_dense", False):
            prefix += f"{{\\setlength{{\\tabcolsep}}{{{tbl.dense_col_sep_pt:.1f}pt}}{t.typography.table_font_size_dense}\n"
            suffix = "\n}"
        else:
            suffix = ""
        return prefix + self._table.dumps() + suffix


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
            base_spec = "|" + "|".join(f"L{{{w}}}" for w in col_spec) + "|"
        else:
            base_spec = col_spec

        ncols = _count_cols(base_spec)
        self.col_spec, self.is_dense = _fit_col_spec(base_spec, ncols, self.theme)

        self.rows: list[list[Any]] = []
        if rows:
            for r in rows:
                self.add_row(r)

    def add_row(self, cells: Sequence[Any]) -> None:
        self.rows.append(list(cells))

    def dumps(self) -> str:
        tbl = self.theme.table
        t = self.theme
        lines = []
        if getattr(self, "is_dense", False):
            lines.append(f"{{\\setlength{{\\tabcolsep}}{{{tbl.dense_col_sep_pt:.1f}pt}}{t.typography.table_font_size_dense}")
        lines.extend([rf"\begin{{tabular}}{{{self.col_spec}}}", r"\hline"])
        for row in self.rows:
            formatted = " & ".join(str(c) for c in row) + r" \\"
            lines.append(formatted)
            lines.append(r"\hline")
        lines.append(r"\end{tabular}")
        if getattr(self, "is_dense", False):
            lines.append("}")
        return "\n".join(lines)


def row_end(pt: float | None = None) -> str:
    """Format standard table row terminator."""
    t = get_active_theme()
    p = pt if pt is not None else t.table.row_pad_pt
    return rf"\\[{p:.0f}pt]"


def row_end_nobreak(pt: float = 6.0) -> str:
    """Format non-breaking row terminator with padding."""
    return rf"\\*[{pt:.0f}pt]"


def row_pad(pt: float = 6.0) -> str:
    """Format row terminator with explicit padding."""
    return rf"\\[{pt:.0f}pt]"
