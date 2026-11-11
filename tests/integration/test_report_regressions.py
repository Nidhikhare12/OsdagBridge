"""Focused regressions for the reviewed data-integrity and layout failures."""
import copy
import math
from types import SimpleNamespace
import pytest
from osdagbridge.core.reports.report_data import check_records, governing_checks, quantity_records, utilization, selected
from osdagbridge.core.reports.visualizations import generate_ur_bar_chart
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.report_generator import build_report_payload, generate_report
from osdagbridge.core.utils import common as K


@pytest.mark.parametrize("value,expected", [(0.8,"PASS"),(1,"PASS"),(1.00001,"FAIL"),(1.4,"FAIL")])
def test_real_girder_schema(value, expected):
    output = {"design_results": {"per_girder": {"G4": {"checks": [
        {"check_id": 1,"name": "Moment", "dcr": value,"demand":100*value,"capacity":100}]}}}}
    records = governing_checks(check_records(output, {}))
    assert records[0].ur == value
    assert records[0].member == "G4"
    assert records[0].status == expected
    assert records[3].ur is None


@pytest.mark.parametrize("value", [None, "", float("nan"), float("inf"), -1])
def test_missing_or_invalid_ratio(value):
    assert utilization(ratio=value) is None


def test_zero_capacity_and_explicit_percent():
    assert utilization(1,0,0.5) is None
    assert utilization(ratio=82,percent=True) == .82
    assert utilization(ratio=82) == 82


def test_quantity_sum_and_unavailable():
    r=quantity_records({"steel_girders_wt_total": 0,"bracing_top_wt_total":1,
       "bracing_bot_wt_total":2,"bracing_diag_wt_total":3,"bracing_wt_total":6})
    assert r[0].value == 0
    assert r[1].value == 6
    assert r[2].value is None
    assert r[4].estimated
    assert all(x.value is None for x in quantity_records({}))


def test_missing_chart_values_have_no_bars(tmp_path):
    fig=generate_ur_bar_chart({"Missing":None,"Zero":0,"Failure":1.2}, str(tmp_path/'chart.png'))
    ax=fig.axes[0]
    assert len(ax.patches)==2
    assert [b.get_height() for b in ax.patches]==[0,1.2]
    assert any(t.get_text()=="Not available" for t in ax.texts)
    assert ax.get_ylim()[1]>1.2


def test_selection_and_footway(default_bridge_inputs):
    data=default_bridge_inputs
    for key in [K.KEY_LL_IRC_CLASS_A,K.KEY_LL_IRC_70R_WHEELED,K.KEY_LL_IRC_70R_TRACKED,
                K.KEY_LL_IRC_AA_WHEELED,K.KEY_LL_IRC_AA_TRACKED,K.KEY_LL_IRC_CLASS_SV,
                K.KEY_LL_IRC_70R_BOGIE,K.KEY_LL_IRC_CLASS_FATIGUE]:
        data[key]='False'
    data[K.KEY_FOOTPATH]='None'
    tex=ch3_loads(data)
    assert 'No Vehicular Live Load' in tex
    assert 'Applied Pedestrian Live Load Intensity & Not applicable' in tex
    data.update({K.KEY_FOOTPATH:'Single Side',K.KEY_TS_FOOTPATH_WIDTH:2,
                 K.KEY_LL_FOOTPATH_PRESSURE_MODE:'User-defined',K.KEY_LL_FOOTPATH_PRESSURE_VALUE:3})
    tex=ch3_loads(data)
    assert '6.00 per side' in tex
    data[K.KEY_LL_FOOTPATH_PRESSURE_VALUE]=0
    assert '0.00 per side' in ch3_loads(data)


def test_compiler_failure_does_not_return_old_pdf(default_bridge_inputs, report_request_factory, monkeypatch):
    request=report_request_factory('Failed')
    request.options.include_figures=False
    from pathlib import Path
    old=Path(request.output_dir)/'Failed.pdf'
    old.write_bytes(b'old PDF')
    monkeypatch.setattr('subprocess.run',lambda *a,**kw: SimpleNamespace(returncode=1,stdout=b'failure',stderr=b''))
    result=generate_report(build_report_payload(request,default_bridge_inputs,{}),request)
    assert result.pdf_path is None
    assert old.read_bytes()==b'old PDF'
    assert result.tex_path


