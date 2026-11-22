# =============================================================================
# OsdagBridge Report Style System — Single Source of Truth
# =============================================================================
# All formatting, colour, spacing, and visual parameters for the report are
# defined here. Import from this module in every chapter/generator file so a
# single change here propagates everywhere.
#
# Usage in chapter files
# ----------------------
#   from osdagbridge.core.reports.styles import STYLE
#
#   # LaTeX helpers
#   tex = STYLE.tex_pass()           → "PASS"
#   tex = STYLE.tex_fail()           → r"\textcolor{red}{FAIL}"
#   tex = STYLE.lt_reset()           → LaTeX snippet to reset LT margins
#   tex = STYLE.table_narrow()       → narrow tabcolsep override
#
#   # Chart helpers (matplotlib / Pillow)
#   c   = STYLE.CLR.PRIMARY          → "#91B014"
#   c   = STYLE.CLR.PASS_BAR         → "#2E7D32"
#   fig_kw = STYLE.MPL.fig_kw_2x2   → {figsize, dpi} dict for 2×2 UR charts
# =============================================================================

from __future__ import annotations
from typing import NamedTuple


# ─────────────────────────────────────────────────────────────────────────────
# 1. PAGE GEOMETRY  (LaTeX geometry package options)
# ─────────────────────────────────────────────────────────────────────────────
class _PageGeometry(NamedTuple):
    top_mm: int     = 25
    bottom_mm: int  = 32
    left_mm: int    = 20
    right_mm: int   = 20
    headheight_pt: int  = 16
    headsep_pt: int     = 12
    footskip_mm: int    = 16

PAGE = _PageGeometry()


