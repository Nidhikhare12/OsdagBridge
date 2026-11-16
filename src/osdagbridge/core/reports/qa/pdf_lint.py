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
            for line in page.lines:
                # Horizontal line: top == bottom or close
                if abs(line["top"] - line["bottom"]) <= 2.0:
                    # In bottom 15% of page
                    if line["top"] > page_height * 0.85:
                        footer_rule_y = line["top"]
                        break

            # If no explicit rule line was drawn, fallback to 45pt from bottom
            threshold_y = (footer_rule_y - tolerance_pt) if footer_rule_y else (page_height - 50.0)

            # Extract words
            footer_tokens = {"osdag", "fossee", "indian", "institute", "of", "technology", "bombay", "|", "page"}
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


def check_header_repeat(pdf_path: str | Path) -> List[PDFViolation]:
    """Verify that multi-page tables repeat headers across page breaks."""
    # Stub for R1 validation; populated during Phase 3
    return []


def summary(pdf_path: str | Path) -> Dict[str, Any]:
    """Return structural summary of the generated PDF."""
    path = Path(pdf_path).resolve()
    with pdfplumber.open(path) as pdf:
        return {
            "page_count": len(pdf.pages),
            "metadata": pdf.metadata,
        }
