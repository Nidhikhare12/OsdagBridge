"""Centralized styling and theme system for OsdagBridge LaTeX reports.

Single source of truth for all LaTeX colors, page geometry, typography,
and table formatting parameters.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class ReportTheme:
    """Design tokens and visual parameters for LaTeX reports."""

    # Page geometry (compact enterprise density)
    top_margin: str = "2.0cm"
    bottom_margin: str = "2.2cm"
    left_margin: str = "1.8cm"
    right_margin: str = "1.8cm"
    head_height: str = "16pt"
    head_sep: str = "12pt"
    foot_skip: str = "22pt"
    include_head_foot: bool = True

    # Color palette (hex format) - Premium Architectural Green Brand Palette
    primary: str = "#16331C"       # Deep premium forest green for primary headings and display rules
    accent: str = "#5E8014"        # Rich olive green accent matching the Osdag logo
    osdag_green: str = "#789A1B"   # Signature Osdag Green from brand logo
    osdag_green_light: str = "#EBF2DE" # Light green accent
    header_bg: str = "#EBF2DE"     # Light green based accent for table headers
    zebra: str = "#F7FAF3"         # Soft warm tint for alternating table rows
    pass_color: str = "#226B28"    # High-contrast emerald green for SAFE / PASS status
    fail_color: str = "#B91C1C"    # Crimson red for UNSAFE / FAIL status
    border: str = "#CCD7C5"        # Subtle sage-slate border for tables and cards
    muted: str = "#455443"         # Deep sage charcoal for secondary notes and captions

    # Table layout parameters (compact, compressed enterprise density)
    array_stretch: float = 1.15    # Vertical padding factor for table rows
    tab_col_sep: str = "4.5pt"     # Horizontal column padding
    lt_pre: str = "4pt"            # Space before longtable
    lt_post: str = "5pt"           # Space after longtable
    array_rule_width: str = "0.45pt" # Thickness of table grid rules

    # Vector and raster graphics resolution
    chart_dpi: int = 300

    def hex_to_rgb_tuple(self, hex_code: str) -> tuple[float, float, float]:
        """Convert a hex color code to a normalized (0.0 to 1.0) RGB tuple."""
        clean = hex_code.lstrip("#")
        return (
            int(clean[0:2], 16) / 255.0,
            int(clean[2:4], 16) / 255.0,
            int(clean[4:6], 16) / 255.0,
        )


DEFAULT_THEME = ReportTheme()


def get_latex_color_definitions(theme: ReportTheme = DEFAULT_THEME) -> str:
    """Generate LaTeX color definitions for the document preamble."""
    return f"""% OsdagBridge centralized palette definitions
\\definecolor{{OsdagPrimary}}{{HTML}}{{{theme.primary.lstrip('#')}}}
\\definecolor{{OsdagAccent}}{{HTML}}{{{theme.accent.lstrip('#')}}}
\\definecolor{{OsdagGreen}}{{HTML}}{{{theme.osdag_green.lstrip('#')}}}
\\definecolor{{OsdagGreenLight}}{{HTML}}{{{theme.osdag_green_light.lstrip('#')}}}
\\definecolor{{OsdagHeaderBg}}{{HTML}}{{{theme.header_bg.lstrip('#')}}}
\\definecolor{{OsdagZebra}}{{HTML}}{{{theme.zebra.lstrip('#')}}}
\\definecolor{{OsdagPass}}{{HTML}}{{{theme.pass_color.lstrip('#')}}}
\\definecolor{{OsdagFail}}{{HTML}}{{{theme.fail_color.lstrip('#')}}}
\\definecolor{{OsdagBorder}}{{HTML}}{{{theme.border.lstrip('#')}}}
\\definecolor{{OsdagMuted}}{{HTML}}{{{theme.muted.lstrip('#')}}}
% Legacy alias to maintain backward compatibility
\\definecolor{{osdagGreen}}{{HTML}}{{{theme.osdag_green.lstrip('#')}}}
"""


def get_geometry_preamble(theme: ReportTheme = DEFAULT_THEME) -> str:
    """Generate geometry package options with explicit head/foot dimensions."""
    headfoot_str = "includeheadfoot" if theme.include_head_foot else ""
    return (
        f"\\usepackage[a4paper, top={theme.top_margin}, bottom={theme.bottom_margin}, "
        f"left={theme.left_margin}, right={theme.right_margin}, "
        f"headheight={theme.head_height}, headsep={theme.head_sep}, "
        f"footskip={theme.foot_skip}, {headfoot_str}]{{geometry}}\n"
    )


def get_table_spacing_preamble(theme: ReportTheme = DEFAULT_THEME) -> str:
    """Generate global table padding and row height commands."""
    return f"""% Centralized table geometry and padding
\\setlength{{\\tabcolsep}}{{{theme.tab_col_sep}}}
\\renewcommand{{\\arraystretch}}{{{theme.array_stretch}}}
\\setlength{{\\LTpre}}{{{theme.lt_pre}}}
\\setlength{{\\LTpost}}{{{theme.lt_post}}}
\\setlength{{\\arrayrulewidth}}{{{theme.array_rule_width}}}
\\setlength{{\\extrarowheight}}{{1.0pt}}
\\arrayrulecolor{{OsdagBorder}}
"""


def apply_document_theme(theme: ReportTheme = DEFAULT_THEME) -> Dict[str, Any]:
    """Return dictionary representation of the theme for report builders."""
    return {
        "theme": theme,
        "colors": get_latex_color_definitions(theme),
        "geometry": get_geometry_preamble(theme),
        "table_spacing": get_table_spacing_preamble(theme),
    }
