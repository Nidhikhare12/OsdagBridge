"""Shared report layout and chart styling."""
import re

BRAND_GREEN = "91B014"
PAGE_MARGIN = "1in"
HEADER_HEIGHT = "18pt"
FOOTER_SKIP = "30pt"
TABLE_PADDING = "4pt"
TABLE_ROW_STRETCH = "1.12"
TABLE_START_SPACE = "9"
SECTION_TABLE_START_SPACE = "13"
CHAPTER_AFTER_SPACE = "10pt"
TABLE_COMPACT_PADDING = "3pt"
TABLE_MEDIUM_PADDING = "3.5pt"
TABLE_RULE_WIDTH = "0.5pt"
TABLE_EXTRA_ROW_HEIGHT = "0.6pt"
TABLE_AFTER_SPACE = "6pt"
CHART_SIZE = (8, 6)
CHART_DPI = 150

TABLE_LAYOUT = r"""
% The caption precedes this macro and belongs only to the first-page head.
\newcommand{\ReportTableHeader}[1]{%
  \hline #1\hline\endfirsthead
  \hline #1\hline\endhead
}
"""


def fit_table_columns(tex):
    """Fit fixed-width table columns inside the text block, including rules."""
    dimension = re.compile(r"(?<=[CLRp])\{(\d+(?:\.\d+)?)cm\}")
    declaration = re.compile(
        r"(?m)(^\\begin\{(?:longtable|tabular)\}\{)((?:[^{}]|\{[^{}]*\})*)\}"
    )

    def fit(match):
        columns = match[2]
        widths = [float(width) for width in dimension.findall(columns)]
        remaining = re.sub(r"%[^\n]*|[<>]\{[^{}]*\}|[CLRp]\{\d+(?:\.\d+)?cm\}|[\s|]", "", columns)
        if not widths or remaining:
            return match[0]
        total = sum(widths)
        rules = columns.count("|")

        def width(cell):
            fraction = float(cell[1]) / total
            return (rf"{{\dimexpr{fraction:.8f}\linewidth"
                    rf"-{2 * len(widths) * fraction:.8f}\tabcolsep"
                    rf"-{rules * fraction:.8f}\arrayrulewidth\relax}}")

        return match[1] + dimension.sub(width, columns) + "}"

    return declaration.sub(fit, tex)
