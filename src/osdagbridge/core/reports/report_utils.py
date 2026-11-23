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


def _clean_number(val):
    """Remove floating-point noise (21.099999999999998 -> 21.1).

    Only numbers with more than 4 decimals are touched; strings that are
    already formatted (e.g. '5575915.69', '2.3444') are returned unchanged.
    """
    if isinstance(val, bool) or val is None:
        return val
    if isinstance(val, (int, float)):
        num = float(val)
    elif isinstance(val, str):
        txt = val.strip()
        try:
            num = float(txt)
        except ValueError:
            return val
        if "." not in txt or len(txt.split(".")[1]) <= 4:
            return val
    else:
        return val
    out = f"{num:.4f}".rstrip("0").rstrip(".")
    return out if out not in ("", "-0") else "0"


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(_clean_number(val)) + unit


def _dim_mm(source_dict, key, unit=" mm"):
    """Girder dimension in mm.

    The designer converts girder dimensions mm -> m before the analysis
    (PlateGirderBridge._convert_girder_dims_mm_to_m), so the input dict holds
    metres at report time.  Values <= 5 can only be metres (no bridge plate is
    thinner than 5 mm, none wider than 5 m) and are converted back to mm.
    """
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    try:
        num = float(val)
    except (TypeError, ValueError):
        return _tex(val) + unit
    if abs(num) <= 5.0:
        num *= 1000.0
    return _tex(_clean_number(round(num, 2))) + unit


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


def _fig_or_placeholder(path, caption, width=None):
    """Figure (or styled placeholder).  Kept for backward compatibility; the
    implementation lives in latex_tables.figure and styles.FIGURE."""
    from osdagbridge.core.reports.latex_tables import figure
    return figure(path, caption, width=width, numbered=False)


def _fig_embed(path, caption, width=None, height=None):
    """Embed a real figure when *path* is given, otherwise a placeholder box."""
    from osdagbridge.core.reports.latex_tables import figure
    return figure(path, caption, width=width, height=height, numbered=False)
