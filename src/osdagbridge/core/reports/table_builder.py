"""Reusable LongTable and TableBuilder infrastructure for LaTeX reports.

Provides standardized generation of multi-page LaTeX longtables conforming to
engineering reporting best practices:
- Complete caption syntax terminating with '\\'
- Initial header row followed by '\\endfirsthead'
- Continuation header repeated on subsequent pages followed by '\\endhead'
- Continuation footer indicating page continuation followed by '\\endfoot'
- Final footer rule followed by '\\endlastfoot'
- Automatic column count resolution and note styling
"""

import re
from typing import List, Optional, Union


def infer_num_columns(col_spec: str) -> int:
    """Infer the number of data columns from a LaTeX column specification string.

    Example:
        '|C{2.5cm}|L{6.5cm}|p{6.5cm}|' -> 3
        '|c|c|c|c|c|' -> 5
    """
    cleaned = re.sub(r'\{[^}]*\}', '', col_spec)
    cleaned = re.sub(r'>[^>]*<', '', cleaned)
    tokens = re.findall(r'[clrpLCRXm]', cleaned)
    return len(tokens) if tokens else 1


class TableBuilder:
    """Fluent builder for creating well-structured LaTeX longtables."""

    def __init__(
        self,
        col_spec: str,
        caption: str,
        label: Optional[str] = None,
        num_cols: Optional[int] = None,
    ):
        self.col_spec = col_spec.strip()
        self.caption = caption.strip()
        self.label = label.strip() if label else None
        self._inferred_cols = num_cols or infer_num_columns(self.col_spec)
        self.headers: List[str] = []
        self.raw_header_str: Optional[str] = None
        self.rows: List[str] = []
        self.note_text: Optional[str] = None
        self.continuation_label: Optional[str] = None

    def set_headers(self, headers: Union[List[str], str], row_height: str = "[6pt]") -> "TableBuilder":
        """Set the table column headers."""
        if isinstance(headers, list):
            self.headers = headers
            self._inferred_cols = len(headers)
            formatted = " & ".join(
                f"\\textbf{{{h}}}" if not h.strip().startswith(r"\textbf") else h
                for h in headers
            )
            self.raw_header_str = f"{formatted} \\\\{row_height}"
        else:
            self.raw_header_str = headers.strip()
            if not self.raw_header_str.endswith(r"\\") and not re.search(r'\\\\(\[[^\]]*\])?$', self.raw_header_str):
                self.raw_header_str += f" \\\\{row_height}"
        return self

    def add_row(self, *cells: str, row_height: str = "[6pt]", hline: bool = True) -> "TableBuilder":
        """Append a single row of cells."""
        row_str = " & ".join(str(c) for c in cells) + f" \\\\{row_height}"
        if hline:
            row_str += "\n\\hline"
        self.rows.append(row_str)
        return self

    def add_raw_content(self, raw_content: str) -> "TableBuilder":
        """Append pre-formatted LaTeX table rows."""
        if raw_content and raw_content.strip():
            self.rows.append(raw_content.strip())
        return self

    def set_note(self, note: str) -> "TableBuilder":
        """Set an explanatory note printed immediately after the table."""
        self.note_text = note.strip() if note else None
        return self

    def set_continuation_label(self, label: str) -> "TableBuilder":
        """Customize the text shown at the top of continuation pages."""
        self.continuation_label = label
        return self

    def build(self) -> str:
        """Assemble the complete LaTeX longtable block."""
        parts = []

        # 1. Begin environment
        parts.append(rf"\begin{{longtable}}{{{self.col_spec}}}")

        # 2. Caption and optional label - MUST terminate with \\ in longtable
        caption_clean = self.caption
        if not caption_clean.startswith(r"\textbf"):
            caption_clean = rf"\textbf{{{caption_clean}}}"

        label_str = rf"\label{{{self.label}}}" if self.label else ""
        parts.append(rf"\caption{{{caption_clean}}}{label_str}\\")

        # 3. First page header
        num_c = self._inferred_cols
        header_line = self.raw_header_str or ""
        if header_line:
            parts.append(r"\hline")
            parts.append(header_line)
            parts.append(r"\hline")
            parts.append(r"\endfirsthead")

            # 4. Continuation page header
            parts.append("")
            cont_text = self.continuation_label or r"\small\textit{Table \thetable{} continued from previous page}"
            parts.append(rf"\multicolumn{{{num_c}}}{{c}}{{{cont_text}}} \\[4pt]")
            parts.append(r"\hline")
            parts.append(header_line)
            parts.append(r"\hline")
            parts.append(r"\endhead")

            # 5. Page-break footer
            parts.append("")
            parts.append(r"\hline")
            parts.append(rf"\multicolumn{{{num_c}}}{{r}}{{\small\textit{{Continued on next page\ldots}}}} \\")
            parts.append(r"\endfoot")

            # 6. Final table bottom rule
            parts.append("")
            parts.append(r"\hline")
            parts.append(r"\endlastfoot")
        else:
            # Table without explicit header row (e.g. key-value tables)
            parts.append(r"\hline")
            parts.append(r"\endfirsthead")
            parts.append("")
            cont_text = self.continuation_label or r"\small\textit{Table \thetable{} continued from previous page}"
            parts.append(rf"\multicolumn{{{num_c}}}{{c}}{{{cont_text}}} \\[4pt]")
            parts.append(r"\hline")
            parts.append(r"\endhead")
            parts.append("")
            parts.append(r"\hline")
            parts.append(rf"\multicolumn{{{num_c}}}{{r}}{{\small\textit{{Continued on next page\ldots}}}} \\")
            parts.append(r"\endfoot")
            parts.append("")
            parts.append(r"\hline")
            parts.append(r"\endlastfoot")

        # 7. Body content
        if self.rows:
            parts.append("")
            parts.append("\n".join(self.rows))

        # 8. End environment
        parts.append(r"\end{longtable}")

        # 9. Optional note
        if self.note_text:
            parts.append(rf"\noindent\textit{{Note: {self.note_text}}}")

        return "\n".join(parts)


def format_longtable(
    col_spec: str,
    caption: str,
    headers: Optional[Union[List[str], str]] = None,
    content: str = "",
    label: Optional[str] = None,
    note: Optional[str] = None,
    num_cols: Optional[int] = None,
    continuation_title: Optional[str] = None,
) -> str:
    """Convenience helper to format a complete LaTeX longtable with headers and footers."""
    builder = TableBuilder(col_spec=col_spec, caption=caption, label=label, num_cols=num_cols)
    if headers:
        builder.set_headers(headers)
    if content:
        builder.add_raw_content(content)
    if note:
        builder.set_note(note)
    if continuation_title:
        builder.set_continuation_label(continuation_title)
    return builder.build()
