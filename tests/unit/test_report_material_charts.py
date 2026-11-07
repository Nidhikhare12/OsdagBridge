import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from osdagbridge.core.reports.charts import (girder_utilization_chart, girder_utilizations,
                                             material_chart, material_values)
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.utils.common import KEY_TS_NO_OF_GIRDERS


def test_material_values_match_table_units_and_ignore_placeholders():
    data = {"steel_girders_wt_total": "4.50", "bracing_top_wt_total": "0",
            "bracing_bot_wt_total": "1.20", "bracing_diag_wt_total": "0.30",
            "concrete_deck_vol_total": "12.50", "rebar_deck_wt_total": r"\placeholder{x}"}
    result = material_values(data)
    assert result["Girder steel"] == 4.5
    assert result["Cross bracing steel"] == 1.5
    assert result["Concrete"] == 12.5
    assert result["Reinforcement steel"] is None
    assert result["End diaphragm steel"] is None
    assert material_values({"steel_girders_wt_total": "nan"})["Girder steel"] is None
    assert material_values({"bracing_top_wt_total": "2"})["Cross bracing steel"] is None


def test_chart_file_and_chapter_embedding(tmp_path):
    assert material_chart({}, tmp_path) is None
    path = material_chart({"steel_girders_wt_total": "0"}, tmp_path)
    assert Path(path).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert r"\includegraphics" in ch7_quantities({}, path)


def test_girder_chart_uses_recorded_dcr_and_ignores_missing(tmp_path):
    data = {"design_results": {"per_girder": {
        "G1": {"checks": [{"check_id": 1, "dcr": 0.8}, {"check_id": 2, "dcr": 1.1}]},
        "G2": {"checks": [{"check_id": 3, "dcr": None}]},
        "EB1": {"checks": [{"check_id": 4, "dcr": 9}]},
    }}}
    assert girder_utilizations(data) == [("G1", 1.1, 2)]
    data["design_results"]["per_girder"]["G5"] = {"checks": [{"check_id": 1, "dcr": 2}]}
    assert girder_utilizations(data, {KEY_TS_NO_OF_GIRDERS: 4}) == [("G1", 1.1, 2)]
    assert girder_utilization_chart({}, tmp_path) is None
    assert Path(girder_utilization_chart(data, tmp_path)).is_file()
