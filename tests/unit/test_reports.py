"""Report regressions runnable without Osdag, Qt, CAD or a TeX installation."""
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from osdagbridge.core.reports import report_generator as report
from osdagbridge.core.reports.chap1 import ch1_project_info
from osdagbridge.core.reports.chap2 import ch2_input_parameters
from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.chap4 import ch4_analysis
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.chap8 import ch8_design_log
from osdagbridge.core.reports.plots import (
    material_values, utilization_values, number, save_plots, figure_latex, _bars,
)
from osdagbridge.core.reports.load_tables import selected
from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.reports.styles import preamble
from osdagbridge.core.utils import common as keys


@pytest.fixture
def metadata():
    return report.ReportMetadata('Report regression fixture', 'Test location', 'Test', 'Test', 'Test')


@pytest.fixture
def outputs():
    return {
        'design_results': {'per_girder': {
            'G1': {'checks': [{'check_id': 1, 'dcr': .8, 'demand': 80, 'capacity': 100}],
                   'per_lc': {'SLS': {'checks': [{'id': 13, 'dcr': 1.2}]}}},
            'G2': {'checks': [{'check_id': 2, 'dcr': .95}]},
            'EB1': {'checks': [{'dcr': 99}]},
        }},
        'deck_design_results': {'ur_flexure': .75, 'ur_shear': 1.05},
        'crossbracing_design_results': {'G1-G2': {'diagonal': {'compression': {'Optimum.UR': .9}}}},
        'end_diaphragm_design_results': {'end': {'chord': {'tension': {'Member.efficiency': .6}}}},
    }


def assert_headers(tex):
    tables = re.findall(r'\\begin\{longtable\}(.*?)\\end\{longtable\}', tex, re.S)
    assert tables
    for table in tables:
        assert table.count(r'\endfirsthead') == 1
        assert table.count(r'\endhead') == 1
        first, remainder = table.split(r'\endfirsthead')
        continuation, body = remainder.split(r'\endhead')
        assert r'\textbf' in continuation, table[:150]
        assert r'\caption' not in continuation  # repeated captions change numbering
        assert r'\hline' in continuation
        assert body.strip()
        if r'\caption' in first:
            assert re.search(r'\\(?:\n)?\s*\\hline', first), first[:150]


def test_every_table_has_real_continuation_headers(metadata):
    inputs = {keys.KEY_TS_NO_OF_GIRDERS: 4}
    bridge = report.ReportDataBridge({}, inputs, None)
    for tex in (ch1_project_info(metadata), ch2_input_parameters(metadata, inputs, {}),
                ch3_loads(inputs), ch4_analysis({}, {}, bridge, 20),
                ch5_design_checks([], bridge), ch7_quantities({}), ch8_design_log([], {})):
        assert_headers(tex)
        assert tex.count(r'\begingroup') == tex.count(r'\endgroup')
    assert r'\multirow' not in ch5_design_checks([], bridge)


@pytest.mark.parametrize('value,expected', [(False, False), ('False', False), ('0', False),
                                         ('off', False), (True, True), ('true', True), (1, True)])
def test_gui_checkbox_values(value, expected):
    assert selected(value) == expected


def test_vehicle_and_footway_selection():
    inputs = {keys.KEY_LL_IRC_CLASS_A: 'False', keys.KEY_LL_IRC_70R_TRACKED: True,
              keys.KEY_LL_CUSTOM_VEHICLES: [{'name': 'Custom & Heavy_1'}],
              keys.KEY_FOOTPATH: 'Both Sides', keys.KEY_LL_FOOTPATH_PRESSURE_MODE: 'Custom',
              keys.KEY_LL_FOOTPATH_PRESSURE_VALUE: 7.5}
    tex = ch3_loads(inputs)
    vehicle = tex.split('Vehicle Live Loads (LL)')[1].split(r'\end{longtable}')[0]
    footway = tex.split('Footway Live Loads')[1].split(r'\end{longtable}')[0]
    assert 'Class 70R (Tracked)' in vehicle
    assert 'Class A' not in vehicle
    assert r'Custom \& Heavy\_\allowbreak{}1' in vehicle
    assert '7.5' in footway and 'kN/m$^2$' in footway
    assert 'Footway live load' not in vehicle
    inputs[keys.KEY_FOOTPATH] = 'None'
    tex = ch3_loads(inputs).split('Footway Live Loads')[1].split(r'\end{longtable}')[0]
    assert 'Not applicable' in tex and '7.5' not in tex


