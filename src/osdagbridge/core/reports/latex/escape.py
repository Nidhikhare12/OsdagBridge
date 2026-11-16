"""LaTeX text escaping functions."""


def tex(value) -> str:
    """Escape a Python value for safe LaTeX embedding, preserving structural characters.
    
    Normalises non-ASCII glyphs (e.g. '∠ 100 ⅹ 100ⅹ 10') that pdflatex cannot render,
    and escapes standard LaTeX special characters.
    """
    s = str(value) if value is not None else ""
    if not s:
        return ""

    # Normalise non-ASCII glyphs from section designations
    for uni, ascii_ in [("∠", "L"), ("ⅹ", "x"), ("×", "x")]:
        s = s.replace(uni, ascii_)

    s = s.replace("\\", r"\textbackslash{}")
    for ch, esc in [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("_", r"\_\allowbreak{}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\^{}"),
    ]:
        s = s.replace(ch, esc)

    s = s.replace(":", r":\allowbreak{}")
    return s
