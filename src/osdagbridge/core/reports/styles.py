"""OsdagBridge report styles -- the single source of truth for visual formatting.

Every font, colour, page dimension, table spacing, caption and header/footer
setting used by the PDF report is defined here. Chapters never hard-code
these values: they use the LaTeX names generated below (colours such as
``osdagFail``, lengths such as ``\\osdagRowGap``, macros such as
``\\osdagHeadRow``), and the Matplotlib charts read the same constants via
``chart_rc()`` and the colour constants.

To change the look of the report, edit the values in this file only.
"""

# ── Page ────────────────────────────────────────────────────────────────────
PAPER = "a4paper"
MARGIN_TOP = "25mm"
MARGIN_BOTTOM = "25mm"
MARGIN_LEFT = "20mm"
MARGIN_RIGHT = "20mm"
HEAD_HEIGHT = "18pt"     # fancyhdr needs >= 17.5pt for the 12pt header line
HEAD_SEP = "6mm"
FOOT_SKIP = "15mm"

# ── Fonts ───────────────────────────────────────────────────────────────────
BASE_FONT_SIZE = "12pt"
# "computer-modern" (LaTeX default) or "times" (Times via mathptmx).
FONT_FAMILY = "computer-modern"
LINE_SPACING = 1.15
CHAPTER_HEADING_SIZE = r"\Large"
SECTION_HEADING_SIZE = r"\Large"      # LaTeX report-class default
SUBSECTION_HEADING_SIZE = r"\large"
CHAPTER_SPACE_BEFORE = "-30pt"   # space above chapter headings
CHAPTER_SPACE_AFTER = "10pt"

# ── Colours (hex, no '#') ───────────────────────────────────────────────────
OSDAG_GREEN = "91B014"        # brand green: header/footer rules
HEADING_COLOR = "5A700D"      # darker brand green, 5.6:1 on white (readable text)
TABLE_HEADER_FILL = "EEF3DC"  # light brand-green band behind table header rows
TEXT_COLOR = "000000"
STATUS_PASS_COLOR = "000000"  # PASS text / passing values: normal ink
STATUS_FAIL_COLOR = "D03B3B"  # FAIL text / failing values (same red as charts)

# ── Tables ──────────────────────────────────────────────────────────────────
TABLE_COL_SEP = "4pt"          # cell padding, all tables
TABLE_COL_SEP_COMPACT = "3.5pt"  # wide 7-column tables (Ch. 7, Ch. 8)
TABLE_COL_SEP_DENSE = "3pt"    # 9-column analysis table (Ch. 4)
TABLE_ARRAY_STRETCH = 1.12     # row height factor
TABLE_DENSE_ARRAY_STRETCH = 1.25
TABLE_RULE_WIDTH = "0.5pt"
TABLE_EXTRA_ROW_HEIGHT = "0.6pt"
TABLE_ROW_GAP = "6pt"          # space after each body row (\\[\osdagRowGap])
TABLE_ROW_GAP_SMALL = "3pt"
TABLE_ROW_GAP_LARGE = "8pt"
LONGTABLE_PRE = "0pt"
LONGTABLE_POST = "6pt"
# Extra room (lines) longtable requires before it starts a table on a page,
# so tables with tall first rows are not split from their caption.
LONGTABLE_START_RESERVE_LINES = 7
HEADING_KEEP_LINES = 8         # a heading needs this many lines below it
FLOAT_KEEP_LINES = 5

# ── Vertical spacing ────────────────────────────────────────────────────────
BLOCK_GAP = "1em"              # between consecutive tables / blocks
SMALL_GAP = "0.5em"            # before a table that follows text

# ── Captions ────────────────────────────────────────────────────────────────
CAPTION_LABEL_BOLD = True
TABLE_CAPTION_TEXT_BOLD = True
FIGURE_CAPTION_TEXT_BOLD = False
CAPTION_JUSTIFICATION = "raggedright"

# ── Header / footer ─────────────────────────────────────────────────────────
FOOTER_LEFT_TEXT = r"Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"
HEADER_RULE_WIDTH = "1pt"
FOOTER_RULE_WIDTH = "1pt"
SOFTWARE_DEFAULT_NOTE = r"* Software default value"

