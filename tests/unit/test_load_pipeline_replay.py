import warnings

import ospgrillage as og
import xarray as xr

from osdagbridge.core.bridge_types.plate_girder.analyser import BridgeGrillageModel
from ospgrillage.osp_grillage import OspGrillage


class TestGrillageModel:
    __test__ = False
    common_grillage_element_z_group = {
        "exterior_main_beam_1": [1], "interior_main_beam": [2, 3],
        "exterior_main_beam_2": [4],
    }

    def __init__(self):
        self.load_case_list = []

    def get_element(self, *, member, options, z_group_num):
        return [self.common_grillage_element_z_group[member][z_group_num]]

    def add_load_case(self, load_case, load_factor=1):
        self.load_case_list.append({"name": load_case.name, "load_factor": load_factor})

    def analyze(self, **kwargs):
        pass


def test_live_load_selects_second_interior_girder_j_end_and_preserves_factors():
    bridge = BridgeGrillageModel.__new__(BridgeGrillageModel)
    bridge.model = TestGrillageModel()
    cases = [og.create_load_case(name=name) for name in ("Case1 exterior", "Case2 inner")]
    for case in cases:
        for factor in (1.0, 0.8):
            case.add_load(og.create_load(loadtype="nodal", node_tag=1, Fy=100),
                          load_factor=factor)
        bridge.model.add_load_case(case, load_factor=1.25)
    bridge.vehicle_load_cases_list = cases
    dataset = xr.Dataset({"forces": (("Loadcase", "Element", "Component"), [
        [[90, 3], [1, 2], [4, 5], [1, 2], [999, 999]],
        [[10, 20], [1, 2], [80, -250], [1, 2], [1, 1]],
    ])}, coords={"Loadcase": [case.name for case in cases], "Element": [1, 2, 3, 4, 5],
                 "Component": ["Mz_i", "Mz_j"]})
    bridge.create_governing_ll_load_case(dataset)
    assert bridge.governing_ll_name == "Case2 inner"
    assert [entry["factor"] for entry in bridge.ll_load_case.load_groups] == [1.25, 1.0]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        combined = bridge.create_dl_ll_combination(ll_factor=1.5)
    assert [entry["factor"] for entry in combined.load_groups] == [1.875, 1.5]
    commands = OspGrillage._distribute_load_types_to_model(None, combined)
    assert [args[2] for _, args, _ in commands] == [187.5, 150.0]
    assert [entry["factor"] for entry in cases[1].load_groups] == [1.0, 0.8]
