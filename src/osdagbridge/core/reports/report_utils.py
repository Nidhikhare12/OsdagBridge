from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),          
                    ('_', r'\_\allowbreak{}'),            
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)
    
    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
        
    # 2. Get total number of girders safely
    n_girders = len(girder_entries)
    
    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def _fig_or_placeholder(path, caption, width=r'0.9\textwidth'):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            r'\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}' + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')

def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        return (r'\begin{figure}[H]' + '\n'
                r'\vspace{-0.5em}' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\vspace{0.5em}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    # fbox placeholder — matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')




def repeat_longtable_headers(tex):
    """Add repeatable headers to captioned longtables that have a simple
    caption + rule + column-header row + rule pattern.

    Existing tables with an explicit \\endfirsthead are left unchanged.
    """
    import re

    if not tex:
        return tex
    pieces = tex.split(r"\begin{longtable}")
    if len(pieces) == 1:
        return tex
    output = [pieces[0]]
    for piece in pieces[1:]:
        table_start = r"\begin{longtable}" + piece
        end_pos = table_start.find(r"\end{longtable}")
        if end_pos < 0:
            output.append(table_start)
            continue
        table, remainder = table_start[:end_pos], table_start[end_pos:]
        if r"\endfirsthead" not in table and r"\caption" in table:
            cap = table.find(r"\caption")
            first_rule = table.find(r"\hline", cap)
            second_rule = table.find(r"\hline", first_rule + len(r"\hline")) if first_rule >= 0 else -1
            if first_rule >= 0 and second_rule >= 0:
                header = table[first_rule + len(r"\hline"):second_rule].strip()
                # Only repeat a non-empty header row. Do not alter tables whose
                # first row is actually body text or a multi-line merged section.
                if header and r"\multicolumn" not in header and r"\textbf" in header:
                    insertion = (
                        "\n" + r"\endfirsthead" + "\n"
                        + r"\hline" + "\n" + header + "\n"
                        + r"\hline" + "\n" + r"\endhead" + "\n"
                    )
                    table = table[:second_rule + len(r"\hline")] + insertion + table[second_rule + len(r"\hline"):]
        output.append(table + remainder)
    return "".join(output)


def write_bar_chart(chart_dir, filename, labels, values, title, ylabel,
                    threshold=None, xlabel=None, horizontal=False, brand_color="#91B014"):
    """Write a simple report chart and return its LaTeX-relative asset path.

    Invalid/missing values are omitted. Returns None if plotting dependencies or
    usable data are unavailable, so report generation can continue safely.
    """
    if not chart_dir:
        return None
    try:
        import os
        import math
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        os.makedirs(chart_dir, exist_ok=True)
        pairs = []
        for label, value in zip(labels, values):
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                pairs.append((str(label), number))
        if not pairs:
            return None
        labs, vals = zip(*pairs)
        # Osdag green for passing bars; red only for values above a supplied
        # threshold (e.g. UR > 1.0). Material charts have no threshold and stay green.
        colors = ["#d62728" if threshold is not None and v > float(threshold) else brand_color
                  for v in vals]
        fig, ax = plt.subplots(figsize=(9, 5.2), constrained_layout=True)
        if horizontal:
            ax.barh(list(labs), list(vals), color=colors)
            if threshold is not None:
                ax.axvline(float(threshold), color="red", linestyle="--", linewidth=1.5,
                           label=f"Limit = {threshold:g}")
            ax.set_xlabel(ylabel)
            if xlabel:
                ax.set_ylabel(xlabel)
        else:
            ax.bar(list(labs), list(vals), color=colors)
            if threshold is not None:
                ax.axhline(float(threshold), color="red", linestyle="--", linewidth=1.5,
                           label=f"Limit = {threshold:g}")
            ax.set_ylabel(ylabel)
            if xlabel:
                ax.set_xlabel(xlabel)
            ax.tick_params(axis="x", labelrotation=25)
        ax.set_title(title, color=brand_color, fontweight="bold")
        ax.grid(axis="y" if not horizontal else "x", alpha=0.25)
        if threshold is not None:
            ax.legend()
        out = os.path.join(chart_dir, filename)
        fig.savefig(out, dpi=180, bbox_inches="tight")
        plt.close(fig)
        return "assets/" + filename
    except Exception:
        return None


def write_dual_axis_chart(chart_dir, filename, left_label, left_value,
                          right_label, right_value, title,
                          left_ylabel, right_ylabel):
    """Create a two-axis comparison when the two quantities use different units."""
    if not chart_dir:
        return None
    try:
        import os
        import math
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        def _number(v):
            try:
                n = float(v)
                return n if math.isfinite(n) else None
            except (TypeError, ValueError):
                return None
        left, right = _number(left_value), _number(right_value)
        if left is None and right is None:
            return None
        fig, ax1 = plt.subplots(figsize=(8.5, 4.5), constrained_layout=True)
        if left is not None:
            ax1.bar([left_label], [left], color="#91B014")
            ax1.set_ylabel(left_ylabel)
        ax1.set_title(title, color="#91B014", fontweight="bold")
        ax2 = ax1.twinx()
        if right is not None:
            ax2.plot([right_label], [right], marker="o", linewidth=2, color="#91B014")
            ax2.set_ylabel(right_ylabel)
        out = os.path.join(chart_dir, filename)
        fig.savefig(out, dpi=180, bbox_inches="tight")
        plt.close(fig)
        return "assets/" + filename
    except Exception:
        return None
