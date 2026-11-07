"""Create a synthetic long-table fixture; this is not a bridge design report."""
from pathlib import Path
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.report_generator import preamble

chapter = ch7_quantities({})
marker = r"\end{longtable}"
row = r"S & Synthetic item & -- & -- & -- & -- & -- \\" + "\n" + r"\hline" + "\n"
chapter = chapter.replace(marker, row * 90 + marker)
Path(__file__).with_name("synthetic-longtable.tex").write_text(
    preamble("Synthetic fixture", "", "") + chapter + r"\end{document}", encoding="utf-8"
)