def test_no_figures_and_no_input_mutation(default_bridge_inputs, report_request_factory):
    request=report_request_factory('NoFigures')
    request.options.include_figures=False
    original=copy.deepcopy(default_bridge_inputs)
    payload=build_report_payload(request,default_bridge_inputs,{})
    assert default_bridge_inputs==original
    before=copy.deepcopy(payload.inputs)
    result=generate_report(payload,request)
    assert payload.inputs==before
    from pathlib import Path
    tex=Path(result.tex_path).read_text(encoding='utf-8')
    assert r"\begin{figure}" not in tex
    assert 'Overall Design Check Summary' in tex
    assert not (Path(request.output_dir)/'images/ur_summary.png').exists()
    # A labelled caption must stay before the first-page header boundary.
    start=tex.index(r"\label{tab:vehicular_ll}")
    assert tex.index(r"\endfirsthead",start)<tex.index(r"\endhead",start)


def test_summary_does_not_claim_missing_components_pass(default_bridge_inputs, default_bridge_outputs):
    from osdagbridge.core.reports.executive_summary import executive_summary
    tex = executive_summary(default_bridge_inputs, default_bridge_outputs, {})
    tex = tex.replace(r"\allowbreak{}", "")
    assert "Steel plate girders: FAIL" in tex
    assert "End diaphragms: Not available" in tex
    assert "1.210 (FAIL)" in tex and "1.250 (FAIL)" in tex
    assert "design pass" not in tex


def test_deck_partial_results_do_not_create_passes(default_bridge_inputs, default_bridge_outputs):
    from osdagbridge.core.reports.chap5 import ch5_design_checks
    from osdagbridge.core.reports.report_generator import ReportDataBridge
    tex = ch5_design_checks([], ReportDataBridge(default_bridge_inputs, default_bridge_outputs))
    assert "0.0000" not in tex
    assert "Not available: verified end-diaphragm results are not supplied." in tex


def test_export_without_pdf_retains_assets(default_bridge_inputs, report_request_factory, monkeypatch):
    import io
    from PIL import Image
    from pathlib import Path
    request = report_request_factory("Source only")
    request.options.include_pdf = False
    request.options.sections = ["loads"]
    stream = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(stream, format="PNG")
    payload = build_report_payload(request, default_bridge_inputs, {})
    payload.figure_data["girder_top"] = stream.getvalue()
    def unexpected(*args, **kwargs):
        raise AssertionError("Source-only generation must not invoke a compiler")
    monkeypatch.setattr("subprocess.run", unexpected)
    result = generate_report(payload, request)
    assert result.tex_path and result.pdf_path is None
    assert (Path(request.output_dir) / "images/girder_top.png").exists()
    tex = Path(result.tex_path).read_text(encoding="utf-8")
    assert "{images/girder_top.png}" in tex
    assert "ur_summary.png" not in tex


def test_chart_does_not_change_backend(tmp_path):
    import matplotlib
    import importlib
    from osdagbridge.core.reports import visualizations
    before = matplotlib.get_backend()
    importlib.reload(visualizations)
    visualizations.generate_ur_summary_chart(output_path=str(tmp_path / "missing.png"))
    assert matplotlib.get_backend() == before


def test_custom_vehicle_special_characters(default_bridge_inputs):
    from osdagbridge.core.reports.report_utils import _tex
    name = r"Custom\A & B_50% {test}"
    default_bridge_inputs[K.KEY_LL_CUSTOM_VEHICLES] = [{"name": name}]
    tex = ch3_loads(default_bridge_inputs)
    assert _tex(name) in tex
    assert r"\textbackslash{}A" in tex
    assert r"\&" in tex and r"\%" in tex


def test_governing_combination_retained_on_envelope_tie():
    check = {"check_id":1, "name":"Moment", "dcr":1.2, "demand":120, "capacity":100}
    output = {"design_results":{"per_girder":{"G4":{"checks":[check],
              "per_lc":{"ULS 1.35 DL + 1.5 LL":{"checks":[check]}}}}}}
    record = governing_checks(check_records(output, {}))[0]
    assert record.load_case == "ULS 1.35 DL + 1.5 LL"
