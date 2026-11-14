"""
Centralized Styling and Color Palette for OsdagBridge LaTeX Reports.

Single source of truth for all visual parameters, brand colors, table formatting,
and LaTeX preamble style injections.
"""

from typing import List, Optional

# Canonical Color Palette
COLOR_OSDAG_GREEN = "#91B014"   # Canonical Osdag brand green
COLOR_HEADER_NAVY = "#1E3A8A"   # Deep Navy for table headers
COLOR_ZEBRA_LIGHT = "#F3F4F6"   # Light subtle grey for alternating table rows
COLOR_PASS        = "#10B981"   # Emerald green for passing design checks
COLOR_FAIL        = "#EF4444"   # Bright red for failing/overstressed checks

# LaTeX Preamble Color Definitions
LATEX_COLOR_DEFINITIONS = r"""
\definecolor{osdagGreen}{HTML}{91B014}
\definecolor{headerNavy}{HTML}{1E3A8A}
\definecolor{zebraLight}{HTML}{F3F4F6}
\definecolor{passGreen}{HTML}{10B981}
\definecolor{failRed}{HTML}{EF4444}
"""

# Table formatting specifications
ARRAY_STRETCH = 1.15
TABLE_HEADER_FORMAT = r"\rowcolor{headerNavy}\color{white}\bfseries "
ZEBRA_ROW_FORMAT = r"\rowcolor{zebraLight} "


def get_preamble_styles() -> str:
    """Return LaTeX macro and color definitions to inject into the document preamble."""
    return LATEX_COLOR_DEFINITIONS


def pass_indicator(text: str = "PASS") -> str:
    """Return LaTeX string for a green pass indicator."""
    return rf"\textcolor{{passGreen}}{{\textbf{{{text}}}}}"


def fail_indicator(text: str = "FAIL") -> str:
    """Return LaTeX string for a red fail indicator."""
    return rf"\textcolor{{failRed}}{{\textbf{{{text}}}}}"


def status_indicator(passed: bool, pass_text: str = "PASS", fail_text: str = "FAIL") -> str:
    """Return LaTeX pass/fail indicator based on boolean status."""
    return pass_indicator(pass_text) if passed else fail_indicator(fail_text)