def test_automatic_footway_and_no_vehicles():
    tex = ch3_loads({keys.KEY_FOOTPATH: 'Single Side', keys.KEY_LL_FOOTPATH_PRESSURE_MODE: 'As per IRC 6'})
    assert 'None selected' in tex and '4.905' in tex


def test_ur_uses_ratios_all_members_and_all_cases(outputs):
    assert list(utilization_values(outputs).values()) == [1.2, 1.05, .9, .6]
    assert all(v is None for v in utilization_values({}).values())


@pytest.mark.parametrize('value', [None, 'N.A.', 'bad', float('inf'), float('nan'), -1, True])
def test_invalid_data_is_not_zero(value):
    assert number(value) is None


def test_quantities_preserve_units_and_avoid_partial_sums():
    values = {'steel_girders_wt_total': 10, 'bracing_top_wt_total': 1,
              'bracing_bot_wt_total': 2, 'bracing_diag_wt_total': 3,
              'concrete_deck_vol_total': 24, 'rebar_deck_wt_total': 2.88}
    data = material_values(values)
    assert data == {'Girders': 10, 'Cross bracing': 6, 'End diaphragms': None,
                    'Concrete': 24, 'Reinforcement': 2.88}
    del values['bracing_bot_wt_total']
    assert material_values(values)['Cross bracing'] is None
    values['steel_bracing_wt_total'] = 6
    assert material_values(values)['Cross bracing'] == 6


def test_plots_write_real_png_and_embed_in_requested_sections(tmp_path, outputs):
    paths = save_plots(outputs, {}, tmp_path)
    for path in paths.values():
        assert Path(path).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    from matplotlib.figure import Figure
    ax = Figure().subplots()
    _bars(ax, {'pass': .8, 'fail': 1.2, 'missing': None, 'zero': 0}, 'Utilization Ratio', True)
    assert len(ax.patches) == 3  # missing value has text, no fabricated zero bar
    assert ax.get_xlim()[1] > 3  # include missing and zero categories in the view
    assert list(ax.lines[0].get_ydata()) == [1.0, 1.0]
    assert ax.lines[0].get_linestyle() == '--'
    bridge = report.ReportDataBridge({}, {}, None)
    tex = ch5_design_checks([], bridge, paths)
    assert tex.index('utilization.png') > tex.index(r'\label{sec:overall-summary}')
    assert 'structural_steel.png' in ch7_quantities({}, paths)
    assert 'concrete_reinforcement.png' in ch7_quantities({}, paths)
    assert figure_latex(None, 'Caption') == ''


def test_shared_styles_reserve_footer_space():
    tex = preamble('Project', 'Job', 'Date')
    assert 'includeheadfoot' in tex and 'footskip=18mm' in tex and 'bottom=32mm' in tex
    assert r'\vspace{-20pt}' not in tex
    assert r'\Needspace{7\baselineskip}' in tex
    assert r'\titleformat{\chapter}' in tex  # chapter styling also applies without a TOC
    assert _tex('A\\B_{x}&') == r'A\textbackslash{}B\_\allowbreak{}\{x\}\&'


