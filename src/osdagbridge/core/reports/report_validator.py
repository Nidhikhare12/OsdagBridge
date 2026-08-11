"""Validation utilities for generated OsdagBridge reports."""

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class ReportValidationResult:
    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_tex_structure(tex_path):
    """Validate basic LaTeX structure of a generated report."""

    path = Path(tex_path)

    result = ReportValidationResult(passed=True)

    if not path.exists():
        result.passed = False
        result.errors.append("LaTeX source file does not exist.")
        return result

    content = path.read_text(encoding="utf-8")

    required_pairs = [
        (r"\begin{document}", r"\end{document}"),
        (r"\begin{longtable}", r"\end{longtable}"),
        (r"\begin{figure}", r"\end{figure}"),
    ]

    for start, end in required_pairs:
        if start in content and end not in content:
            result.passed = False
            result.errors.append(
                f"Missing closing LaTeX block: {end}"
            )

    return result


def validate_pdf(pdf_path):
    """Validate generated PDF existence."""

    path = Path(pdf_path)

    result = ReportValidationResult(passed=True)

    if not path.exists():
        result.passed = False
        result.errors.append("PDF file does not exist.")

    return result

def validate_chapters(tex_path, required_chapters=None):
    """Check required report chapters exist in LaTeX source."""

    if required_chapters is None:
        required_chapters = [
            "Chapter 1",
            "Chapter 2",
            "Chapter 3",
            "Chapter 4",
            "Chapter 5",
            "Chapter 6",
            "Chapter 7",
            "Chapter 8",
            "References",
        ]

    path = Path(tex_path)

    result = ReportValidationResult(passed=True)

    if not path.exists():
        result.passed = False
        result.errors.append("LaTeX source file does not exist.")
        return result

    content = path.read_text(encoding="utf-8")

    for chapter in required_chapters:
        if chapter not in content:
            result.passed = False
            result.errors.append(
                f"Missing report section: {chapter}"
            )

    return result
    result = ReportValidationResult(passed=True)

    if not path.exists():
        result.passed = False
        result.errors.append("PDF file does not exist.")
        return result

    if path.stat().st_size == 0:
        result.passed = False
        result.errors.append("PDF file is empty.")

    return result


def validate_report(pdf_path=None, tex_path=None):
    """Run all report validation checks."""

    final = ReportValidationResult(passed=True)

    if pdf_path:
        pdf_result = validate_pdf(pdf_path)
        final.errors.extend(pdf_result.errors)

    if tex_path:
        tex_result = validate_tex_structure(tex_path)
        final.errors.extend(tex_result.errors)

    if final.errors:
        final.passed = False

    return final

