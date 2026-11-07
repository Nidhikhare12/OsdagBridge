from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("report_chap7", ROOT / "src/osdagbridge/core/reports/chap7.py")
chapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chapter)


def test_quantity_table_continuation_header_and_group():
    tex = chapter.ch7_quantities({"steel_girders_wt_total": "12.5"})
    first, continuation = tex.split(r"\endfirsthead", 1)
    header, rows = continuation.split(r"\endhead", 1)
    assert r"\textbf{Item Description}" in first
    assert r"\textbf{Item Description}" in header
    assert "12.5" in rows
    assert tex.count(r"\begingroup") == tex.count(r"\endgroup") == 1


def test_girder_summary_has_continuation_header():
    source = (ROOT / "src/osdagbridge/core/reports/chap5.py").read_text(encoding="utf-8")
    table = source.split(r"\caption{\textbf{Girder Design Summary", 1)[1].split(r"\end{longtable}", 1)[0]
    first, continuation = table.split(r"\endfirsthead", 1)
    header, _ = continuation.split(r"\endhead", 1)
    assert r"\textbf{Controlling LC / Combination}" in first
    assert r"\textbf{Controlling LC / Combination}" in header
