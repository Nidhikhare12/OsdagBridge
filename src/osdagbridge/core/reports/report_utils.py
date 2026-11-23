# =============================================================================
# Report Utilities
# Compatibility layer for existing report chapters.
# LaTeX formatting is centralized in report_formatting.py.
# =============================================================================

import os

from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_TS_NO_OF_GIRDERS,
)

from osdagbridge.core.reports.report_formatting import (
    escape_latex,
    render_value,
    format_table_caption,
    format_table_cell,
    standard_table_start,
    standard_table_end,
    format_table_row,
)


def _tex(value):
    """Backward-compatible plain-text to LaTeX escaping function."""
    return escape_latex(value)


def _render_value(source_dict, key, unit=""):
    """Backward-compatible dictionary value renderer."""
    return render_value(source_dict, key, unit)


def get_girder_entries(input_dict):
    """Return (girder label, member ID) pairs using canonical backend keys."""
    input_dict = input_dict or {}
    try:
        count = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0) or 0)
    except (TypeError, ValueError):
        count = 0

    entries = []
    for index in range(1, count + 1):
        entries.append((
            input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{index}", f"G{index}"),
            input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{index}.M1", f"G{index}M1"),
        ))
    return entries


def _figure_note(caption):
    safe_caption = format_table_caption(caption)
    return (
        r"\par\smallskip\noindent"
        + r"\textit{Figure not available: " + safe_caption + r"}"
        + "\n"
    )


def _fig_or_placeholder(path, caption, width=r"0.9\textwidth"):
    """Embed an existing image, otherwise show a compact non-overflowing note."""
    if path and os.path.isfile(os.fspath(path)):
        image_path = os.fspath(path).replace("\\", "/")
        safe_caption = format_table_caption(caption)
        return (
            r"\begin{figure}[H]" + "\n"
            + r"\centering" + "\n"
            + r"\includegraphics[width=" + width + r"]{\detokenize{" + image_path + "}}\n"
            + r"\caption*{" + safe_caption + "}" + "\n"
            + r"\end{figure}" + "\n"
        )
    # Do not fill the report with repeated placeholder sentences. Missing
    # figure assets are summarized once in their owning chapter.
    return ""


def _fig_embed(path, caption, width=r"\textwidth", height=None):
    """Embed an existing image or a compact note; never emit a broken image path."""
    if path and os.path.isfile(os.fspath(path)):
        image_path = os.fspath(path).replace("\\", "/")
        options = "width=" + width
        if height:
            options += ",height=" + height + ",keepaspectratio"
        safe_caption = format_table_caption(caption)
        return (
            r"\begin{figure}[H]" + "\n"
            + r"\centering" + "\n"
            + r"\includegraphics[" + options + r"]{\detokenize{" + image_path + "}}\n"
            + r"\caption*{\small " + safe_caption + "}" + "\n"
            + r"\end{figure}" + "\n"
        )
    return ""
