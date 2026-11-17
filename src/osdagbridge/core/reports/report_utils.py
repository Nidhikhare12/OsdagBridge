import re
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


def _render_value(source_dict, key, unit="", nd=None):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    if nd is not None:
        try:
            val = f"{float(val):.{nd}f}"
        except (TypeError, ValueError):
            pass
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

def make_longtable(colspec, caption, header, body, header_gap="6pt"):
    r"""Build a LaTeX longtable whose header row repeats on every page.

    colspec     column spec, e.g. r"|C{4.0cm}|p{11.5cm}|"
    caption     caption text (the helper wraps it in \textbf{})
    header      header row WITHOUT the trailing \\, e.g.
                r"\textbf{ID} & \textbf{Load Cases}"
    body        table body rows. Each row ends with \\ and its own \hline,
                exactly as the chapter code already writes them.
    header_gap  extra space under the header row
    """
    head = (
        "\\hline\n"
        + header + " \\\\[" + header_gap + "]\n"
        + "\\hline\n"
    )
    # The table's closing rule goes into \endlastfoot so LaTeX can never
    # push it alone onto a new page (the "lone header bar").
    body = body.rstrip()
    closing = ""
    if body.endswith("\\hline"):
        body = body[: -len("\\hline")].rstrip()
        closing = "\\hline\n\\endlastfoot\n\n"
    return (
        "\\begin{longtable}{" + colspec + "}\n"
        + "\\caption{\\textbf{" + caption + "}}\\\\\n"
        + head
        + "\\endfirsthead\n\n"
        + head
        + "\\endhead\n\n"
        + closing
        + body + "\n"
        + "\\end{longtable}\n"
    )
_BEGIN = "\\begin{longtable}"
_END = "\\end{longtable}"
_ROW_END = re.compile(r"\\\\(\[[^\]]*\])?\s*$")

def add_repeating_headers(tex):
    r"""Make every longtable repeat its column-header row on each page.

    Safety net for the legacy tables written as raw LaTeX strings in the
    chapter files. A table is changed only when it has the standard shape

        \begin{longtable}{...}
        \caption{...}
        \hline
        <ONE header row ending in \\ or \\[6pt]>
        \hline
        <body rows>

    and no working \endhead. Tables that already repeat their header, and
    tables with any other shape (e.g. multi-row headers), are left untouched.
    """
    out = []
    pos = 0
    while True:
        start = tex.find(_BEGIN, pos)
        if start == -1:
            out.append(tex[pos:])
            break
        end = tex.find(_END, start)
        if end == -1:
            out.append(tex[pos:])
            break
        end += len(_END)
        out.append(tex[pos:start])
        out.append(_fix_one(tex[start:end]))
        pos = end
    return "".join(out)


def _add_header(block):
    lines = block.split("\n")
    # lines[0] = \begin{longtable}{spec}   lines[1] = \caption{...}
    if len(lines) < 6 or not lines[1].startswith("\\caption{"):
        return block
    if lines[2].strip() != "\\hline" or lines[4].strip() != "\\hline":
        return block
    header = lines[3].rstrip()
    if not _ROW_END.search(header) or "\\cline" in header or '"""' in header:
        return block
    # A real header row has bold text in every cell; a data row does not.
    cells = _ROW_END.sub("", header).split("&")
    if not all("\\textbf" in c for c in cells):
        return block

    caption = lines[1].rstrip()
    if not caption.endswith("\\\\"):
        caption += "\\\\"
    head = ["\\hline", header, "\\hline"]
    rest = lines[5:]

    # Case 1: no head markers at all -> add both.
    if not any(l.strip() in ("\\endfirsthead", "\\endhead") for l in rest):
        new = [lines[0], caption] + head + ["\\endfirsthead", ""] + head + ["\\endhead"] + rest
        return "\n".join(new)

    # Case 2: empty "\endfirsthead \endhead" pair -> fill the empty \endhead.
    idx = [i for i, l in enumerate(rest) if l.strip() == "\\endfirsthead"]
    if idx and idx[0] + 1 < len(rest) and rest[idx[0] + 1].strip() == "\\endhead":
        i = idx[0]
        new_rest = rest[: i + 1] + [""] + head + ["\\endhead"] + rest[i + 2:]
        return "\n".join([lines[0], lines[1], *lines[2:5], *new_rest])

    return block

def _pin_closing_rule(block):
    r"""Move a table's final \hline into \endlastfoot so LaTeX cannot push
    it alone onto a new page (the lone header bar)."""
    if "\\endlastfoot" in block or "\\endhead" not in block:
        return block
    lines = block.rstrip().split("\n")
    if lines[-1].strip() != "\\end{longtable}":
        return block
    j = len(lines) - 2
    while j >= 0 and not lines[j].strip():
        j -= 1
    if j < 0 or lines[j].strip() != "\\hline":
        return block
    del lines[j]
    k = next(i for i, l in enumerate(lines) if l.strip() == "\\endhead")
    lines[k + 1:k + 1] = ["\\hline", "\\endlastfoot"]
    return "\n".join(lines)


def _fix_one(block):
    return _pin_closing_rule(_add_header(block))



