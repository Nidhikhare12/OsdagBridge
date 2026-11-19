from types import SimpleNamespace

import pytest
import xarray as xr

from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
from osdagbridge.core.reports.chap5 import ch5_design_checks
from osdagbridge.core.reports.report_generator import ReportDataBridge
from osdagbridge.core.utils.common import KEY_TS_NO_OF_GIRDERS


class Grillage:
    common_grillage_element_z_group = {
        "exterior_main_beam_1": [1], "interior_main_beam": [2, 3],
        "exterior_main_beam_2": [4], "edge_beam": [0, 5],
    }

    def get_element(self, *, member, z_group_num, options):
        group = self.common_grillage_element_z_group[member][z_group_num]
        return [group] if options == "elements" else [[group, group + 10]]


def test_four_main_girders_exclude_edge_beams():
    model = Grillage()
    dataset = xr.Dataset(coords={"Element": range(6), "Node": range(16)})
    results = PlateGirderAnalysisResults(dataset, SimpleNamespace(model=model))
    groups = results.design_girder_groups(4)
    assert list(groups) == ["G1", "G2", "G3", "G4"]
    assert [value["elements"] for value in groups.values()] == [[1], [2], [3], [4]]

    with pytest.raises(ValueError, match="Expected 5 main girders"):
        results.design_girder_groups(5)
    model.common_grillage_element_z_group = {**model.common_grillage_element_z_group,
                                             "interior_main_beam": [2, 2]}
    with pytest.raises(ValueError, match="G3"):
        results.design_girder_groups(4)
    model.common_grillage_element_z_group["interior_main_beam"] = [2, 7]
    with pytest.raises(ValueError, match="G3"):
        results.design_girder_groups(4)


def test_moment_and_shear_tables_show_each_girders_own_results():
    checks = {
        "G1": {"checks": [{"check_id": 1, "demand": 100, "capacity": 200,
                           "dcr": 0.5, "status": "PASS"}]},
        "G2": {"checks": [{"check_id": 1, "demand": 300, "capacity": 250,
                           "dcr": 1.2, "status": "FAIL"}]},
    }
    bridge = ReportDataBridge({"design_results": {"per_girder": checks}},
                              {KEY_TS_NO_OF_GIRDERS: 3}, None)
    chapter = ch5_design_checks([], bridge)
    moment = chapter.split("Moment Capacity Check", 1)[1].split("Shear Capacity Check", 1)[0]
    assert "100.00 kN-m" in moment and "200.00 kN-m" in moment and "0.50 & PASS" in moment
    assert "300.00 kN-m" in moment and "250.00 kN-m" in moment and "1.20 & FAIL" in moment
    assert "Unavailable" in moment