# ── Charts (Matplotlib) ─────────────────────────────────────────────────────
CHART_DPI = 200
CHART_PASS_COLOR = "#0ca30c"
CHART_FAIL_COLOR = "#" + STATUS_FAIL_COLOR.lower()
CHART_LIMIT_COLOR = CHART_FAIL_COLOR
CHART_QUANTITY_COLOR = "#6b8510"   # brand green, >= 3:1 on white for bars
CHART_INK = "#1f1f1f"
CHART_INK_MUTED = "#5f5f5f"
CHART_GRID = "#d9d9d9"
CHART_NO_DATA_EDGE = "#8a8a8a"
CHART_FONT_SIZE = 9

_CHART_FONTS = {
    "computer-modern": (["cmr10", "DejaVu Serif"], "cm"),
    "times": (["Times New Roman", "Nimbus Roman", "Nimbus Roman No9 L", "DejaVu Serif"], "stix"),
}


def chart_rc():
    """Matplotlib rcParams matching the report body font and colours."""
    serif, mathfont = _CHART_FONTS.get(FONT_FAMILY, _CHART_FONTS["computer-modern"])
    return {
        "font.family": "serif",
        "font.serif": serif,
        "mathtext.fontset": mathfont,
        "axes.formatter.use_mathtext": True,
        "axes.unicode_minus": False,
        "font.size": CHART_FONT_SIZE,
        "axes.edgecolor": CHART_INK_MUTED,
        "axes.labelcolor": CHART_INK,
        "xtick.color": CHART_INK_MUTED,
        "ytick.color": CHART_INK_MUTED,
    }


# ── LaTeX generation ────────────────────────────────────────────────────────

def document_class():
    return r"\documentclass[" + BASE_FONT_SIZE + "," + PAPER + "]{report}"


def geometry_package():
    return (r"\usepackage[" + PAPER + ", top=" + MARGIN_TOP + ", bottom=" + MARGIN_BOTTOM
            + ", left=" + MARGIN_LEFT + ", right=" + MARGIN_RIGHT + ", headheight=" + HEAD_HEIGHT
            + ", headsep=" + HEAD_SEP + ", footskip=" + FOOT_SKIP + "]{geometry}")


def font_packages():
    return r"\usepackage{mathptmx}" if FONT_FAMILY == "times" else ""


def _bf(flag):
    return "bf" if flag else "md"


