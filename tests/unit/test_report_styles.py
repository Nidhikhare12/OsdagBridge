"""Regression checks for report formatting and chart output.

Run with: python -m unittest discover -s tests/unit -p test_report_styles.py
"""
import importlib.util
from pathlib import Path
import unittest

REPORTS = Path(__file__).resolve().parents[2] / "src/osdagbridge/core/reports"
spec = importlib.util.spec_from_file_location("report_styles", REPORTS / "styles.py")
styles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(styles)


class ReportStyleTests(unittest.TestCase):
    def test_repeated_header_is_identical_on_both_pages(self):
        header = r"Name & Value \\" + "\n" + r"\hline"
        self.assertEqual(styles.repeated_header(header),
                         header + "\n\\endfirsthead\n" + header + "\n\\endhead")

    def test_failure_is_red_and_unknown_is_not_a_pass(self):
        self.assertEqual(styles.status(False), r"\textcolor{red}{FAIL}")
        self.assertEqual(styles.status_or_dash(None), "---")
        self.assertEqual(styles.ur_markup(1.0), "1.00")
        self.assertEqual(styles.ur_markup(1.01), r"\textcolor{red}{1.01}")

    def test_nonbreaking_rule_protects_negative_skip(self):
        self.assertIn(r"\noalign{\penalty\@M\vskip-\arrayrulewidth}",
                      styles.PREAMBLE_NBCLINE)
        chapter = (REPORTS / "chap5.py").read_text()
        self.assertEqual(chapter.count(r"\nbcline{"), 46)
        self.assertEqual(chapter.count(r"\\*[6pt]"), 46)
        self.assertNotIn(r"\nopagebreak", chapter)

    def test_theme_includes_layout_and_metadata(self):
        preamble = styles.document_preamble("Project", "Job", "Date", "Rev")
        self.assertIn("Project $|$ Job", preamble)
        self.assertIn(styles.PREAMBLE_NBCLINE, preamble)
        self.assertIn(styles.COLOR_DEF_BRAND, preamble)
        self.assertIn(styles.PREAMBLE_CAPTIONS, preamble)
        self.assertIn(styles.PREAMBLE_TABLE_LAYOUT, preamble)
        self.assertIn(r"\usepackage[a4paper, margin=1in]{geometry}", preamble)

    def test_all_headered_chapter_longtables_have_repeat_markers(self):
        total = 0
        for chapter in REPORTS.glob("chap*.py"):
            text = chapter.read_text()
            self.assertEqual(text.count(r"\endfirsthead"),
                             text.count(r"\endhead"), chapter.name)
            total += text.count(r"\endhead")
        self.assertEqual(total, 49)  # Includes mutually exclusive table variants.


if __name__ == "__main__":
    unittest.main()