def test_full_pipeline_keeps_assets_and_rejects_stale_pdf(tmp_path, monkeypatch, metadata):
    options = report.ReportOptions(['loads', 'design_checks'], True, False, True)
    payload = report.ReportPayload(metadata, options, {}, {}, [], report.ReportFigures())
    request = report.ReportRequest(metadata, options, str(tmp_path), 'Report_After')
    stale = tmp_path / 'Report_After.pdf'
    stale.write_bytes(b'stale PDF must not count as successful generation')
    monkeypatch.setattr(report.subprocess, 'run', lambda *a, **k: SimpleNamespace(
        returncode=1, stdout=b'compiler unavailable in test', stderr=b''))
    result = report.generate_report(payload, request)
    assert result.pdf_path is None
    assert result.tex_path is not None
    tex = Path(result.tex_path).read_text(encoding='utf-8')
    assert 'Report_After_assets/utilization.png' in tex
    assert 'Report_After_Report_After_assets' not in tex
    assert (tmp_path / 'Report_After_assets/utilization.png').exists()
    assert str(tmp_path).replace('\\', '/') not in tex
    assert_headers(tex)


def test_charts_do_not_depend_on_drawings_and_missing_compiler_keeps_tex(tmp_path, monkeypatch, metadata):
    # The GUI sets include_figures only when "Drawings" is ticked; the Chapter 5
    # and 7 charts must still be produced without it.
    options = report.ReportOptions(['loads', 'design_checks'], False, False, True)
    payload = report.ReportPayload(metadata, options, {}, {}, [], report.ReportFigures())
    request = report.ReportRequest(metadata, options, str(tmp_path), 'No_Drawings')
    def missing_compiler(*args, **kwargs):
        raise FileNotFoundError('pdflatex missing')
    monkeypatch.setattr(report.subprocess, 'run', missing_compiler)
    result = report.generate_report(payload, request)
    assert result.pdf_path is None and Path(result.tex_path).exists()
    tex = Path(result.tex_path).read_text(encoding='utf-8')
    for chart in ('utilization.png', 'structural_steel.png', 'concrete_reinforcement.png'):
        assert chart in tex
    assert 'Drawings were requested' not in tex and 'Drawings were not selected' in tex


def test_successful_compiler_returns_new_pdf(tmp_path, monkeypatch, metadata):
    options = report.ReportOptions([], False, False, True)
    payload = report.ReportPayload(metadata, options, {}, {}, [], report.ReportFigures())
    request = report.ReportRequest(metadata, options, str(tmp_path), 'Fresh')
    def compiler(args, **kwargs):
        (Path(kwargs['cwd']) / 'Fresh.pdf').write_bytes(b'%PDF-test-compiler-output')
        return SimpleNamespace(returncode=0, stdout=b'', stderr=b'')
    monkeypatch.setattr(report.subprocess, 'run', compiler)
    result = report.generate_report(payload, request)
    assert Path(result.pdf_path).read_bytes() == b'%PDF-test-compiler-output'


def test_bracing_slenderness_uses_compression_result_and_member_limit():
    from osdagbridge.core.reports.plots import member_ur
    results = {'G1-G2': {
        'diagonal': {'compression': {'Member.efficiency': .2, 'Member.Slenderness': 125.0},
                     'tension': {'Member.efficiency': .1, 'Member.Slenderness': 240.0}},
        'chord': {'tension': {'Member.efficiency': .05, 'Member.Slenderness': 200.0}},
    }}
    # Diagonal: 125/250 = 0.5 (tension KL/r is not compared with the 250 limit).
    # Chord: no compression result, so tension KL/r 200/400 = 0.5.
    assert member_ur(results) == pytest.approx(.5)


def test_bracing_type_end_diaphragm_matches_summary_table_rule(outputs):
    outputs = dict(outputs, end_diaphragm_design_results={})
    assert list(utilization_values(outputs).values())[-1] is None
    inputs = {keys.KEY_MP_ED_TYPE + '.G1G2.E1M1': 'Cross Bracing'}
    values = utilization_values(outputs, inputs)
    assert values['End diaphragms\n(as bracing)'] == values['Cross\nbracing']


