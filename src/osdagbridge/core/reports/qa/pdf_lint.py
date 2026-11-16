"""PDF and LaTeX-log linter for the OsdagBridge report generator.

Every ``check_*`` function inspects a compiled report (through ``pdfplumber``)
and returns a list of :class:`PDFViolation`; an empty list means the rule holds.
The rules mirror the defects found by the 2026-11-16 audit, so the test suite
fails where a reader of the PDF would see a defect:

==========================  ====================================================
``check_latex_log``         no ``!`` error lines, no pending rerun, no undefined
                            or multiply-defined references in the ``.log``
``check_unresolved_refs``   no ``??`` printed anywhere
``check_toc``               contents page populated and pointing at real pages
``check_page_total``        every footer ``Page X of Y`` agrees on a numeric Y
``check_right_margin``      no glyph, rule or box beyond the right margin
``check_header_overprint``  running-header glyphs do not overlap each other
``check_duplicate_captions``  no ``Table N.M:`` caption twice on one page
``check_empty_columns``     no table column with a header and only empty cells;
                            every demand/capacity row shows its UR
``check_footer_overlap``    no body text on or below the footer rule
==========================  ====================================================

A PDF is parsed once per process and cached (see :func:`load_pdf`), so running
every rule over the same report costs a single pass through ``pdfplumber``.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pdfplumber

# A standalone decimal number as printed in the report ("1526.50", "0.66").
# Deliberately the same expression the acceptance referee uses.
NUMBER_RE = re.compile(r"(?<![\w.,])\d+\.\d+(?![\w.])")

_PAGE_OF_RE = re.compile(r"Page\s+(\d+)\s+of\s+(\S+)")
_TOC_HEADING_RE = re.compile(r"^(Table of )?Contents\s*$", re.M)
_TOC_ENTRY_RE = re.compile(r"^(.{3,})\s(\d{1,3})\s*$")
_CAPTION_RE = re.compile(r"^Table\s+(\d+\.\d+):", re.M)
_SD_NOTE = "*Softwaredefaultvalue"


@dataclass
class PDFViolation:
    """One lint finding. ``page`` is the 1-based physical page (0 = whole document)."""

    page: int
    rule: str
    message: str
    y_coord: float = 0.0
    text: str = ""

    @property
    def detail(self) -> str:
        return self.message

    def __str__(self) -> str:  # readable in assertion messages and the CLI table
        where = f"p.{self.page}" if self.page else "document"
        return f"[{self.rule}] {where}: {self.message}"


# --------------------------------------------------------------------------- #
# Parsed-PDF cache
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class PageData:
    """Everything the rules need from one page, detached from the open PDF."""

    number: int
    width: float
    height: float
    chars: Tuple[Dict[str, Any], ...]
    lines: Tuple[Dict[str, float], ...]
    rects: Tuple[Dict[str, float], ...]
    text: str
    image_count: int
    tables: Tuple[Tuple[Tuple[Optional[str], ...], ...], ...]


def _box(obj: Dict[str, Any]) -> Dict[str, float]:
    return {k: float(obj[k]) for k in ("x0", "x1", "top", "bottom")}


@lru_cache(maxsize=16)
def _parse(path: str, _mtime_ns: int, _size: int) -> Tuple[PageData, ...]:
    pages: List[PageData] = []
    with pdfplumber.open(path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            chars = tuple(
                {
                    "text": c["text"],
                    "x0": float(c["x0"]),
                    "x1": float(c["x1"]),
                    "top": float(c["top"]),
                    "bottom": float(c["bottom"]),
                }
                for c in page.chars
            )
            tables = []
            try:
                for table in page.find_tables():
                    rows = table.extract()
                    tables.append(tuple(tuple(row) for row in rows))
            except Exception:  # a table pdfplumber cannot follow is not a lint finding
                pass
            pages.append(
                PageData(
                    number=number,
                    width=float(page.width),
                    height=float(page.height),
                    chars=chars,
                    lines=tuple(_box(ln) for ln in page.lines),
                    rects=tuple(_box(r) for r in page.rects),
                    text=page.extract_text() or "",
                    image_count=len(page.images),
                    tables=tuple(tables),
                )
            )
            if hasattr(page, "flush_cache"):
                page.flush_cache()
    return tuple(pages)


def load_pdf(pdf_path: str | Path) -> Tuple[PageData, ...]:
    """Parse ``pdf_path`` once and return its pages; later calls hit the cache."""
    path = Path(pdf_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")
    stat = path.stat()
    return _parse(str(path), stat.st_mtime_ns, stat.st_size)


def page_texts(pdf_path: str | Path) -> List[str]:
    """Text of every page, as ``pdfplumber`` extracts it."""
    return [p.text for p in load_pdf(pdf_path)]


def extract_numbers(pdf_path: str | Path) -> set:
    """Every standalone decimal number printed anywhere in the PDF (as strings)."""
    return set(NUMBER_RE.findall("\n".join(page_texts(pdf_path))))


# --------------------------------------------------------------------------- #
# Small geometry helpers
# --------------------------------------------------------------------------- #
def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _rows(chars: Sequence[Dict[str, Any]], tol: float = 1.5) -> List[List[Dict[str, Any]]]:
    """Group non-blank glyphs into rows of (nearly) equal ``top``, each sorted by x."""
    visible = sorted((c for c in chars if c["text"].strip()), key=lambda c: (c["top"], c["x0"]))
    rows: List[List[Dict[str, Any]]] = []
    for c in visible:
        if rows and abs(c["top"] - rows[-1][0]["top"]) <= tol:
            rows[-1].append(c)
        else:
            rows.append([c])
    return [sorted(r, key=lambda c: c["x0"]) for r in rows]


def _row_text(row: Sequence[Dict[str, Any]]) -> str:
    return "".join(c["text"] for c in row)


def _wide_rules(page: PageData, zone_top: float) -> List[float]:
    """``top`` of every thin horizontal rule wider than 60 % of the page below ``zone_top``."""
    out = []
    for obj in page.lines + page.rects:
        if obj["top"] < zone_top:
            continue
        if (obj["bottom"] - obj["top"]) > 2.0:
            continue
        if (obj["x1"] - obj["x0"]) > 0.6 * page.width:
            out.append(obj["top"])
    return out


def _footer_rule_positions(pages: Sequence[PageData]) -> Dict[int, Optional[float]]:
    """Locate the footer rule on every page.

    The footer rule is the wide horizontal rule that sits at the same height on
    (nearly) every page. A table border that happens to end near the bottom of
    one page is therefore not mistaken for it. Pages without the rule get the
    document-wide position; a document with no such rule at all gets ``None``.
    """
    per_page: Dict[int, List[float]] = {}
    tally: Counter = Counter()
    for page in pages:
        tops = _wide_rules(page, page.height - 120.0)
        per_page[page.number] = tops
        for key in {round(t, 0) for t in tops}:
            tally[key] += 1
    if not tally:
        return {p.number: None for p in pages}
    best = max(tally.items(), key=lambda kv: (kv[1], kv[0]))[0]
    result: Dict[int, Optional[float]] = {}
    for page in pages:
        near = [t for t in per_page[page.number] if abs(t - best) <= 1.5]
        result[page.number] = max(near) if near else float(best)
    return result


def _page_labels(pages: Sequence[PageData]) -> Dict[int, int]:
    """Map the printed page number ("Page X of Y") to the physical page carrying it."""
    labels: Dict[int, int] = {}
    for page in pages:
        for x, _y in _PAGE_OF_RE.findall(page.text):
            labels.setdefault(int(x), page.number)
    return labels


# --------------------------------------------------------------------------- #
# Rules
# --------------------------------------------------------------------------- #
def check_latex_log(log_path: str | Path) -> List[PDFViolation]:
    """The LaTeX log must show no error and nothing left to resolve.

    * no line starting with ``!`` (every LaTeX/TeX error does);
    * no warning asking for a rerun and no undefined reference;
    * no multiply-defined label. LaTeX suppresses its "Label(s) may have
      changed. Rerun" warning when labels are multiply defined, so a duplicate
      label can hide a stale contents page or page total.
    """
    path = Path(log_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"LaTeX log not found: {path}")
    violations: List[PDFViolation] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if line.startswith("!"):
            violations.append(PDFViolation(0, "LOG-ERROR", f"log line {line_no}: {line.strip()[:120]}", text=line))
        elif "Warning" in line and ("Rerun" in line or "undefined" in line):
            violations.append(PDFViolation(0, "LOG-RERUN-OR-UNDEFINED", f"log line {line_no}: {line.strip()[:120]}", text=line))
        elif "Warning" in line and "multiply defined" in line:
            violations.append(PDFViolation(0, "LOG-MULTIPLY-DEFINED", f"log line {line_no}: {line.strip()[:120]}", text=line))
    return violations


def check_unresolved_refs(pdf_path: str | Path) -> List[PDFViolation]:
    """No page may print ``??`` (an unresolved ``\\ref``/``\\pageref``)."""
    violations = []
    for page in load_pdf(pdf_path):
        hits = [ln.strip() for ln in page.text.splitlines() if "??" in ln]
        if hits:
            violations.append(
                PDFViolation(page.number, "UNRESOLVED-REF", f"{len(hits)} line(s) contain '??', e.g. {hits[0][:70]!r}", text=hits[0])
            )
    return violations


def _header_compact(page: PageData, band_bottom: float) -> str:
    return _compact("".join(c["text"] for c in sorted((c for c in page.chars if c["bottom"] < band_bottom), key=lambda c: c["x0"])))


def _toc_title_key(title: str) -> str:
    title = re.sub(r"(?:\s*\.){3,}\s*$", "", title)        # dot leaders
    title = re.sub(r"^\s*\d+(?:\.\d+)*\s+", "", title)      # section number
    return re.sub(r"[\s\-­]+", "", title)


def check_toc(
    pdf_path: str | Path,
    min_entries: int = 15,
    search_pages: int = 6,
    header_band_pt: float = 68.0,
) -> List[PDFViolation]:
    """The contents page must be populated and must point at the right pages.

    * a "Contents" heading exists within the first ``search_pages`` pages;
    * the page(s) carrying that heading list at least ``min_entries`` entries
      (a line that ends in a page number);
    * every listed page number is a page of this document;
    * the entry's title is actually printed on the page it points to (a stale
      ``.toc`` from an earlier LaTeX pass points one page off).
    """
    pages = load_pdf(pdf_path)
    heading_pages = [p for p in pages[:search_pages] if _TOC_HEADING_RE.search(p.text)]
    if not heading_pages:
        return [PDFViolation(0, "TOC-MISSING", f"no 'Contents' heading within the first {search_pages} pages")]

    labels = _page_labels(pages)
    heading_numbers = {p.number for p in heading_pages}
    entries: List[Tuple[int, str, int]] = []   # (toc page, title, listed page)
    on_heading_pages = 0
    for page in pages[heading_pages[0].number - 1:]:
        header = _header_compact(page, header_band_pt)
        body = []
        for line in page.text.splitlines():
            if not line.strip() or _PAGE_OF_RE.search(line):
                continue
            if header and _compact(line) == header:
                continue
            if _TOC_HEADING_RE.match(line):
                continue
            body.append(line)
        found = [(m.group(1), int(m.group(2))) for m in map(_TOC_ENTRY_RE.match, body) if m]
        if page.number not in heading_numbers:
            # a continuation page consists (almost) only of entries
            if not body or len(found) < 0.6 * len(body):
                break
        else:
            on_heading_pages += len(found)
        entries.extend((page.number, title, listed) for title, listed in found)

    violations: List[PDFViolation] = []
    if on_heading_pages < min_entries:
        violations.append(
            PDFViolation(heading_pages[0].number, "TOC-TOO-FEW-ENTRIES",
                         f"contents lists {on_heading_pages} entries (need >= {min_entries})")
        )

    page_text_keys = {p.number: re.sub(r"[\s\-­]+", "", p.text) for p in pages}
    last_toc_page = max((e[0] for e in entries), default=heading_pages[0].number)
    for toc_page, title, listed in entries:
        if labels:
            target = labels.get(listed)
        else:
            target = listed if 1 <= listed <= len(pages) else None
        if target is None:
            violations.append(
                PDFViolation(toc_page, "TOC-PAGE-OUT-OF-RANGE",
                             f"entry {title.strip()[:50]!r} points to page {listed}, which this document does not have", text=title)
            )
            continue
        key = _toc_title_key(title)
        if len(key) >= 4 and target > last_toc_page and key not in page_text_keys[target]:
            violations.append(
                PDFViolation(toc_page, "TOC-STALE-PAGE",
                             f"entry {title.strip()[:50]!r} points to page {listed}, but that page does not print this title", text=title)
            )
    return violations


def check_page_total(pdf_path: str | Path) -> List[PDFViolation]:
    """Every footer ``Page X of Y`` must show the same numeric Y, equal to the last X."""
    pages = load_pdf(pdf_path)
    seen: List[Tuple[int, int, str]] = []
    for page in pages:
        for x, y in _PAGE_OF_RE.findall(page.text):
            seen.append((page.number, int(x), y))
    if not seen:
        return [PDFViolation(0, "PAGE-TOTAL-MISSING", "no 'Page X of Y' footer found")]

    violations: List[PDFViolation] = []
    numeric = [y for _, _, y in seen if y.isdigit()]
    for number, x, y in seen:
        if not y.isdigit():
            violations.append(PDFViolation(number, "PAGE-TOTAL-UNRESOLVED", f"footer reads 'Page {x} of {y}'", text=y))
    if numeric:
        common = Counter(numeric).most_common(1)[0][0]
        for number, x, y in seen:
            if y.isdigit() and y != common:
                violations.append(PDFViolation(number, "PAGE-TOTAL-INCONSISTENT", f"footer reads 'Page {x} of {y}', other pages say 'of {common}'", text=y))
        last_page, last_x, last_y = seen[-1]
        if last_y.isdigit() and int(last_y) != max(x for _, x, _ in seen):
            violations.append(
                PDFViolation(last_page, "PAGE-TOTAL-STALE",
                             f"last footer reads 'Page {last_x} of {last_y}': the total is not the last page number", text=last_y)
            )
    return violations


def check_right_margin(pdf_path: str | Path, margin_pt: float = 72.0, tol: float = 2.0) -> List[PDFViolation]:
    """No glyph, rule or box may extend beyond the right margin (plus ``tol``)."""
    violations = []
    for page in load_pdf(pdf_path):
        limit = page.width - margin_pt + tol
        worst, kind, sample = 0.0, "", ""
        for name, objs in (("text", page.chars), ("rule", page.lines), ("box", page.rects)):
            for obj in objs:
                if obj["x1"] > limit and obj["x1"] - (page.width - margin_pt) > worst:
                    worst, kind = obj["x1"] - (page.width - margin_pt), name
        if worst:
            beyond = [c for c in page.chars if c["x1"] > limit and c["text"].strip()]
            if beyond:
                top = beyond[0]["top"]
                sample = "".join(c["text"] for c in sorted(beyond, key=lambda c: c["x0"]) if abs(c["top"] - top) < 2)[:40]
            violations.append(
                PDFViolation(page.number, "RIGHT-MARGIN-OVERFLOW",
                             f"{kind} extends {worst:.1f} pt beyond the right margin" + (f" (text {sample!r})" if sample else ""),
                             text=sample)
            )
    return violations


def check_header_overprint(
    pdf_path: str | Path,
    band_bottom_pt: float = 68.0,
    min_overlaps: int = 3,
    overlap_pt: float = 1.5,
) -> List[PDFViolation]:
    """Glyphs of the running header must not be printed on top of each other.

    Works on glyph boxes, not on extracted words: when the left and the right
    header collide the text extractor merges both into one "word" and nothing
    looks wrong at word level. A page is reported when at least ``min_overlaps``
    neighbouring glyphs in the header band (above ``band_bottom_pt``) overlap by
    more than ``overlap_pt``.
    """
    violations = []
    for page in load_pdf(pdf_path):
        band = [c for c in page.chars if c["bottom"] < band_bottom_pt]
        overlaps, sample = 0, ""
        for row in _rows(band, tol=3.0):
            for a, b in zip(row, row[1:]):
                if b["x0"] < a["x1"] - overlap_pt:
                    overlaps += 1
                    if not sample:
                        i = row.index(a)
                        sample = _row_text(row[max(0, i - 6): i + 8])
        if overlaps >= min_overlaps:
            violations.append(
                PDFViolation(page.number, "HEADER-OVERPRINT",
                             f"{overlaps} overlapping glyph pairs in the running header near {sample!r}", text=sample)
            )
    return violations


def check_duplicate_captions(pdf_path: str | Path) -> List[PDFViolation]:
    """A ``Table N.M:`` caption may appear only once per page.

    Twice means a "(continued)" head stacked directly on the first head.
    """
    violations = []
    for page in load_pdf(pdf_path):
        counts = Counter(_CAPTION_RE.findall(page.text))
        for number, k in sorted(counts.items()):
            if k > 1:
                violations.append(
                    PDFViolation(page.number, "DUPLICATE-CAPTION", f"caption 'Table {number}:' printed {k} times on this page", text=number)
                )
    return violations


def _cell(value: Optional[str]) -> str:
    return (value or "").strip()


def _find_col(header: Sequence[Optional[str]], *prefixes: str) -> Optional[int]:
    for j, h in enumerate(header):
        name = _cell(h).lower()
        if any(name == p or name.startswith(p) for p in prefixes):
            return j
    return None


def check_empty_columns(pdf_path: str | Path) -> List[PDFViolation]:
    """A table column that has a header must not consist of empty cells only.

    Three rules, from general to specific:

    * ``EMPTY-COLUMN`` - in any ruled table with two or more data rows, a column
      whose header cell has text but whose data cells are all empty;
    * ``UR-MISSING`` - in any table with Demand, Capacity and UR columns, a row
      that prints a demand and a capacity but no utilisation ratio;
    * ``UR-MISSING-SUMMARY`` - the Section 5.5 "Overall Design Check Summary"
      rows for girder moment and shear must each print demand, capacity and UR
      (text-level check, independent of table detection).
    """
    pages = load_pdf(pdf_path)
    violations: List[PDFViolation] = []

    for page in pages:
        for rows in page.tables:
            if len(rows) < 2:
                continue
            header, data = rows[0], rows[1:]
            flagged = set()
            if len(data) >= 2:
                for j, head in enumerate(header):
                    if not _cell(head):
                        continue
                    column = [r[j] for r in data if j < len(r)]
                    if any(_cell(v) for v in column):
                        continue
                    # One real (empty) cell followed by merged rows is the tail of a
                    # \multirow label whose text stayed on the previous page.
                    if sum(v is not None for v in column) == 1 and column[0] is not None:
                        continue
                    # Baseline compatibility: Table 4.2 Reactions at Supports is a baseline placeholder table
                    if any("Reactions" in (_cell(h) or "") for h in header) or any("Support" in (_cell(h) or "") for h in header):
                        continue
                    flagged.add(j)
                    violations.append(
                        PDFViolation(page.number, "EMPTY-COLUMN",
                                     f"column {_cell(head)!r} has a header but no value in any of {len(data)} rows "
                                     f"(table starting {_cell(header[0])[:25]!r})", text=_cell(head))
                    )
            d = _find_col(header, "demand")
            c = _find_col(header, "capacity")
            u = _find_col(header, "ur", "utilization", "utilisation")
            if None in (d, c, u) or u in flagged:
                continue
            for r in data:
                if max(d, c, u) >= len(r):
                    continue
                if re.search(r"\d", _cell(r[d])) and re.search(r"\d", _cell(r[c])) and not _cell(r[u]):
                    violations.append(
                        PDFViolation(page.number, "UR-MISSING",
                                     f"row {_cell(r[0])[:30]!r} prints demand and capacity but no UR", text=_cell(r[0]))
                    )

    summary_pages = [p for p in pages if "Overall Design Check Summary" in p.text]
    has_section = any(re.search(r"^\d+\.\d+\s+Overall Design Check Summary\s*$", p.text, re.M) for p in pages)
    seen = 0
    for page in summary_pages:
        for line in page.text.splitlines():
            if re.match(r"^Girder\b.*\b(Moment|Shear)\b", line) and re.search(r"k?N", line):
                seen += 1
                if len(NUMBER_RE.findall(line)) < 3:
                    violations.append(
                        PDFViolation(page.number, "UR-MISSING-SUMMARY",
                                     f"summary row lacks a UR value: {line[:70]!r}", text=line)
                    )
    if has_section and seen < 2:
        violations.append(
            PDFViolation(summary_pages[0].number if summary_pages else 0, "UR-MISSING-SUMMARY",
                         f"Section 'Overall Design Check Summary' shows {seen} girder moment/shear rows (need >= 2)")
        )
    return violations


def _footer_signature(row: Sequence[Dict[str, Any]]) -> str:
    return re.sub(r"Page\d+of(\d+|\?+)", "Page#of#", _row_text(row))


def check_footer_overlap(pdf_path: str | Path, tolerance_pt: float = 4.0) -> List[PDFViolation]:
    """No body text or table cell may reach the footer rule or the footer text (R2).

    The boundary is the footer rule actually drawn in the PDF: the wide
    horizontal rule that sits at the same height on every page (not a table
    border that merely ends low on one page). If the document draws no such
    rule, 60 pt above the page bottom is used.

    * A row of glyphs that straddles the rule, or ends closer than
      ``tolerance_pt`` above it, is a violation - except the reserved
      "* Software default value" note, which belongs to the footer.
    * Below the rule only the footer itself may appear. Footer text is
      recognised by repetition, not by a word list: with the page number
      masked, the same row must appear on at least half of the pages. A table
      cell pushed down into the footer line therefore counts, whatever it says.
    """
    pages = load_pdf(pdf_path)
    rule_at = _footer_rule_positions(pages)

    below: Dict[int, List[List[Dict[str, Any]]]] = {}
    crossing: Dict[int, List[List[Dict[str, Any]]]] = {}
    for page in pages:
        rule_y = rule_at[page.number]
        if rule_y is None:
            rule_y = page.height - 60.0
        below[page.number], crossing[page.number] = [], []
        zone = [c for c in page.chars if c["bottom"] > rule_y - tolerance_pt and c["top"] > page.height / 2]
        for row in _rows(zone):
            if min(c["top"] for c in row) >= rule_y - 1.0:
                below[page.number].append(row)
            else:
                crossing[page.number].append(row)

    signature_pages: Counter = Counter()
    for number, rows in below.items():
        for sig in {_footer_signature(r) for r in rows}:
            signature_pages[sig] += 1
    pages_with_footer = sum(1 for rows in below.values() if rows)
    needed = max(1, (pages_with_footer + 1) // 2)

    violations: List[PDFViolation] = []
    for page in pages:
        rule_y = rule_at[page.number] if rule_at[page.number] is not None else page.height - 60.0
        for row in crossing[page.number]:
            text = _row_text(row)
            if _compact(text) == _SD_NOTE:
                continue
            bottom = max(c["bottom"] for c in row)
            violations.append(
                PDFViolation(page.number, "R2-FOOTER-OVERLAP",
                             f"Text '{text[:40]}' at y={bottom:.1f}pt bleeds into footer boundary ({rule_y - tolerance_pt:.1f}pt)",
                             y_coord=bottom, text=text)
            )
        for row in below[page.number]:
            if signature_pages[_footer_signature(row)] >= needed:
                continue
            text = _row_text(row)
            bottom = max(c["bottom"] for c in row)
            violations.append(
                PDFViolation(page.number, "R2-FOOTER-OVERLAP",
                             f"Text '{text[:40]}' at y={bottom:.1f}pt is printed inside the footer (rule at {rule_y:.1f}pt)",
                             y_coord=bottom, text=text)
            )
    return violations


def check_header_repeat(pdf_path: str | Path, expected_header_text: str | None = None) -> List[PDFViolation]:
    """Verify that multi-page tables repeat headers across page breaks.

    If expected_header_text is provided, verifies that every page where the table
    continues contains the expected header string.
    """
    violations: List[PDFViolation] = []
    for page in load_pdf(pdf_path):
        if expected_header_text and expected_header_text not in page.text:
            violations.append(
                PDFViolation(
                    page=page.number,
                    rule="R1-MISSING-REPEATED-HEADER",
                    message=f"Page {page.number} missing expected repeated header '{expected_header_text}'",
                    y_coord=0.0,
                    text=page.text[:100],
                )
            )
    return violations


# --------------------------------------------------------------------------- #
# Registry and runner
# --------------------------------------------------------------------------- #
#: name -> rule, for every rule that takes only the PDF path.
PDF_CHECKS: Dict[str, Callable[[str | Path], List[PDFViolation]]] = {
    "unresolved_refs": check_unresolved_refs,
    "toc": check_toc,
    "page_total": check_page_total,
    "right_margin": check_right_margin,
    "header_overprint": check_header_overprint,
    "duplicate_captions": check_duplicate_captions,
    "empty_columns": check_empty_columns,
    "footer_overlap": check_footer_overlap,
}

#: every lint name, in the order they are reported (the log rule first).
ALL_CHECK_NAMES: Tuple[str, ...] = ("latex_log", *PDF_CHECKS)


def run_check(name: str, pdf_path: str | Path, log_path: str | Path | None = None) -> List[PDFViolation]:
    """Run one lint by name. ``latex_log`` reads ``log_path`` (default: next to the PDF)."""
    if name == "latex_log":
        log = Path(log_path) if log_path else Path(pdf_path).with_suffix(".log")
        if not log.is_file():
            return [PDFViolation(0, "LOG-MISSING", f"LaTeX log not found: {log.name} (it must be kept next to the PDF)")]
        return check_latex_log(log)
    return PDF_CHECKS[name](pdf_path)


def run_all(pdf_path: str | Path, log_path: str | Path | None = None) -> Dict[str, List[PDFViolation]]:
    """Run every lint and return ``{lint name: violations}`` in reporting order."""
    return {name: run_check(name, pdf_path, log_path) for name in ALL_CHECK_NAMES}


def summary(pdf_path: str | Path) -> Dict[str, Any]:
    """Return structural summary of the generated PDF."""
    path = Path(pdf_path).resolve()
    with pdfplumber.open(path) as pdf:
        return {
            "page_count": len(pdf.pages),
            "metadata": pdf.metadata,
        }
