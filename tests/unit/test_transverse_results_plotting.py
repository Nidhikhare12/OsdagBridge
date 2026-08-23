import pytest
import numpy as np
import pandas as pd
import xarray as xr
from osdagbridge.core.utils.common import (
    KEY_ANALYSIS_MEMBER,
    KEY_OUTPUT_DOCK_MEMBER_ID,
    KEY_TS_NO_OF_GIRDERS,
    DISP_TRANSVERSE_MEMBERS,
)
from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
    _get_bg_nodes_members,
    _find_transverse_elements,
)
from osdagbridge.core.bridge_types.plate_girder.analysis_results import PlateGirderAnalysisResults
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.desktop.ui.docks.output_dock import OutputDock
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication([])


def test_find_transverse_elements_and_bg_filter():
    nodes = {
        1: [0.0, 0.0, 0.0],
        2: [10.0, 0.0, 0.0],
        3: [0.0, 0.0, 3.0],
        4: [10.0, 0.0, 3.0],
    }
    members = {
        101: [1, 2],  # Longitudinal (along X at Z=0)
        102: [3, 4],  # Longitudinal (along X at Z=3)
        103: [1, 3],  # Transverse (along Z at X=0)
        104: [2, 4],  # Transverse (along Z at X=10)
    }

    t_elems = _find_transverse_elements(nodes, members)
    assert 103 in t_elems
    assert 104 in t_elems
    assert 101 not in t_elems
    assert 102 not in t_elems

    bg_nodes, bg_members = _get_bg_nodes_members(nodes, members, 0.0, DISP_TRANSVERSE_MEMBERS, [])
    assert 103 in bg_members
    assert 104 in bg_members
    assert 101 not in bg_members
    assert 102 not in bg_members


def test_output_dock_transverse_member_in_dropdown():
    backend = PlateGirderBridge()
    backend.input_dict = {KEY_TS_NO_OF_GIRDERS: 3}
    dock = OutputDock(backend=backend)
    dock.refresh_member_dropdown()

    combo_analysis = dock._w(KEY_ANALYSIS_MEMBER)
    assert combo_analysis is not None
    items = [combo_analysis.itemText(i) for i in range(combo_analysis.count())]
    assert "All" in items
    assert "G1" in items
    assert "G2" in items
    assert "G3" in items
    assert DISP_TRANSVERSE_MEMBERS in items


def test_plate_girder_analysis_results_transverse_members():
    # Construct synthetic dataset with longitudinal and transverse elements
    # Nodes: 1 (0,0,0), 2 (10,0,0), 3 (0,0,3), 4 (10,0,3)
    # Elements: 101 (1->2), 102 (3->4), 103 (1->3), 104 (2->4)
    nodes = [1, 2, 3, 4]
    elements = [101, 102, 103, 104]
    loadcases = ["LC1"]
    components_f = ["Mz_i", "Mz_j", "Vy_i", "Vy_j", "Fx_i", "Fx_j"]
    components_d = ["x", "y", "z"]

    forces_data = np.ones((len(loadcases), len(elements), len(components_f))) * 50000.0  # 50 kN/kNm in N/Nm
    disp_data = np.ones((len(loadcases), len(nodes), len(components_d))) * 0.005        # 5 mm

    forces_da = xr.DataArray(
        forces_data,
        coords={"Loadcase": loadcases, "Element": elements, "Component": components_f},
        dims=["Loadcase", "Element", "Component"],
    )
    disp_da = xr.DataArray(
        disp_data,
        coords={"Loadcase": loadcases, "Node": nodes, "Component": components_d},
        dims=["Loadcase", "Node", "Component"],
    )

    ds = xr.Dataset(
        data_vars={
            "forces": forces_da,
            "displacements": disp_da,
        }
    )

    # Subclass or mock connectivity
    class MockAnalysisResults(PlateGirderAnalysisResults):
        def __init__(self, ds):
            self.ds = ds
            self.edge_dist = 0.0

        def build_grillage_connectivity(self):
            nodes_dict = {
                1: (0.0, 0.0, 0.0),
                2: (10.0, 0.0, 0.0),
                3: (0.0, 0.0, 3.0),
                4: (10.0, 0.0, 3.0),
            }
            elems_dict = {
                101: (1, 2),
                102: (3, 4),
                103: (1, 3),
                104: (2, 4),
            }
            adj = {1: [2, 3], 2: [1, 4], 3: [1, 4], 4: [2, 3]}
            return nodes_dict, elems_dict, adj

    res = MockAnalysisResults(ds)
    t_map = res.build_transverse_members()
    assert 103 in t_map["elements"]
    assert 104 in t_map["elements"]
    assert 101 not in t_map["elements"]
    assert 102 not in t_map["elements"]

    df_forces = res._get_forces_df("LC1", "Transverse Members", "Mz_i")
    assert not df_forces.empty
    assert len(df_forces) == 2
    assert "Mz_i (kNm)" in df_forces.columns
    assert df_forces["Mz_i (kNm)"].iloc[0] == 50.0

    df_disp = res._get_displacements_df("LC1", "Transverse Members", "dy")
    assert not df_disp.empty
    assert "dy" in df_disp.columns
    assert df_disp["dy"].iloc[0] == 5.0

    df_coords = res._get_node_coords_df("Transverse Members")
    assert not df_coords.empty
    assert "Z (m)" in df_coords.columns
    assert len(df_coords) == 4
