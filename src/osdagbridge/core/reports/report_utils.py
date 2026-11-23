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
            r'\centering\vspace{1em}' + '\n'
            r'\textit{[ Figure unavailable in this report export ]}' + '\n'
            r'\vspace{1em}' + '\n'
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
            r'\centering\vspace{1em}' + '\n'
            r'\textit{[ Figure unavailable in this report export ]}' + '\n'
            r'\vspace{1em}' + '\n'
            r'}}')


def make_longtable_header(col_spec: str, caption: str, header_row: str,
                          label: str = "", num_cols: int = None,
                          continued_header: str = None,
                          continued_footer: str = None) -> str:
    """Generate professional longtable opening, caption, firsthead, repeated head, and footers.

    Ensures compliance with multi-page table requirements:
      - \\caption and initial column header on first page (\\endfirsthead)
      - Repeated column header with continued notice on subsequent pages (\\endhead)
      - \\multicolumn continued notice at bottom of intermediate pages (\\endfoot)
      - Clean \\hline closing at end of final page (\\endlastfoot)
    """
    from osdagbridge.core.reports.styles import (
        CONTINUED_FROM_PREV_PAGE,
        CONTINUED_ON_NEXT_PAGE,
    )
    if num_cols is None:
        first_row = header_row.strip().split(r"\\")[0]
        num_cols = first_row.count("&") + 1

    lbl_clause = f"\\label{{{label}}}" if label else ""
    cont_head = continued_header or CONTINUED_FROM_PREV_PAGE
    cont_foot = continued_footer or CONTINUED_ON_NEXT_PAGE

    clean_hrow = header_row.strip()
    if not clean_hrow.endswith(r"\\") and not clean_hrow.endswith("]"):
        clean_hrow += r" \\[4pt]"

    return (
        rf"\begin{{longtable}}{{{col_spec}}}" + "\n"
        rf"\caption{{{caption}}}{lbl_clause}\\" + "\n"
        r"\hline" + "\n"
        rf"{clean_hrow}" + "\n"
        r"\hline" + "\n"
        r"\endfirsthead" + "\n\n"
        rf"\multicolumn{{{num_cols}}}{{c}}{{\small\textit{{{cont_head}}}}} \\[4pt]" + "\n"
        r"\hline" + "\n"
        rf"{clean_hrow}" + "\n"
        r"\hline" + "\n"
        r"\endhead" + "\n\n"
        r"\hline" + "\n"
        rf"\multicolumn{{{num_cols}}}{{r@{{}}}}{{\footnotesize\textit{{{cont_foot}}}}} \\" + "\n"
        r"\endfoot" + "\n\n"
        r"\hline" + "\n"
        r"\endlastfoot" + "\n"
    )
