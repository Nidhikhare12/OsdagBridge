"""Add repeating headers (\\endfirsthead / \\endhead) to every longtable
whose first row is a plain \\textbf header row."""
import re


def _skip_ws(s, i):
    while i < len(s) and s[i] in " \t\r\n":
        i += 1
    return i


def _group_end(s, i):
    """s[i] == '{' (or '['); return index just after the matching close."""
    op, cl = s[i], {"{": "}", "[": "]"}[s[i]]
    d, k = 0, i
    while k < len(s):
        c = s[k]
        if c == "\\":
            k += 2
            continue
        if c == op:
            d += 1
        elif c == cl:
            d -= 1
            if d == 0:
                return k + 1
        k += 1
    return -1


def _row_end(s, i):
    """Index just after the first depth-0 row terminator (\\\\ and optional [..])."""
    d, k = 0, i
    while k < len(s):
        c = s[k]
        if c == "\\":
            if s[k + 1:k + 2] == "\\" and d == 0:
                k += 2
                j = _skip_ws(s, k)
                if s[j:j + 1] == "[":
                    e = _group_end(s, j)
                    if e > 0:
                        k = e
                return k
            k += 2
            continue
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
        k += 1
    return -1


def _fix_block(b):
    """b = text between \\begin{longtable} and \\end{longtable}. Returns (new, reason)."""
    if r"\endhead" in b or r"\endfirsthead" in b:
        return None, "already has header"
    p = _skip_ws(b, 0)
    if b[p:p + 1] == "[":
        p = _group_end(b, _skip_ws(b, _group_end(b, p)) if False else p)
        p = _skip_ws(b, p)
    if b[p:p + 1] != "{":
        return None, "spec not found"
    p = _group_end(b, p)
    p = _skip_ws(b, p)
    if b.startswith(r"\caption", p):
        q = p + len(r"\caption")
        if b[q:q + 1] == "*":
            q += 1
        if b[q:q + 1] == "[":
            q = _group_end(b, q)
        q = _skip_ws(b, q)
        if b[q:q + 1] != "{":
            return None, "caption not parsed"
        p = _skip_ws(b, _group_end(b, q))
        if b.startswith("\\\\", p):
            p += 2
            p = _skip_ws(b, p)
    if b.startswith(r"\label", p):
        p = _skip_ws(b, _group_end(b, p + len(r"\label")))
    if not b.startswith(r"\hline", p):
        return None, "no \\hline before first row"
    p = _skip_ws(b, p + len(r"\hline"))
    e = _row_end(b, p)
    if e < 0:
        return None, "header row not parsed"
    header = b[p:e]
    if r"\textbf" not in header or r"\multirow" in header or r"\multicolumn" in header:
        return None, "first row is not a plain header"
    e2 = _skip_ws(b, e)
    if b.startswith(r"\hline", e2):
        e = e2 + len(r"\hline")
    first = b[:e] + "\n"
    cont = "\\endfirsthead\n\\hline\n" + header.strip() + "\n\\hline\n\\endhead\n"
    return first.rstrip("\n") + "\n" + cont + b[e:], "fixed"


def add_repeating_headers(tex, report=None):
    out, pos = [], 0
    tag, endtag = r"\begin{longtable}", r"\end{longtable}"
    while True:
        i = tex.find(tag, pos)
        if i < 0:
            break
        j = tex.find(endtag, i)
        if j < 0:
            break
        body_start = i + len(tag)
        new, why = _fix_block(tex[body_start:j])
        out.append(tex[pos:body_start])
        out.append(new if new is not None else tex[body_start:j])
        if report is not None:
            report.append((tex.count("\n", 0, i) + 1, why))
        pos = j
    out.append(tex[pos:])
    return "".join(out)
