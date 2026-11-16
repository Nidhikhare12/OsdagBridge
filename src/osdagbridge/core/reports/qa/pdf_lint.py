"""PDF QA Linter for OsdagBridge Report Generator using pdfplumber."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import pdfplumber


@dataclass
class PDFViolation:
    page: int
    rule: str
    message: str
    y_coord: float
    text: str


def check_footer_overlap(pdf_path: str | Path, tolerance_pt: float = 4.0) -> List[PDFViolation]:
    """Scan every page in the PDF to verify that no body text bleeds into the footer zone.
    
    Rule R2: No body text or table cell should overlap with the footer rule or footer text.
    """
    path = Path(pdf_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    violations: List[PDFViolation] = []

    with pdfplumber.open(path) as pdf:
        for p_idx, page in enumerate(pdf.pages, start=1):
            page_height = float(page.height)

            # Find horizontal lines that could be the footer rule (typically green, within bottom 100 pt)
            footer_rule_y = None
            rules = [
                l["top"]
                for l in page.lines
                if abs(l["top"] - l["bottom"]) <= 2.0 and l["top"] > (page_height - 100.0)
            ]
            if rules:
                footer_rule_y = max(rules)

            # If no explicit rule line was drawn, fallback to 45pt from bottom
            threshold_y = (footer_rule_y - tolerance_pt) if footer_rule_y else (page_height - 50.0)

            # Extract words
            footer_tokens = {
                "osdag", "fossee", "indian", "institute", "of", "technology", "bombay",
                "|", "page", "*", "software", "default", "value"
            }
            words = page.extract_words()
            for w in words:
                text = w["text"].strip()
                bottom = float(w["bottom"])

                # Skip standard footer elements and page numbers
                clean = text.lower()
                if clean in footer_tokens or clean.isdigit():
                    continue

                if bottom > threshold_y:
                    violations.append(
                        PDFViolation(
                            page=p_idx,
                            rule="R2-FOOTER-OVERLAP",
                            message=f"Text '{text}' at y={bottom:.1f}pt bleeds into footer boundary ({threshold_y:.1f}pt)",
                            y_coord=bottom,
                            text=text,
                        )
                    )

    return violations


def check_header_repeat(pdf_path: str | Path, expected_header_text: str | None = None) -> List[PDFViolation]:
    """Verify that multi-page tables repeat headers across page breaks.
    
    If expected_header_text is provided, verifies that every page where the table
    continues contains the expected header string.
    """
    path = Path(pdf_path).resolve()
    violations: List[PDFViolation] = []

    with pdfplumber.open(path) as pdf:
        for p_idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if expected_header_text and expected_header_text not in text:
                violations.append(
                    PDFViolation(
                        page=p_idx,
                        rule="R1-MISSING-REPEATED-HEADER",
                        message=f"Page {p_idx} missing expected repeated header '{expected_header_text}'",
                        y_coord=0.0,
                        text=text[:100],
                    )
                )

    return violations


def summary(pdf_path: str | Path) -> Dict[str, Any]:
    """Return structural summary of the generated PDF."""
    path = Path(pdf_path).resolve()
    with pdfplumber.open(path) as pdf:
        return {
            "page_count": len(pdf.pages),
            "metadata": pdf.metadata,
        }
