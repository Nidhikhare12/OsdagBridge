"""Regression tests for the report-generator enhancement assignment."""
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.report_charts import build_chart_images, utilization_rows
from osdagbridge.core.reports.report_generator import preamble
from osdagbridge.core.reports.styles import repeating_longtable_header


def test_shared_theme_reserves_header_and_footer_space():
    latex = preamble("Demo", "JOB-1", "2026-11-15")
    assert "bottom=0.95in" in latex
    assert "headheight=20pt" in latex
    assert "reportPass" in latex


def test_longtable_header_is_repeated_on_later_pages():
    header = repeating_longtable_header(r"\textbf{A} & \textbf{B} \\")
    assert r"\endfirsthead" in header
    assert r"\endhead" in header
    assert header.count(r"\textbf{A}") == 2


def test_chapter_three_separates_vehicle_and_footway_loads():
    latex = ch3_loads({})
    assert "Vehicle Live Loads" in latex
    assert "Footway Live Load" in latex
    assert "Load Combinations" in latex and r"\endhead" in latex


def test_charts_are_pngs_from_actual_payload_values():
    images = build_chart_images(
        [{"name": "Plate girder", "utilization_ratio": 0.83}],
        {
            "steel_girders_wt_total": "20.0",
            "concrete_deck_vol_total": "35.0",
            "rebar_deck_wt_total": "3.5",
        },
    )
    assert set(images) == {"utilization_summary", "material_quantities"}
    assert all(image.startswith(b"\x89PNG\r\n\x1a\n") for image in images.values())


def test_utilization_chart_accepts_calculated_output_dictionary_values():
    assert utilization_rows({"girder_utilization": "0.76"}) == [("girder utilization", 0.76)]


def test_chapter_seven_repeats_header_and_embeds_quantity_chart():
    latex = ch7_quantities({}, {"material_quantities": "images/material_quantities.png"})
    assert r"\endfirsthead" in latex
    assert "material_quantities.png" in latex


def test_selected_vehicles_exclude_false_flags_and_escape_names():
    from osdagbridge.core.reports.load_tables import live_load_tables
    from osdagbridge.core.utils import common as k
    latex = live_load_tables({k.KEY_LL_IRC_CLASS_A: 'Yes', k.KEY_LL_IRC_AA_TRACKED: 'No',
                             k.KEY_LL_CUSTOM_VEHICLES: [
                                 {'name': 'Hidden', 'included': False},
                                 {'name': 'Truck & trailer', 'included': True}]})
    assert 'Class A' in latex
    assert 'Class AA (Tracked)' not in latex
    assert 'Hidden' not in latex
    assert r'Truck \& trailer' in latex
    assert r'kN/m$^2$' in latex


def test_component_ratios_use_all_four_actual_result_schemas():
    from osdagbridge.core.reports.report_charts import component_utilizations
    outputs = {
        'design_results': {'per_girder': {
            'G1': {'checks': [{'dcr': 0.8}, {'dcr': 1.3}]},
            'EB1': {'checks': [{'dcr': 99}]} }},
        'deck_design_results': {'ur_bot_uls': 0.9, 'ur_top_uls': float('nan')},
        'crossbracing_design_results': {'G1-G2': {'diagonal': {
            'tension': {'Member.efficiency': 0.7}, 'compression': None}}},
        'end_diaphragm_design_results': {'G1-G2': {'chord': {
            'compression': {'Optimum.UR': 1.1}}}},
    }
    assert [value for _, value in component_utilizations(outputs)] == [1.3, 0.9, 0.7, 1.1]
    assert [value for _, value in component_utilizations({})] == [None] * 4


def test_multiline_header_keeps_body_and_is_idempotent():
    from osdagbridge.core.reports.styles import format_tables
    original = r'''\begin{longtable}{|L{3cm}|C{2cm}|}
\caption{A sample}
\hline
\textbf{Member} & \textbf{Value} \\ \hline
G4 & 0.88 \\ \hline
\end{longtable}'''
    result = format_tables(original)
    assert result.count(r'\textbf{Member}') == 2
    assert result.count('G4 & 0.88') == 1
    assert r'\multicolumn{2}' in result
    assert r'\caption{A sample}\\' in result
    assert format_tables(result) == result


def test_chart_rendering_does_not_change_gui_backend():
    import matplotlib
    before = matplotlib.get_backend()
    build_chart_images([], {}, {})
    assert matplotlib.get_backend() == before


def test_end_diaphragm_takeoff_counts_both_ends_and_all_pairs():
    from osdagbridge.core.boq.boq_generator import end_diaphragm_quantities
    from osdagbridge.core.utils import common as k

    def for_pair(key, pair):
        prefix, field = key.rsplit(".", 1)
        return f"{prefix}.{pair}.{field}"

    inputs = {k.KEY_TS_GIRDER_SPACING: 2.5, k.KEY_TS_NO_OF_GIRDERS: 3}
    outputs = {}
    for pair, mass in [('G1G2', 20), ('G2G3', 30)]:
        outputs[for_pair(k.KEY_MP_ED_TYPE, pair)] = 'Rolled Beam'
        outputs[for_pair(k.KEY_TD_ED_PROP_M, pair)] = mass
    result = end_diaphragm_quantities(inputs, outputs)
    assert result['end_diaphragms_qty'] == '4'
    assert result['end_diaphragms_wt_total'] == '0.250'
    del outputs[for_pair(k.KEY_TD_ED_PROP_M, 'G2G3')]
    assert end_diaphragm_quantities(inputs, outputs) == {}


def test_failed_compiler_never_returns_an_existing_pdf(tmp_path, monkeypatch):
    import subprocess
    from osdagbridge.core.reports import report_generator as g
    metadata = g.ReportMetadata('Test', '', '', '', '')
    options = g.ReportOptions([], False, False, True)
    request = g.ReportRequest(metadata, options, str(tmp_path), 'report')
    payload = g.ReportPayload(metadata, options, {}, {}, [], g.ReportFigures())
    (tmp_path / 'report.pdf').write_bytes(b'stale PDF')
    for name in ('executive_summary', 'ch1_project_info', 'ch2_input_parameters',
                 'ch7_quantities', 'ch8_design_log', 'references'):
        monkeypatch.setattr(g, name, lambda *args: '')
    monkeypatch.setattr(g, 'build_chart_images', lambda *args: {})
    monkeypatch.setattr(g.subprocess, 'run', lambda *a, **kw:
                        subprocess.CompletedProcess(a[0], 1, b'Compiler failed', b''))
    result = g.generate_report(payload, request)
    assert result.pdf_path is None
    assert result.tex_path
    assert (tmp_path / 'report_source' / 'report.compiler.log').read_bytes() == b'Compiler failed'