def page_geometry_tex() -> str:
    """Return the LaTeX geometry package option string."""
    return (
        f"  a4paper,\n"
        f"  top={PAGE.top_mm}mm,\n"
        f"  bottom={PAGE.bottom_mm}mm,\n"
        f"  left={PAGE.left_mm}mm,\n"
        f"  right={PAGE.right_mm}mm,\n"
        f"  headheight={PAGE.headheight_pt}pt,\n"
        f"  headsep={PAGE.headsep_pt}pt,\n"
        f"  footskip={PAGE.footskip_mm}mm"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. TYPOGRAPHY & LINE SPACING
# ─────────────────────────────────────────────────────────────────────────────
class _Typography(NamedTuple):
    base_font_pt: int       = 12
    line_stretch: float     = 1.15     # \setstretch
    array_stretch: float    = 1.10     # \arraystretch (row height multiplier)

TYPO = _Typography()


# ─────────────────────────────────────────────────────────────────────────────
# 3. TABLE LAYOUT SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
class _TableLayout(NamedTuple):
    tabcolsep_pt: float         = 5.0   # default inter-column half-padding
    tabcolsep_narrow_pt: float  = 3.5   # for wide/dense tables (chap7, chap8)
    tabcolsep_wide_pt: float    = 4.0   # for medium-density tables (chap2, chap5 ED)
    lt_pre_pt: float            = 4.0   # \LTpre
    lt_post_pt: float           = 6.0   # \LTpost
    arrayrulewidth_pt: float    = 0.5   # \arrayrulewidth
    extrarowheight_pt: float    = 0.5   # \extrarowheight
    abovecaptionskip_pt: float  = 2.0   # \abovecaptionskip
    belowcaptionskip_pt: float  = 2.0   # \belowcaptionskip

TABLE = _TableLayout()


def table_global_tex() -> str:
    """Global table settings injected once in the LaTeX preamble."""
    return (
        f"\\setlength{{\\tabcolsep}}{{{TABLE.tabcolsep_pt}pt}}\n"
        f"\\renewcommand{{\\arraystretch}}{{{TYPO.array_stretch}}}\n"
        f"\\setlength{{\\LTpre}}{{{TABLE.lt_pre_pt}pt}}\n"
        f"\\setlength{{\\LTpost}}{{{TABLE.lt_post_pt}pt}}\n"
        f"\\setlength{{\\arrayrulewidth}}{{{TABLE.arrayrulewidth_pt}pt}}\n"
        f"\\setlength{{\\extrarowheight}}{{{TABLE.extrarowheight_pt}pt}}"
    )


def table_narrow_tex() -> str:
    """Override for dense tables — use inside \\begingroup/\\endgroup."""
    return f"\\setlength{{\\tabcolsep}}{{{TABLE.tabcolsep_narrow_pt}pt}}"


def table_wide_tex() -> str:
    """Override for medium-density tables — use inside \\begingroup/\\endgroup."""
    return f"\\setlength{{\\tabcolsep}}{{{TABLE.tabcolsep_wide_pt}pt}}"


def lt_full_width_tex() -> str:
    """Make a longtable span full text-width (reset LTleft/LTright to zero)."""
    return "\\setlength{\\LTleft}{0pt}\n\\setlength{\\LTright}{\\fill}"


def lt_centered_tex() -> str:
    """Center a longtable on the page (default global setting)."""
    return "\\setlength{\\LTleft}{\\fill}\n\\setlength{\\LTright}{\\fill}"


def caption_spacing_tex() -> str:
    """Caption spacing overrides for dense layouts."""
    return (
        f"\\setlength{{\\abovecaptionskip}}{{{TABLE.abovecaptionskip_pt}pt}}\n"
        f"\\setlength{{\\belowcaptionskip}}{{{TABLE.belowcaptionskip_pt}pt}}"
    )


def caption_setup_tex() -> str:
    """Return LaTeX \\captionsetup configurations for tables and figures.
    - Tables: left-aligned (raggedright) per engineering documentation standard.
    - Figures: centered (justification=centering) for balanced visual presentation.
    """
    return (
        "\\captionsetup[table]{\n"
        "    labelfont=bf,\n"
        "    justification=raggedright,\n"
        "    singlelinecheck=false,\n"
        "    format=plain,\n"
        "    skip=4pt\n"
        "}\n"
        "\\captionsetup[figure]{\n"
        "    labelfont=bf,\n"
        "    justification=centering,\n"
        "    singlelinecheck=false,\n"
        "    format=plain,\n"
        "    font=small,\n"
        "    skip=6pt\n"
        "}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. NEEDSPACE THRESHOLDS
# ─────────────────────────────────────────────────────────────────────────────
class _Needspace(NamedTuple):
    before_table: int       = 8   # baselineskips before \table float
    before_section: int     = 6   # baselineskips before \section
    before_subsection: int  = 5   # baselineskips before \subsection

NEEDSPACE = _Needspace()


def needspace_preamble_tex() -> str:
    """Return \\BeforeBeginEnvironment and \\pretocmd blocks for the preamble.
    Uses \\Needspace* (exact calculation with space suppression) to avoid
    awkward page breaks and stray longtable continuation headers.
    """
    return (
        f"\\BeforeBeginEnvironment{{table}}{{\\Needspace*{{{NEEDSPACE.before_table}\\baselineskip}}}}\n"
        f"\\pretocmd{{\\section}}{{\\Needspace*{{{NEEDSPACE.before_section}\\baselineskip}}}}{{}}{{}}\n"
        f"\\pretocmd{{\\subsection}}{{\\Needspace*{{{NEEDSPACE.before_subsection}\\baselineskip}}}}{{}}{{}}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────
class _Colors:
    # Brand
    PRIMARY         = "#91B014"   # osdagGreen
    PRIMARY_DARK    = "#6E8710"   # darker variant for pressed states

    # Status — LaTeX
    FAIL_LATEX      = "red"
    PASS_LATEX      = "black"

    # Status — Python charts
    PASS_BAR        = "#2E7D32"   # dark green bar fill (UR ≤ 1.0)
    PASS_EDGE       = "#1B5E20"   # green bar outline
    PASS_DARK       = "#1B5E20"   # darker green (Pillow outline)
    FAIL_BAR        = "#C62828"   # red bar fill (UR > 1.0)
    FAIL_EDGE       = "#851A1A"   # red bar outline
    THRESHOLD_LINE  = "#D32F2F"   # dashed UR=1.0 threshold line

    # Steel breakdown chart
    STEEL_GIRDER    = "#1976D2"
    STEEL_GIRDER_E  = "#0D47A1"
    STEEL_CB        = "#00897B"
    STEEL_CB_E      = "#004D40"
    STEEL_ED        = "#FB8C00"
    STEEL_ED_E      = "#E65100"

    # Concrete vs Rebar chart
    CONCRETE_BAR    = "#546E7A"
    CONCRETE_EDGE   = "#263238"
    REBAR_BAR       = "#D32F2F"
    REBAR_EDGE      = "#B71C1C"

    # UI general
    TITLE_DARK      = "#1A237E"   # navy for chart/subplot titles
    TEXT_DARK       = "#111111"   # annotation text
    TEXT_MID        = "#222222"   # axis labels
    TEXT_LIGHT      = "#555555"   # tick labels
    TEXT_FAINT      = "#333333"   # x-axis bar labels
    AXIS_LINE       = "#444444"   # axis / frame lines
    GRID            = "#F0F0F0"   # horizontal gridlines
    PANEL_BORDER    = "#E0E0E0"   # Pillow panel border
    GRID_LINE       = "#F0F0F0"   # horizontal gridlines
    TICK_LABEL      = "#555555"   # tick labels
    BAR_LABEL       = "#333333"   # x-axis bar labels
    FAIL_DARK       = "#851A1A"   # red bar outline

    # Badge backgrounds
    BADGE_STEEL_BG  = "#E3F2FD"
    BADGE_STEEL_BD  = "#1976D2"
    BADGE_STEEL_TXT = "#0D47A1"
    BADGE_REBAR_BG  = "#FFEBEE"
    BADGE_REBAR_BD  = "#D32F2F"
    BADGE_REBAR_TXT = "#B71C1C"

CLR = _Colors()


def tex_color_def() -> str:
    """Return \\definecolor declarations for the LaTeX preamble."""
    return f"\\definecolor{{osdagGreen}}{{HTML}}{{{CLR.PRIMARY.lstrip('#')}}}"


def tex_pass() -> str:
    """Return LaTeX-safe 'PASS' string (plain text, no colour)."""
    return "PASS"


def tex_fail(label: str = "FAIL") -> str:
    """Return LaTeX red-coloured FAIL string."""
    return f"\\textcolor{{{CLR.FAIL_LATEX}}}{{{label}}}"


def tex_status(passed: bool, label_pass: str = "PASS", label_fail: str = "FAIL") -> str:
    """Return PASS or \\textcolor{red}{FAIL} depending on the boolean."""
    return tex_pass() if passed else tex_fail(label_fail)


# ─────────────────────────────────────────────────────────────────────────────
# 6. HEADER / FOOTER THEME
# ─────────────────────────────────────────────────────────────────────────────
class _HeaderFooter(NamedTuple):
    rule_height_pt: float   = 1.0    # thickness of the green rule
    rule_vspace_after: int  = 2      # \vspace{Xpt} after head rule
    foot_vspace_after: int  = 6      # \vspace{Xpt} after foot rule
    sd_note_vspace: int     = 2      # \vspace after "* Software default value"
    footer_org: str = "Osdag $|$ FOSSEE $|$ Indian Institute of Technology Bombay"

HF = _HeaderFooter()


# ─────────────────────────────────────────────────────────────────────────────
# 7. MATPLOTLIB CHART SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
class _MplSettings:
    # Resolution
    DPI_STANDARD = 200   # general charts (UR)
    DPI_HIGH     = 300   # publication-quality (BOQ)

    # Figure sizes (width, height) in inches
    FIGSIZE_2x2  = (11, 8.5)    # UR summary 2×2 grid
    FIGSIZE_1x2  = (13.5, 5.5)  # BOQ combined 2-panel
    FIGSIZE_1x1  = (7, 5)       # single standalone chart

    # Font sizes
    FONT_TITLE_LG  = 13    # main chart title
    FONT_TITLE_SM  = 11    # subplot title
    FONT_LABEL     = 11    # axis labels
    FONT_TICK      = 8.5   # tick labels
    FONT_ANNOT_LG  = 10.5  # bar value annotations (BOQ)
    FONT_ANNOT_SM  = 8.5   # bar value annotations (UR)
    FONT_LEGEND    = 8     # legend text

    # Bar widths
    BAR_WIDTH_NARROW = 0.48
    BAR_WIDTH_MED    = 0.55

MPL = _MplSettings()


# ─────────────────────────────────────────────────────────────────────────────
# 8. PILLOW CHART SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
class _PillowSettings:
    # Canvas sizes
    CANVAS_UR_W  = 1800
    CANVAS_UR_H  = 1350
    CANVAS_BOQ_W = 1500
    CANVAS_BOQ_H = 620

    # Font sizes (pixel)
    FONT_TITLE   = 20
    FONT_SUB     = 16
    FONT_LABEL   = 14
    FONT_VAL     = 15
    FONT_BADGE   = 13
    FONT_LEGEND  = 16

    # Font paths (try these in order)
    FONT_BOLD   = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
    FONT_NORMAL = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"

PIL_S = _PillowSettings()


def pil_load_fonts(size_title: int = PIL_S.FONT_TITLE, size_sub: int = PIL_S.FONT_SUB,
                   size_label: int = PIL_S.FONT_LABEL, size_val: int = PIL_S.FONT_VAL,
                   size_badge: int = PIL_S.FONT_BADGE, size_legend: int = PIL_S.FONT_LEGEND):
    """Load Pillow fonts from the canonical DejaVu paths, falling back to default."""
    from PIL import ImageFont
    def _load(path, size):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    return {
        "title":  _load(PIL_S.FONT_BOLD,   size_title),
        "sub":    _load(PIL_S.FONT_BOLD,   size_sub),
        "label":  _load(PIL_S.FONT_NORMAL, size_label),
        "val":    _load(PIL_S.FONT_BOLD,   size_val),
        "badge":  _load(PIL_S.FONT_BOLD,   size_badge),
        "legend": _load(PIL_S.FONT_NORMAL, size_legend),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 9. CONVENIENCE LATEX SNIPPETS
# ─────────────────────────────────────────────────────────────────────────────

def lt_needspace_tex(lines: int = 6) -> str:
    """Return LaTeX snippet ensuring minimum vertical space before longtable entry.
    Prevents tables from starting with 0 data rows at the bottom of a page,
    which causes spurious continuation headers at the top of the next page.
    """
    return f"\\par\\Needspace*{{{lines}\\baselineskip}}\\vspace{{0.8em}}"


def longtable_header_row(*cols: str, row_extra: str = r"\\[6pt]") -> str:
    """Format a standard longtable \\endhead / \\endfirsthead header row.

    Parameters
    ----------
    *cols : bold column header text strings (already escaped / LaTeX-safe).
    row_extra : trailing row terminator (default \\\\[6pt]).
    """
    cells = " & ".join(f"\\textbf{{{c}}}" for c in cols)
    return cells + " " + row_extra


def longtable_env(caption: str, col_spec: str, header_row: str, body: str,
                  full_width: bool = False) -> str:
    """Generate a complete longtable environment string.

    Parameters
    ----------
    caption     : table caption (plain text; will be bolded in LaTeX).
    col_spec    : column specification string e.g. '|C{2cm}|L{5cm}|'
    header_row  : formatted header row string (from longtable_header_row()).
    body        : table body rows (pre-rendered string).
    full_width  : if True, inject LTleft/LTright = 0 / fill.
    """
    lt_width = lt_full_width_tex() + "\n" if full_width else ""
    return (
        f"{lt_width}"
        f"\\begin{{longtable}}{{{col_spec}}}\n"
        f"\\caption{{\\textbf{{{caption}}}}}\\\\\n"
        f"\\hline\n"
        f"{header_row}\n"
        f"\\hline\n"
        f"\\endfirsthead\n"
        f"\\hline\n"
        f"{header_row}\n"
        f"\\hline\n"
        f"\\endhead\n"
        f"{body}\n"
        f"\\end{{longtable}}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10. MASTER STYLE FACADE  (single import point for chapter files)
# ─────────────────────────────────────────────────────────────────────────────
class _Style:
    """Master facade — import STYLE and access everything through it."""
    # Sub-namespaces
    PAGE        = PAGE
    TYPO        = TYPO
    TABLE       = TABLE
    NEEDSPACE   = NEEDSPACE
    CLR         = CLR
    HF          = HF
    MPL         = MPL
    PIL         = PIL_S

    # Page geometry
    page_geometry_tex   = staticmethod(page_geometry_tex)

    # Table helpers
    table_global_tex    = staticmethod(table_global_tex)
    table_narrow_tex    = staticmethod(table_narrow_tex)
    table_wide_tex      = staticmethod(table_wide_tex)
    lt_full_width_tex   = staticmethod(lt_full_width_tex)
    lt_centered_tex     = staticmethod(lt_centered_tex)
    caption_spacing_tex = staticmethod(caption_spacing_tex)
    caption_setup_tex   = staticmethod(caption_setup_tex)
    lt_needspace_tex    = staticmethod(lt_needspace_tex)

    # Needspace
    needspace_preamble_tex = staticmethod(needspace_preamble_tex)

    # Colours / branding
    tex_color_def       = staticmethod(tex_color_def)

    # Status strings
    tex_pass            = staticmethod(tex_pass)
    tex_fail            = staticmethod(tex_fail)
    tex_status          = staticmethod(tex_status)

    # Longtable helpers
    longtable_header_row = staticmethod(longtable_header_row)
    longtable_env        = staticmethod(longtable_env)

    # Pillow font loader
    pil_load_fonts      = staticmethod(pil_load_fonts)


STYLE = _Style()

__all__ = ["STYLE", "PAGE", "TYPO", "TABLE", "NEEDSPACE", "CLR", "HF", "MPL", "PIL_S"]
