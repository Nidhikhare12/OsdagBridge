import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from osdagbridge.core.reports import report_generator as report
from osdagbridge.core.reports import styles


def test_preamble_consumes_shared_styles(monkeypatch):
    monkeypatch.setattr(report, "PAGE_MARGIN", "23mm")
    tex = report.preamble("Project", "Job", "Date")
    assert r"margin=23mm" in tex
    assert styles.BRAND_GREEN in tex


def test_payload_figures_survive_two_generations(monkeypatch, tmp_path):
    metadata = report.ReportMetadata("Project", "", "", "", "")
    options = report.ReportOptions([], False, False, True)
    payload = report.ReportPayload(metadata, options, {}, {}, [], report.ReportFigures(),
                                   figure_data={"plan": b"controlled fixture"})
    request = report.ReportRequest(metadata, options, str(tmp_path), "test")
    monkeypatch.setattr(report, "calculate_material_quantities", lambda *_: {})
    for name in ("preamble", "title_page", "ch1_project_info",
                 "ch2_input_parameters", "ch7_quantities", "ch8_design_log", "references"):
        monkeypatch.setattr(report, name, lambda *args: "")
    monkeypatch.setattr(report, "executive_summary", lambda inputs, outputs, figures: figures["plan"])
    observed = []

    def compile_stub(command, **kwargs):
        images = Path(kwargs["cwd"]) / "images"
        observed.append((images / "plan.png").read_bytes())
        (Path(kwargs["cwd"]) / "test.pdf").write_bytes(b"controlled compiler fixture")
        return SimpleNamespace(stdout=b"", stderr=b"", returncode=0)

    monkeypatch.setattr(report.subprocess, "run", compile_stub)
    assert report.generate_report(payload, request).pdf_path
    assert report.generate_report(payload, request).pdf_path
    assert observed == [b"controlled fixture"] * 4
    assert payload.figure_data == {"plan": b"controlled fixture"}
    assert (tmp_path / "test_assets" / "images" / "plan.png").read_bytes() == b"controlled fixture"
    assert "test_assets/images/plan.png" in (tmp_path / "test.tex").read_text(encoding="utf-8")


def test_longtable_caption_rows_are_terminated_without_changing_figures():
    tex = ("\\begin{longtable}{c}\n\\caption{A}\n\\hline\n"
           "\\end{longtable}\n\\begin{figure}\n\\caption{B}\n\\end{figure}")
    result = report._finish_longtable_captions(tex)
    assert "\\caption{A}\\\\\n\\hline" in result
    assert "\\caption{B}\n" in result
    assert report._finish_longtable_captions(result) == result


def test_compiler_failure_does_not_report_stale_pdf(monkeypatch, tmp_path):
    metadata = report.ReportMetadata("Project", "", "", "", "")
    options = report.ReportOptions([], False, False, True)
    payload = report.ReportPayload(metadata, options, {}, {}, [], report.ReportFigures())
    request = report.ReportRequest(metadata, options, str(tmp_path), "test")
    (tmp_path / "test.pdf").write_bytes(b"previous report")
    monkeypatch.setattr(report, "calculate_material_quantities", lambda *_: {})
    for name in ("preamble", "title_page", "executive_summary", "ch1_project_info",
                 "ch2_input_parameters", "ch7_quantities", "ch8_design_log", "references"):
        monkeypatch.setattr(report, name, lambda *args: "")
    monkeypatch.setattr(report.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(stdout=b"compiler failed", stderr=b"", returncode=1))
    result = report.generate_report(payload, request)
    assert result.pdf_path is None
    assert (tmp_path / "test.pdf").read_bytes() == b"previous report"
