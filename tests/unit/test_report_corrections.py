from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "src" / "osdagbridge" / "core" / "reports"


def test_chapter3_acknowledges_unconfigured_footpath():
    source = (REPORTS / "chap3.py").read_text(encoding="utf-8")
    assert "No footpath load is applied" in source
    assert r"\ReportTopicBreak" in source


def test_end_diaphragm_report_uses_its_own_input_data_not_cross_bracing_rows():
    source = (REPORTS / "chap5.py").read_text(encoding="utf-8")
    start = source.index(r"\section{End Diaphragm Design}")
    end = source.index(r"\section{Overall Design Check Summary}", start)
    end_diaphragm_section = source[start:end]
    assert "_ed_forces_content" in end_diaphragm_section
    assert "_ed_slender_content" in end_diaphragm_section
    assert "_ed_capacity_content" in end_diaphragm_section
    assert "cb_forces_content" not in end_diaphragm_section
    assert "cb_slenderness_content" not in end_diaphragm_section


def test_executive_summary_includes_explicit_total_deflection_check():
    source = (REPORTS / "executive_summary.py").read_text(encoding="utf-8")
    assert "KEY_SD_DEFL_TOTAL" in source
    assert "Total-load deflection" in source


def test_material_chart_separates_deck_and_barrier_concrete_volume():
    source = (REPORTS / "chap7.py").read_text(encoding="utf-8")
    assert 'deck_concrete_m3 = _quantity(input_dict.get("concrete_deck_vol_total"))' in source
    assert 'barrier_m3 = _quantity(input_dict.get("crash_barrier_vol_total"))' in source
    assert 'volume_ax.set_ylabel("Volume (m³)")' in source


def test_missing_figure_assets_do_not_create_repeated_placeholder_text():
    source = (REPORTS / "report_utils.py").read_text(encoding="utf-8")
    assert 'return ""' in source
    chap6 = (REPORTS / "chap6.py").read_text(encoding="utf-8")
    assert "did not supply CAD figure assets" in chap6
