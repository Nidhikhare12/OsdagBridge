"""Base chart styling, formatting, and file export helpers."""

from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # Headless non-interactive backend
import matplotlib.pyplot as plt
from typing import Tuple

from osdagbridge.core.reports.theme import get_active_theme, Theme


def setup_figure(
    figsize: Tuple[float, float] | None = None,
    dpi: int | None = None,
    theme: Theme | None = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Create a styled matplotlib Figure and Axes using theme parameters."""
    t = theme or get_active_theme()
    c = t.chart
    
    fig_size = figsize or c.figsize_overall
    fig_dpi = dpi or c.dpi

    plt.style.use("default")
    plt.rcParams.update({
        "font.family": c.font_family,
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.grid": True,
        "grid.alpha": c.grid_alpha,
        "grid.linestyle": ":",
        "figure.autolayout": True,
    })

    fig, ax = plt.subplots(figsize=fig_size, dpi=fig_dpi)
    return fig, ax


def save_chart(fig: plt.Figure, output_path: str | Path, dpi: int | None = None) -> str:
    """Save figure to destination path and close figure to prevent memory leaks."""
    path = Path(output_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    save_dpi = dpi or 200
    fig.savefig(str(path), dpi=save_dpi, bbox_inches="tight")
    plt.close(fig)
    return str(path)