VALIDATION = Path(__file__).resolve().parents[2] / 'validation' / 'design'


@pytest.mark.skipif(not (VALIDATION / 'outputs.json').exists(), reason='validation snapshot not present')
def test_ur_chart_matches_overall_summary_table():
    """Every bar must equal the largest UR of that element's rows in Section 5.5."""
    import json
    outputs = json.loads((VALIDATION / 'outputs.json').read_text(encoding='utf-8'))
    inputs = json.loads((VALIDATION / 'inputs.json').read_text(encoding='utf-8'))
    tex = ch5_design_checks([], report.ReportDataBridge(outputs, inputs, None), {})
    table = tex[tex.index(r'\label{tab:overall-summary}'):]
    table = table[:table.index(r'\end{longtable}')]
    rows = {}
    for line in table.splitlines():
        cells = line.split(' & ')
        if len(cells) == 5:
            match = re.search(r'([0-9]+\.[0-9]+)', cells[-1])
            if match:
                rows[cells[0].strip()] = float(match.group(1))
    groups = {'Steel plate\ngirders': ('Girder',), 'Concrete\ndeck slab': ('Deck', 'Crack Width', 'Transverse Shear'),
              'Cross\nbracing': ('Cross Bracing',), 'End diaphragms\n(as bracing)': ('End Diaphragm',)}
    for bar, value in utilization_values(outputs, inputs).items():
        table_max = max(v for label, v in rows.items() if label.startswith(groups[bar]))
        assert round(value, 2) == pytest.approx(table_max, abs=.006), bar


def test_header_omits_empty_job_number_and_palette_is_single_source():
    from osdagbridge.core.reports.styles import PALETTE, CHART
    tex = preamble('Project', '', 'Date')
    assert r'\fancyhead[L]{Project}' in tex
    assert r'\fancyhead[L]{Project $|$ Job}' in preamble('Project', 'Job', 'Date')
    for name, value in PALETTE.items():
        assert r'\definecolor{%s}{HTML}{%s}' % (name, value) in tex
    assert CHART['fail'] == '#' + PALETTE['reportFail']


def test_chapter_six_is_kept_when_drawings_are_omitted(tmp_path, monkeypatch, metadata):
    options = report.ReportOptions(['loads'], False, False, True)
    payload = report.ReportPayload(metadata, options, {}, {}, [], report.ReportFigures())
    request = report.ReportRequest(metadata, options, str(tmp_path), 'No_Drawings')
    monkeypatch.setattr(report.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=1, stdout=b'', stderr=b''))
    tex = Path(report.generate_report(payload, request).tex_path).read_text(encoding='utf-8')
    assert tex.index(r'\chapter{Drawings and Visualizations}') < tex.index(r'\setcounter{chapter}{6}')


