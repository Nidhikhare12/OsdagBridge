"""LaTeX Source & Output Linter for OsdagBridge Report Generator."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class LintViolation:
    file: str
    line: int
    rule: str
    message: str
    context: str


def check_sources(reports_dir: str | Path, allowlist: set | None = None) -> List[LintViolation]:
    """Scan Python chapter files for prohibited hardcoded formatting and raw LaTeX tables.
    
    Rules checked:
    - R-NO-RAW-LONGTABLE: Chapters must not contain raw '\\begin{longtable}' (use ReportTable).
    - R-NO-RAW-DEFINECOLOR: Colors must not be hardcoded via '\\definecolor' (use Theme).
    - R-NO-RAW-TEXTCOLOR: Custom inline colors '\\textcolor{red}' prohibited (use Theme/status).
    - R-NO-RAW-VSPACE: Arbitrary '\\vspace{' calls prohibited.
    - R-NO-RAW-DIMENSIONS: Hardcoded column lengths 'L{...cm}' prohibited (use ColumnPresets).
    """
    reports_p = Path(reports_dir).resolve()
    violations: List[LintViolation] = []
    allow = allowlist or set()

    target_files = [
        "executive_summary.py", "chap1.py", "chap2.py", "chap3.py",
        "chap4.py", "chap5.py", "chap6.py", "chap7.py", "chap8.py", "chap9.py"
    ]

    rules = [
        ("R-NO-RAW-LONGTABLE", r"\\begin\{longtable\}", "Direct \\begin{longtable} found; migrate to ReportTable"),
        ("R-NO-RAW-DEFINECOLOR", r"\\definecolor", "Direct \\definecolor found; define in theme.Palette"),
        ("R-NO-RAW-TEXTCOLOR", r"\\textcolor\{red\}", "Hardcoded \\textcolor{red}; use theme status styling"),
        ("R-NO-RAW-VSPACE", r"\\vspace\{", "Direct \\vspace{...} found; configure via TableTheme or PageTheme"),
        ("R-NO-RAW-DIMENSIONS", r"[LCR]\{\d+(\.\d+)?(cm|pt)\}", "Hardcoded column width found; use theme.ColumnPresets"),
    ]

    for fname in target_files:
        fpath = reports_p / fname
        if not fpath.is_file():
            continue

        with open(fpath, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                clean_line = line.strip()
                if clean_line.startswith("#"):
                    continue

                for rule_id, pattern, msg in rules:
                    if re.search(pattern, line):
                        key = (fname, line_no, rule_id)
                        if key not in allow:
                            violations.append(
                                LintViolation(
                                    file=fname,
                                    line=line_no,
                                    rule=rule_id,
                                    message=msg,
                                    context=clean_line,
                                )
                            )

    return violations


def check_tex(tex_path: str | Path) -> List[LintViolation]:
    """Scan compiled .tex document to ensure all tables meet R1 requirements."""
    path = Path(tex_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"LaTeX file not found: {path}")

    violations: List[LintViolation] = []
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find each longtable block and verify \endfirsthead and \endhead exist
    table_pattern = re.compile(r"(\\begin\{longtable\}.*?\\end\{longtable\})", re.DOTALL)
    tables = list(table_pattern.finditer(content))

    for idx, match in enumerate(tables, start=1):
        tbl_text = match.group(1)
        line_no = content[:match.start()].count("\n") + 1

        if "\\endfirsthead" not in tbl_text:
            violations.append(
                LintViolation(
                    file=path.name,
                    line=line_no,
                    rule="R1-NO-ENDFIRSTHEAD",
                    message=f"Table #{idx} lacks \\endfirsthead repeated header directive",
                    context=tbl_text.splitlines()[0],
                )
            )

        if "\\endhead" not in tbl_text:
            violations.append(
                LintViolation(
                    file=path.name,
                    line=line_no,
                    rule="R1-NO-ENDHEAD",
                    message=f"Table #{idx} lacks \\endhead continuation header directive",
                    context=tbl_text.splitlines()[0],
                )
            )

    return violations
