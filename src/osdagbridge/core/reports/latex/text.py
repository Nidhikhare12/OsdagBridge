"""LaTeX inline text and status formatting components."""

from osdagbridge.core.reports.theme import get_active_theme, Theme


def status_pass(text: str = "PASS", theme: Theme | None = None) -> str:
    """Format a passing check status using the active theme's pass color."""
    t = theme or get_active_theme()
    return rf"\textcolor[HTML]{{{t.palette.status_pass}}}{{\textbf{{{text}}}}}"


def status_fail(text: str = "FAIL", theme: Theme | None = None) -> str:
    """Format a failing check status using the active theme's fail color."""
    t = theme or get_active_theme()
    return rf"\textcolor[HTML]{{{t.palette.status_fail}}}{{\textbf{{{text}}}}}"


def status_warn(text: str = "WARNING", theme: Theme | None = None) -> str:
    """Format a warning check status using the active theme's warning color."""
    t = theme or get_active_theme()
    return rf"\textcolor[HTML]{{{t.palette.status_warn}}}{{\textbf{{{text}}}}}"


def note(text: str, theme: Theme | None = None) -> str:
    """Format a table footnote or explanatory note."""
    t = theme or get_active_theme()
    return rf"{{\footnotesize\itshape {text}}}"


def unit(text: str) -> str:
    """Format engineering units consistently."""
    return rf"\textnormal{{{text}}}"