def latex_style_definitions():
    """Colours, lengths, macros and formatting rules for the preamble.

    Emitted after the packages are loaded; chapters use only the names
    defined here.
    """
    return r"""
% ===== Styles generated from reports/styles.py (edit there, not here) =====
\definecolor{osdagGreen}{HTML}{""" + OSDAG_GREEN + r"""}
\definecolor{osdagHeading}{HTML}{""" + HEADING_COLOR + r"""}
\definecolor{osdagTableHead}{HTML}{""" + TABLE_HEADER_FILL + r"""}
\definecolor{osdagText}{HTML}{""" + TEXT_COLOR + r"""}
\definecolor{osdagPass}{HTML}{""" + STATUS_PASS_COLOR + r"""}
\definecolor{osdagFail}{HTML}{""" + STATUS_FAIL_COLOR + r"""}

% Tables
\setlength{\tabcolsep}{""" + TABLE_COL_SEP + r"""}
\renewcommand{\arraystretch}{""" + f"{TABLE_ARRAY_STRETCH:g}" + r"""}
\setlength{\LTpre}{""" + LONGTABLE_PRE + r"""}
\setlength{\LTpost}{""" + LONGTABLE_POST + r"""}
\setlength{\arrayrulewidth}{""" + TABLE_RULE_WIDTH + r"""}
\setlength{\extrarowheight}{""" + TABLE_EXTRA_ROW_HEIGHT + r"""}
\newlength{\osdagRowGap}\setlength{\osdagRowGap}{""" + TABLE_ROW_GAP + r"""}
\newlength{\osdagRowGapSmall}\setlength{\osdagRowGapSmall}{""" + TABLE_ROW_GAP_SMALL + r"""}
\newlength{\osdagRowGapLarge}\setlength{\osdagRowGapLarge}{""" + TABLE_ROW_GAP_LARGE + r"""}
\newlength{\osdagColSepCompact}\setlength{\osdagColSepCompact}{""" + TABLE_COL_SEP_COMPACT + r"""}
\newlength{\osdagColSepDense}\setlength{\osdagColSepDense}{""" + TABLE_COL_SEP_DENSE + r"""}
\newcommand{\osdagDenseStretch}{\renewcommand{\arraystretch}{""" + f"{TABLE_DENSE_ARRAY_STRETCH:g}" + r"""}}
% Shaded table header row: put \osdagHeadRow at the start of each header row.
\newcommand{\osdagHeadRow}{\rowcolor{osdagTableHead}}

% Status values (PASS / FAIL, utilization ratios)
\newcommand{\osdagPassText}[1]{\textcolor{osdagPass}{#1}}
\newcommand{\osdagFailText}[1]{\textcolor{osdagFail}{#1}}

% Vertical spacing
\newlength{\osdagBlockGap}\setlength{\osdagBlockGap}{""" + BLOCK_GAP + r"""}
\newlength{\osdagSmallGap}\setlength{\osdagSmallGap}{""" + SMALL_GAP + r"""}

% Keep headings / floats with following content
\BeforeBeginEnvironment{table}{\needspace{""" + str(FLOAT_KEEP_LINES) + r"""\baselineskip}}
\pretocmd{\section}{\needspace{""" + str(HEADING_KEEP_LINES) + r"""\baselineskip}}{}{}
\pretocmd{\subsection}{\needspace{""" + str(HEADING_KEEP_LINES) + r"""\baselineskip}}{}{}

% Captions
\captionsetup{labelfont=""" + _bf(CAPTION_LABEL_BOLD) + r""", justification=""" + CAPTION_JUSTIFICATION + r""", singlelinecheck=false, format=plain}
\captionsetup[table]{textfont=""" + _bf(TABLE_CAPTION_TEXT_BOLD) + r"""}
\captionsetup[figure]{textfont=""" + _bf(FIGURE_CAPTION_TEXT_BOLD) + r"""}

% Headings
\titleformat{\chapter}[block]
  {\normalfont""" + CHAPTER_HEADING_SIZE + r"""\bfseries\centering\color{osdagHeading}}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{""" + CHAPTER_SPACE_BEFORE + r"""}{""" + CHAPTER_SPACE_AFTER + r"""}
% Unnumbered chapter-level heading (e.g. Executive Summary), same look
\newcommand{\osdagUnnumberedHeading}[1]{{\centering\normalfont""" + CHAPTER_HEADING_SIZE + r"""\bfseries\color{osdagHeading} #1\par}}
\titleformat*{\section}{\normalfont""" + SECTION_HEADING_SIZE + r"""\bfseries\color{osdagHeading}}
\titleformat*{\subsection}{\normalfont""" + SUBSECTION_HEADING_SIZE + r"""\bfseries\color{osdagHeading}}

% Header / footer rules (used by the page styles)
\newcommand{\osdagHeadRule}{{\color{osdagGreen}\hrule width\headwidth height """ + HEADER_RULE_WIDTH + r"""}\vspace{2pt}}
\newcommand{\osdagFootRule}{{\color{osdagGreen}\hrule width\headwidth height """ + FOOTER_RULE_WIDTH + r"""}\vspace{4pt}}
\newcommand{\osdagFooterLeft}{""" + FOOTER_LEFT_TEXT + r"""}
\newcommand{\osdagSoftwareDefaultNote}{\footnotesize\textit{""" + SOFTWARE_DEFAULT_NOTE + r"""}}
"""


def line_spacing():
    return r"\setstretch{" + f"{LINE_SPACING:g}" + "}"


def longtable_start_reserve():
    return r"\setlength{\LTstartreserve}{" + str(LONGTABLE_START_RESERVE_LINES) + r"\baselineskip}"
