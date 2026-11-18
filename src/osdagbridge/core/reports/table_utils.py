import re

_LONGTABLE = re.compile(r"\\begin\{longtable\}.*?\\end\{longtable\}", re.S)

_HEADER = re.compile(
    r"(?P<pre>[ \t]*\\hline[ \t]*\n)"
    r"(?P<row>[^\n]*\\textbf\{[^\n]*\\\\(?:\[[^\]]*\])?[ \t]*)\n"
    r"(?P<post>[ \t]*\\hline[ \t]*\n)"
)
_HEAD_BLOCK = re.compile(r"\\endfirsthead(.*?)\\endhead[ \t]*\n?", re.S)
_CAPTION = re.compile(r"\\caption\{\\textbf\{(.*?)\}\}[ \t]*(?:\\\\)?[ \t]*\n")
_LEADING_HLINE = re.compile(r"^[ \t]*\\hline[ \t]*\n")

# Tables whose generated LaTeX has no header row: caption -> header row to add
FALLBACK_HEADERS = {
    "Stiffener Design Summary":
        r"\textbf{Girder} & \textbf{Parameter} & \textbf{Value} \\[6pt]",
    "Deck Slab --- Loading and Geometry":
        r"\textbf{Parameter} & \textbf{Value} \\[6pt]",
}


def _nth_newline(text, n):
    idx = -1
    for _ in range(n):
        idx = text.find("\n", idx + 1)
        if idx == -1:
            return len(text)
    return idx


def _build_head(pre, row, post):
    return "\\endfirsthead\n" + pre + row + "\n" + post + "\\endhead\n"


def _fallback(block):
    cap = _CAPTION.search(block)
    if not cap:
        return block
    row = FALLBACK_HEADERS.get(cap.group(1).strip())
    if not row:
        return block
    head = "\\hline\n" + row + "\n\\hline\n" + _build_head("\\hline\n", row, "\\hline\n")
    rest = _LEADING_HLINE.sub("", block[cap.end():], count=1)
    return block[:cap.end()] + head + rest


def _fix_table(block):
    seg = _HEAD_BLOCK.search(block)
    if seg:
        if "&" in seg.group(1):
            return block
        block = block[:seg.start()] + block[seg.end():]

    m = _HEADER.search(block)
    if m and m.start() <= _nth_newline(block, 6):
        insert = _build_head(m.group("pre"), m.group("row"), m.group("post"))
        return block[:m.end()] + insert + block[m.end():]

    return _fallback(block)


def add_repeating_headers(tex):
    return _LONGTABLE.sub(lambda m: _fix_table(m.group(0)), tex)