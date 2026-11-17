"""
test_transverse_plotting.py
---------------------------
Unit tests for Transverse Member Result Plotting (Task 3).
Covers:
1. Member classification in results_data (classify_transverse_members).
2. Transverse station grouping and width sorting (_find_transverse_lines).
3. Polyline building across bridge width (_build_transverse_polyline).
4. SFD, BMD, and Deflection figure generation for End Diaphragm and Intermediate Cross Bracing.
5. Summary data dictionary population for the HUD overlay.
"""

from unittest.mock import MagicMock
import numpy as np
import pytest

from osdagbridge.core.utils.common import (
    KEY_DISP_END_DIAPHRAGM,
    KEY_DISP_INTERMEDIATE_CROSS_BRACING,
)
from osdagbridge.core.bridge_types.plate_girder.results_data import (
    classify_transverse_members,
)
from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
    _find_transverse_lines,
    _build_transverse_polyline,
    build_figure_bmd,
    build_figure_sfd,
    build_figure_deflection,
)


# ==============================================================================
# Fixtures & Sample Grillage Geometry
# ==============================================================================

@pytest.fixture
def sample_mesh():
    """
    Construct a 3-girder bridge model (Span L = 20m, Width B = 6m, Girders at Z=0, 3, 6):
    - Longitudinal elements at Z=0, Z=3, Z=6.
    - End Diaphragm at X = 0.0 (elements 101, 102).
    - Intermediate Cross Bracing at X = 10.0 (elements 201, 202).
    - End Diaphragm at X = 20.0 (elements 301, 302).
    """
    nodes = {
        # X=0.0 (Start support)
        1: [0.0, 0.0, 0.0],
        2: [0.0, 0.0, 3.0],
        3: [0.0, 0.0, 6.0],

        # X=10.0 (Mid-span)
        4: [10.0, 0.0, 0.0],
        5: [10.0, 0.0, 3.0],
        6: [10.0, 0.0, 6.0],

        # X=20.0 (End support)
        7: [20.0, 0.0, 0.0],
        8: [20.0, 0.0, 3.0],
        9: [20.0, 0.0, 6.0],
    }

    members = {
        # Longitudinal girder G1 (Z=0.0)
        11: [1, 4],
        12: [4, 7],

        # Longitudinal girder G2 (Z=3.0)
        21: [2, 5],
        22: [5, 8],

        # Longitudinal girder G3 (Z=6.0)
        31: [3, 6],
        32: [6, 9],

        # Transverse: Start End Diaphragm (X=0.0)
        101: [1, 2],
        102: [2, 3],

        # Transverse: Mid-span Cross Bracing (X=10.0)
        201: [4, 5],
        202: [5, 6],

        # Transverse: End End Diaphragm (X=20.0)
        301: [7, 8],
        302: [8, 9],
    }

    groups = {
        "start_edge": [101, 102],
        "end_edge": [301, 302],
        "transverse_slab": [201, 202],
    }

    return nodes, members, groups


@pytest.fixture
def mock_dataset():
    """
    Create a mock xarray-like Dataset for testing plot generators.
    """
    ds = MagicMock()
    ds.__getitem__ = MagicMock()

    # Mock Component values
    component_mock = MagicMock()
    component_mock.values = np.array(["Vx_i", "Vx_j", "Vy_i", "Vy_j", "Vz_i", "Vz_j",
                                      "Mx_i", "Mx_j", "My_i", "My_j", "Mz_i", "Mz_j",
                                      "dx", "dy", "dz"])
    ds.__getitem__.side_effect = lambda k: {
        "Component": component_mock,
        "forces": _create_mock_data_array(force_val=150000.0),
        "displacements": _create_mock_data_array(disp_val=-0.012, is_disp=True),
    }.get(k, component_mock)

    return ds


def _create_mock_data_array(force_val=0.0, disp_val=0.0, is_disp=False):
    da = MagicMock()
    da.coords = {
        "Component": MagicMock(values=np.array(["Vx_i", "Vx_j", "Vy_i", "Vy_j", "Mz_i", "Mz_j", "dy"])),
        "Element": MagicMock(values=np.array([11, 12, 21, 22, 31, 32, 101, 102, 201, 202, 301, 302])),
        "Node": MagicMock(values=np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])),
    }
    sel_mock = MagicMock()
    sel_mock.values = np.array(disp_val if is_disp else force_val)
    da.sel.return_value = sel_mock
    return da


# ==============================================================================
# 1. Classification Tests (results_data.py)
# ==============================================================================

def test_classify_transverse_members_via_groups(sample_mesh):
    """Verify group-based extraction routes through start_edge, end_edge, and transverse_slab."""
    nodes, members, groups = sample_mesh
    classified = classify_transverse_members(nodes, members, groups=groups)

    assert set(classified["end_diaphragm"]) == {101, 102, 301, 302}
    assert set(classified["intermediate_cross_bracing"]) == {201, 202}
    assert set(classified["all"]) == {101, 102, 201, 202, 301, 302}


def test_classify_transverse_members_geometric_fallback(sample_mesh):
    """Verify geometric coordinate classification when groups are None."""
    nodes, members, _ = sample_mesh
    classified = classify_transverse_members(nodes, members, groups=None)

    assert set(classified["end_diaphragm"]) == {101, 102, 301, 302}
    assert set(classified["intermediate_cross_bracing"]) == {201, 202}
    assert set(classified["all"]) == {101, 102, 201, 202, 301, 302}


