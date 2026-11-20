import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

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
    monkeypatch.setattr(report, "executive_summary", lambda inputs, outputs, figures: r"\includegraphics{" + figures["plan"] + "}")
    observed = []

    def compile_stub(command, **kwargs):
        images = Path(kwargs["cwd"]) / "images"
        observed.append((images / "plan.png").read_bytes())
        (Path(kwargs["cwd"]) / "test.pdf").write_bytes(b"%PDF-1.4\ncontrolled fixture\n%%EOF\n")
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


@pytest.fixture
def export_report(monkeypatch, tmp_path):
    metadata = report.ReportMetadata("Project", "", "", "", "")
    options = report.ReportOptions([], False, False, True)
    payload = report.ReportPayload(metadata, options, {}, {}, [], report.ReportFigures())
    request = report.ReportRequest(metadata, options, str(tmp_path), "test")
    monkeypatch.setattr(report, "calculate_material_quantities", lambda *_: {})
    for name in ("preamble", "title_page", "executive_summary", "ch1_project_info",
                 "ch2_input_parameters", "ch7_quantities", "ch8_design_log", "references"):
        monkeypatch.setattr(report, name, lambda *args: "")
    monkeypatch.setattr(report, "executive_summary", lambda inputs, outputs, figures:
                        "\n".join(r"\includegraphics{" + path + "}" for path in figures.values()))

    def export(version, *, fail_pass=None, omit_pdf_pass=None):
        pass_number = 0
        payload.figure_data = {version: version.encode()}

        def compile_stub(command, *, cwd, **kwargs):
            nonlocal pass_number
            pass_number += 1
            work = Path(cwd)
            (work / "test.log").write_text(f"{version} pass {pass_number}", encoding="utf-8")
            if pass_number != omit_pdf_pass:
                (work / "test.pdf").write_bytes(f"%PDF-1.4\n{version}\n%%EOF\n".encode())
            return SimpleNamespace(stdout=b"compiler stdout", stderr=b"compiler stderr",
                                   returncode=int(pass_number == fail_pass))

        monkeypatch.setattr(report.subprocess, "run", compile_stub)
        return report.generate_report(payload, request)

    return export


def bundle_bytes(directory):
    return {path.relative_to(directory): path.read_bytes() for path in directory.rglob("*")
            if path.is_file() and path.relative_to(directory).parts[0] in
            {"test.pdf", "test.tex", "test.log", "test_assets"}}


def test_failed_reexport_preserves_successful_bundle(export_report, tmp_path):
    assert export_report("first").pdf_path
    before = bundle_bytes(tmp_path)

    result = export_report("second", fail_pass=2)

    assert result.pdf_path is None
    assert bundle_bytes(tmp_path) == before
    diagnostic_tex = Path(result.tex_path)
    assert diagnostic_tex.parent != tmp_path
    assert "test_assets/images/second.png" in diagnostic_tex.read_text(encoding="utf-8")
    assert (diagnostic_tex.parent / "test.log").read_text(encoding="utf-8") == "second pass 2"
    assert (diagnostic_tex.parent / "test_assets/images/second.png").read_bytes() == b"second"
    assert "compiler stderr" in (diagnostic_tex.parent / "compiler-output.txt").read_text(encoding="utf-8")
    assert not (diagnostic_tex.parent / "test.pdf").exists()


def test_successful_reexport_replaces_bundle_and_removes_stale_assets(export_report, tmp_path):
    assert export_report("first").pdf_path
    result = export_report("second")

    assert Path(result.pdf_path) == tmp_path / "test.pdf"
    assert Path(result.tex_path) == tmp_path / "test.tex"
    assert b"second" in (tmp_path / "test.pdf").read_bytes()
    assert "test_assets/images/second.png" in (tmp_path / "test.tex").read_text(encoding="utf-8")
    assert (tmp_path / "test.log").read_text(encoding="utf-8") == "second pass 2"
    assert (tmp_path / "test_assets/images/second.png").read_bytes() == b"second"
    assert not (tmp_path / "test_assets/images/first.png").exists()
    assert {path.name for path in tmp_path.iterdir()} == {"test.pdf", "test.tex", "test.log", "test_assets"}


@pytest.mark.parametrize("failure", [{"fail_pass": 1}, {"omit_pdf_pass": 2}])
def test_first_failed_export_only_publishes_diagnostics(export_report, tmp_path, failure):
    result = export_report("failed", **failure)

    assert result.pdf_path is None
    assert not bundle_bytes(tmp_path)
    diagnostic_tex = Path(result.tex_path)
    assert diagnostic_tex.is_file()
    assert diagnostic_tex.parent.parent == tmp_path
    assert (diagnostic_tex.parent / "compiler-output.txt").is_file()
    assert list(tmp_path.iterdir()) == [diagnostic_tex.parent]


def test_publish_error_restores_existing_bundle(export_report, tmp_path, monkeypatch):
    assert export_report("first").pdf_path
    before = bundle_bytes(tmp_path)
    replace = Path.replace

    def replace_with_locked_destination(self, target):
        if self.parent.name.startswith(".report-") and target == tmp_path / "test_assets":
            raise PermissionError("simulated Windows sharing violation")
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", replace_with_locked_destination)
    result = export_report("second")

    assert result.pdf_path is None
    assert bundle_bytes(tmp_path) == before
    diagnostic = Path(result.tex_path).with_name("compiler-output.txt")
    assert "simulated Windows sharing violation" in diagnostic.read_text(encoding="utf-8")
    assert not (tmp_path / ".test.publish").exists()
