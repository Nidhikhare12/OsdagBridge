"""Centralized report styling and theme system for OsdagBridge.

Single source of truth for:
- Document geometry, margins, fonts, colors, and header/footer rules.
- Table padding, row spacing, borders, and column-layout presets.
- Longtable continuation captions and page-break protection.
- Chart themes, DPI, dimensions, and color coding.
"""

# Document configuration
PAGE_SIZE = "a4paper"
FONT_SIZE = "12pt"
PAGE_MARGIN = "1in"
HEAD_HEIGHT = "26pt"
TOP_MARGIN = "1.2in"
BOTTOM_MARGIN = "1.2in"
LINE_SPACING = 1.15
TEXTWIDTH_CM = 15.92  # Printable text width on A4 with 1-inch margins

GEOMETRY_OPTIONS = (
    f"{PAGE_SIZE}, margin={PAGE_MARGIN}, headheight={HEAD_HEIGHT}, "
    f"top={TOP_MARGIN}, bottom={BOTTOM_MARGIN}"
)

# Color palette
PRIMARY_GREEN = "91B014"         # Osdag green (Hex HTML without # for xcolor)
COLOR_OSDAG_GREEN = "#91B014"    # Hex HTML with # for matplotlib
COLOR_PASS = "#2ca02c"           # Green for PASS checks
COLOR_FAIL = "#d62728"           # Red for FAIL checks
COLOR_THRESHOLD = "#e41a1c"      # Red dashed line for UR = 1.0 limit
COLOR_UNAVAILABLE = "#9e9e9e"    # Gray for NOT CALCULATED / UNAVAILABLE
COLOR_ACCENT = "#1f77b4"         # Steel blue accent
COLOR_GRID = "#e8e8e8"           # Light gray for chart grids

# Table formatting presets
TABLE_COLUMN_PADDING = "4pt"          # Standard tabcolsep
TABLE_COLUMN_PADDING_COMPACT = "3pt"  # Compact tabcolsep for wide 7-8 column tables
TABLE_ROW_STRETCH = 1.25              # Standard arraystretch
TABLE_ROW_STRETCH_COMPACT = 1.15      # Compact arraystretch
TABLE_RULE_WIDTH = "0.5pt"
TABLE_EXTRA_ROW_HEIGHT = "0.6pt"
LONGTABLE_PRE_SKIP = "0pt"
LONGTABLE_POST_SKIP = "6pt"

# Page-break protection
MIN_TABLE_SPACE = 5                   # lines of space before table page-break

# Chart configuration presets
CHART_DPI = 300
CHART_FIGSIZE_WIDE = (8.5, 4.5)
CHART_FIGSIZE_SUMMARY = (9.5, 6.0)
CHART_FIGSIZE_HALF = (6.0, 4.0)


def document_style() -> str:
    """Return shared LaTeX document and table settings."""
    return rf"""
\setlength{{\tabcolsep}}{{{TABLE_COLUMN_PADDING}}}
\renewcommand{{\arraystretch}}{{{TABLE_ROW_STRETCH}}}
\setlength{{\arrayrulewidth}}{{{TABLE_RULE_WIDTH}}}
\setlength{{\extrarowheight}}{{{TABLE_EXTRA_ROW_HEIGHT}}}
\setlength{{\LTpre}}{{{LONGTABLE_PRE_SKIP}}}
\setlength{{\LTpost}}{{{LONGTABLE_POST_SKIP}}}

\BeforeBeginEnvironment{{table}}{{\needspace{{{MIN_TABLE_SPACE}\baselineskip}}}}
\BeforeBeginEnvironment{{longtable}}{{\needspace{{{MIN_TABLE_SPACE}\baselineskip}}}}

\definecolor{{osdagGreen}}{{HTML}}{{{PRIMARY_GREEN}}}
\setstretch{{{LINE_SPACING}}}
"""


def longtable_continuation_caption(caption_text: str) -> str:
    """Return a standardized continuation caption for longtables."""
    return rf"\caption[]{{\textbf{{{caption_text} (Continued)}}}}\\"


def format_status_badge(status_str: str) -> str:
    """Format status string consistently across all report chapters."""
    if not status_str or str(status_str).strip() in ("", "None", "---"):
        return "---"
    s = str(status_str).strip().upper()
    if "FAIL" in s:
        return r"\textcolor{red}{FAIL}"
    elif "PASS" in s:
        return "PASS"
    elif "PARTIAL" in s:
        return r"\textcolor{orange}{PARTIAL}"
    elif "NOT CALCULATED" in s or "UNAVAILABLE" in s:
        return r"\textit{NOT CALCULATED}"
    elif "NOT APPLICABLE" in s:
        return r"\textit{NOT APPLICABLE}"
    return str(status_str)