def test_classify_transverse_members_empty():
    """Verify empty input returns empty classification lists without crashing."""
    classified = classify_transverse_members({}, {})
    assert classified == {"all": [], "end_diaphragm": [], "intermediate_cross_bracing": []}


# ==============================================================================
# 2. Line Grouping & Sorting Tests (plot_generator.py)
# ==============================================================================

def test_find_transverse_lines_end_diaphragm(sample_mesh):
    """Verify _find_transverse_lines returns only support lines for End Diaphragm."""
    nodes, members, _ = sample_mesh
    lines = _find_transverse_lines(nodes, members, member_type=KEY_DISP_END_DIAPHRAGM)

    # Stations should be 0.0 and 20.0
    assert list(lines.keys()) == [0.0, 20.0]
    assert lines[0.0] == [101, 102]
    assert lines[20.0] == [301, 302]


def test_find_transverse_lines_intermediate_cross_bracing(sample_mesh):
    """Verify _find_transverse_lines returns only mid-span line for Intermediate Cross Bracing."""
    nodes, members, _ = sample_mesh
    lines = _find_transverse_lines(nodes, members, member_type=KEY_DISP_INTERMEDIATE_CROSS_BRACING)

    # Station should be 10.0 only
    assert list(lines.keys()) == [10.0]
    assert lines[10.0] == [201, 202]


def test_find_transverse_lines_sorted_across_z(sample_mesh):
    """Verify elements within each transverse line are sorted ascending by Z-coordinate."""
    nodes, members, _ = sample_mesh
    # Deliberately reverse member definition order to test sorting
    reversed_members = dict(members)
    reversed_members[101], reversed_members[102] = reversed_members[102], reversed_members[101]

    lines = _find_transverse_lines(nodes, reversed_members, member_type=KEY_DISP_END_DIAPHRAGM)
    # Element 101 connects Z=0 to Z=3; Element 102 connects Z=3 to Z=6
    # Element 101 must precede Element 102 after sorting
    assert lines[0.0] == [101, 102]


# ==============================================================================
# 3. Polyline Builder Tests (plot_generator.py)
# ==============================================================================

def test_build_transverse_polyline(sample_mesh, mock_dataset):
    """Verify _build_transverse_polyline extracts coordinates and forces across width."""
    nodes, members, _ = sample_mesh
    elems = [101, 102]

    xs, ys, zs, vals, node_ids = _build_transverse_polyline(
        elems, members, nodes, "Mz_i", "Mz_j", mock_dataset
    )

    # 2 elements in series give 3 polyline points (nodes 1, 2, 3)
    assert len(xs) == 3
    assert len(zs) == 3
    assert len(vals) == 3
    assert node_ids == [1, 2, 3]
    # Coordinates along X should be 0.0
    assert np.allclose(xs, [0.0, 0.0, 0.0])
    # Coordinates along Z should be 0.0, 3.0, 6.0
    assert np.allclose(zs, [0.0, 3.0, 6.0])
    # Force values converted N -> kN (150000 N -> 150 kN)
    assert np.allclose(vals, [150.0, 150.0, 150.0])


# ==============================================================================
# 4. Figure Generation Tests (BMD, SFD, Deflection)
# ==============================================================================

def test_build_figure_bmd_end_diaphragm(sample_mesh, mock_dataset):
    """Verify build_figure_bmd renders for End Diaphragm and populates summary_data."""
    nodes, members, _ = sample_mesh
    fig, summary = build_figure_bmd(
        mock_dataset, "Mz", nodes, members, selected_girder=KEY_DISP_END_DIAPHRAGM
    )

    assert fig is not None
    assert len(summary) == 2  # 2 end diaphragms (X=0.00m and X=20.00m)
    assert any("End Diaph (X=0.00m)" in k for k in summary)
    assert any("End Diaph (X=20.00m)" in k for k in summary)


def test_build_figure_bmd_intermediate_cross_bracing(sample_mesh, mock_dataset):
    """Verify build_figure_bmd renders for Intermediate Cross Bracing."""
    nodes, members, _ = sample_mesh
    fig, summary = build_figure_bmd(
        mock_dataset, "Mz", nodes, members, selected_girder=KEY_DISP_INTERMEDIATE_CROSS_BRACING
    )

    assert fig is not None
    assert len(summary) == 1  # 1 intermediate cross bracing (X=10.00m)
    assert any("Cross Bracing (X=10.00m)" in k for k in summary)


def test_build_figure_sfd_transverse_members(sample_mesh, mock_dataset):
    """Verify build_figure_sfd renders for transverse members."""
    nodes, members, _ = sample_mesh
    fig, summary = build_figure_sfd(
        mock_dataset, "Fy", nodes, members, selected_girder=KEY_DISP_END_DIAPHRAGM
    )

    assert fig is not None
    assert len(summary) == 2


def test_build_figure_deflection_transverse_members(sample_mesh, mock_dataset):
    """Verify build_figure_deflection renders for transverse members."""
    nodes, members, _ = sample_mesh
    fig, summary = build_figure_deflection(
        mock_dataset, "Dy", nodes, members, selected_girder=KEY_DISP_INTERMEDIATE_CROSS_BRACING
    )

    assert fig is not None
    assert len(summary) == 1
