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
        return SimpleNamespace(stdout=b"", stderr=b"")

    monkeypatch.setattr(report.subprocess, "run", compile_stub)
    assert report.generate_report(payload, request).pdf_path
    assert report.generate_report(payload, request).pdf_path
    assert observed == [b"controlled fixture"] * 4
    assert payload.figure_data == {"plan": b"controlled fixture"}
    assert (tmp_path / "test_assets" / "images" / "plan.png").read_bytes() == b"controlled fixture"
    assert "test_assets/images/plan.png" in (tmp_path / "test.tex").read_text(encoding="utf-8")
