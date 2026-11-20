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


def test_utilization_chart_vertical_axes_and_missing(monkeypatch, tmp_path):
    from matplotlib.figure import Figure

    captured = {}
    def save(fig, path, **kwargs):
        ax = fig.axes[0]
        captured["xlabel"] = ax.get_xlabel()
        captured["ylabel"] = ax.get_ylabel()
        captured["xlim"] = ax.get_xlim()
        captured["bars"] = [(bar.get_height(), bar.get_width()) for bar in ax.patches]
        captured["styles"] = [(bar.get_facecolor(), bar.get_hatch()) for bar in ax.patches]
        captured["lines"] = [(list(line.get_ydata()), line.get_color(), line.get_linestyle()) for line in ax.lines]
        captured["texts"] = [text.get_text() for text in ax.texts]

    monkeypatch.setattr(Figure, "savefig", save)
    data = {"design_results": {"per_girder": {"G1": {"checks": [{"dcr": 1.577, "name": "Fatigue"}]}}},
            "deck_design_results": {"ur_composite_crack": .9914}}
    girder_utilization_chart(data, tmp_path)
    assert captured["xlabel"] == "Structural Component"
    assert captured["ylabel"] == "Utilization Ratio"
    assert captured["xlim"] == (-0.6, 3.6)
    assert all("\\\\n" not in text for text in captured["texts"])
    assert [height for height, _ in captured["bars"]] == [1.577, .9914]
    assert all(abs(width - .58) < 1e-9 for _, width in captured["bars"])
    assert ([1.0, 1.0], "red", "--") in captured["lines"]
    assert sum(text == "Not available" for text in captured["texts"]) == 2
    assert any("1.577  FAIL" in text or "1.577 FAIL" in text for text in captured["texts"])
    assert captured["styles"][0][0] != captured["styles"][1][0]
    assert captured["styles"][0][1] == "///" and captured["styles"][1][1] is None
    assert any("PASS" in text for text in captured["texts"])


def test_crash_barrier_ambiguous_area_is_not_converted_to_zero():
    from osdagbridge.core.boq.boq_generator import calculate_material_quantities
    for area in (0.3023, 302300):
        quantities = calculate_material_quantities({"typical_section.crash_barrier.area": area}, {})
        assert quantities["crash_barrier_vol_total"] == "N.A."
        assert quantities["crash_barrier_wt_total"] == "N.A."


def test_deck_chart_labels_unavailable_capacity_without_plotting_fallback(monkeypatch, tmp_path):
    from matplotlib.figure import Figure

    rendered = []

    def save(fig, path, **kwargs):
        ax = fig.axes[0]
        rendered.append(([bar.get_height() for bar in ax.patches],
                         [item.get_text() for item in ax.texts],
                         [item.get_text() for item in ax.get_xticklabels()]))

    monkeypatch.setattr(Figure, "savefig", save)
    result = {"ur_bot_shear": 9.999, "ur_unavailable_capacity": ["ur_bot_shear"]}
    outputs = {"deck_design_results": result}
    girder_utilization_chart(outputs, tmp_path)
    bars, notes, _ = rendered[-1]
    assert not bars
    assert "Capacity unavailable" in notes

    result["ur_composite_crack"] = 0.9914
    girder_utilization_chart(outputs, tmp_path)
    bars, notes, labels = rendered[-1]
    assert bars == [0.9914]
    assert any(text.startswith("0.991 PASS") for text in notes)
    assert any("Some capacities unavailable" in label for label in labels)