def test_vehicle_table_follows_brief_layout():
    from osdagbridge.core.reports.load_tables import vehicle_rows
    inputs = {keys.KEY_SPAN: 20, keys.KEY_LL_ECCENTRICITY: '1.2',
              keys.KEY_LL_IRC_CLASS_A: True, keys.KEY_LL_IRC_70R_WHEELED: True,
              keys.KEY_LL_IRC_CLASS_SV: True, keys.KEY_LL_IRC_CLASS_FATIGUE: True,
              keys.KEY_LL_IRC_AA_TRACKED: True, keys.KEY_BL_IRC_CLASS_SV: 'False',
              keys.KEY_LL_CUSTOM_VEHICLES: [{'name': 'Crane', 'axle_loads': [100, 150], 'impact_factor': 0.2}]}
    rows = {r['name']: r for r in vehicle_rows(inputs)}
    assert list(rows) == ['Class A', 'Class 70R (Wheeled)', 'Class AA (Tracked)', 'Class SV', 'Class Fatigue', 'Crane']
    assert rows['Class A']['total_kN'] == pytest.approx(543.474)
    assert rows['Class A']['impact'] == pytest.approx(1.269)          # IRC 6 Cl. 208.2
    assert rows['Class 70R (Wheeled)']['impact'] == pytest.approx(1.1)  # IRC 6 Cl. 208.3
    assert rows['Class AA (Tracked)']['total_kN'] is None             # no definition in the code
    assert rows['Class SV']['braking'] is False                       # follows its own checkbox
    assert rows['Class Fatigue']['braking'] is False and rows['Class Fatigue']['eccentricity'] is None
    assert rows['Class A']['braking'] and rows['Class A']['eccentricity'] == 1.2
    assert rows['Crane']['total_kN'] == 250 and rows['Crane']['impact'] == pytest.approx(1.2)
    tex = ch3_loads(inputs)
    table = tex.split('Vehicle Live Loads (LL)')[1].split(r'\end{longtable}')[0]
    for heading in ('Total Load', 'Impact Factor', 'Braking Load', 'Considered?', 'Value (kN)', 'Eccentricity (m)'):
        assert heading in table
    assert 'Class A & 543.5 & 1.269 & Yes & N/A & 1.20' in table
    assert re.search(r'Class SV & 3776\.\d & N/A & No & -- & --', table)


def test_formatting_comes_only_from_styles():
    folder = Path(report.__file__).parent
    for path in folder.glob('*.py'):
        if path.name == 'styles.py':
            continue
        source = path.read_text(encoding='utf-8')
        # Row / line gaps such as \\[6pt] must use the named lengths from styles.py.
        assert not re.search(r'\\\\\[\d+(\.\d+)?(pt|cm|mm|em)\]', source), path.name
        assert not re.search(r'\\(text)?color\{(red|black|blue|green)\}', source), path.name
        assert r'\definecolor' not in source and r'\fontsize' not in source, path.name
    tex = ch5_design_checks([], report.ReportDataBridge({}, {}, None)) + ch3_loads({})
    assert r'\\[\ReportRowGap]' in tex
    assert r'[\\Report' not in tex  # a doubled backslash would break the length
    pre = preamble('P', 'J', 'D')
    for name in ('ReportRowGap', 'ReportPass', 'ReportFail', 'ReportTitleBlockGap'):
        assert '\\' + name in pre


def test_file_menu_report_captures_figures_like_output_dock():
    """File -> Create Design Report must go through the Output dock's figure capture."""
    pytest.importorskip('PySide6')
    from osdagbridge.desktop.ui import template_page
    calls = []
    page = SimpleNamespace(output_dock=SimpleNamespace(generate_report=lambda: calls.append('capture')),
                           open_report_dialog=lambda **kw: calls.append('dialog-without-figures'))
    template_page.CustomWindow.create_design_report(page)
    assert calls == ['capture']
    source = Path(template_page.__file__).read_text(encoding='utf-8')
    assert 'triggered.connect(lambda _: self.create_design_report())' in source


def test_bracing_results_with_live_text_entries():
    """The Transverse Member Design dialog adds text entries to each pair at runtime."""
    from osdagbridge.core.reports.plots import member_ur
    from osdagbridge.core.reports.executive_summary import _max_member_efficiency
    results = {'G1-G2': {'diagonal': {'compression': {'Member.efficiency': .3, 'Member.Slenderness': 100.0}},
                         'chord': {'tension': {'Member.efficiency': .1}},
                         'ed_type': 'Cross Bracing', 'ed_bracing_type': 'X-Bracing'},
               'note': 'not a pair'}
    assert member_ur(results) == pytest.approx(.4)        # 100 / 250
    assert _max_member_efficiency(results) == pytest.approx(.4)
    assert member_ur('unexpected') is None
    outputs = {'crossbracing_design_results': results}
    assert utilization_values(outputs)['Cross\nbracing'] == pytest.approx(.4)
