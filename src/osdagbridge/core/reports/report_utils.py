from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


# Human-readable mapping for internal check names and code identifiers
CHECK_NAME_MAP = {
    "Int.Stiff: Leg ≤ H_limit": "Intermediate Stiffener Outstand Limit",
    "Int.Stiff: Leg <= H_limit": "Intermediate Stiffener Outstand Limit",
    "Int.Stiff: Leg <= H limit": "Intermediate Stiffener Outstand Limit",
    "Bearing.Stiff: Outstand limit": "Bearing Stiffener Outstand Limit",
    "Web: d/tw limit": r"Web Slenderness Limit ($d/t_w$)",
    "Flange: b/tf limit": r"Flange Slenderness Limit ($b/t_f$)",
    "Flexure": "Girder Flexural Resistance",
    "Shear": "Girder Shear Capacity",
    "Shear Buckling": "Web Shear Buckling Resistance",
    "Combined M-V": "Bending and Shear Interaction",
    "Deflection Live": "Live Load Deflection Limit",
    "Deflection Total": "Total Deflection Limit",
    "Punching Shear": "Deck Slab Punching Shear",
    "Transverse Flexure": "Deck Slab Transverse Flexure",
}


def format_check_name(name: str) -> str:
    """Map internal check IDs or raw expressions to clean, professional engineering labels."""
    if not name:
        return "-"
    s = str(name).strip()
    if s in CHECK_NAME_MAP:
        return CHECK_NAME_MAP[s]
    # General cleanup of internal coder tags
    s = s.replace("Int.Stiff:", "Intermediate Stiffener: ")
    s = s.replace("Bearing.Stiff:", "Bearing Stiffener: ")
    s = s.replace("_", " ")
    return _tex(s)


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "∠ 100 ⅹ 100ⅹ 10")
    # and design check names (e.g. "Leg ≤ H_limit") that pdflatex cannot render.
    for uni, ascii_ in [('∠', 'L'), ('ⅹ', 'x'), ('×', 'x'), ('\u2014', '-'), ('\u2013', '-')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),          
                    ('_', r'\_\allowbreak{}'),            
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    s = s.replace('≤', r'$\le$').replace('≥', r'$\ge$')
    s = s.replace('>', r'$>$').replace('<', r'$<$')
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
    try:
        n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 4) or 4)
    except (ValueError, TypeError):
        n = 4

    entries = []
    for i in range(1, n + 1):
        g_lbl = input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}")
        if not g_lbl or str(g_lbl).strip() == "":
            g_lbl = f"G{i}"
        m_id = input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1")
        if not m_id or str(m_id).strip() == "":
            m_id = f"G{i}M1"
        entries.append((str(g_lbl).strip(), str(m_id).strip()))

    return entries


def _fig_or_placeholder(path, caption, width=r'0.9\textwidth'):
    """Embed figure if path is provided (file already copied to assets); omit cleanly if not available."""
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption{\small ' + caption + '}\n'
                r'\end{figure}')
    return ""


def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided; omit cleanly if not available."""
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
                r'\caption{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    return ""


