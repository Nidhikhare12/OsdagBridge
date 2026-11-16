"""LaTeX rendering primitives and layout builders for OsdagBridge."""

from .escape import tex
from .text import status_pass, status_fail, status_warn, note, unit
from .figures import figure, placeholder, figure_or_placeholder, figure_embed
from .document import build_preamble, title_page, toc_section

__all__ = [
    "tex",
    "status_pass",
    "status_fail",
    "status_warn",
    "note",
    "unit",
    "figure",
    "placeholder",
    "figure_or_placeholder",
    "figure_embed",
    "build_preamble",
    "title_page",
    "toc_section",
]
