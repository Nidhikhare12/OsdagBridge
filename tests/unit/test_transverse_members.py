"""
Transverse member mapping / extraction in results_data.py (Task III).

A small synthetic grillage is used so the test needs no OpenSees run:

    z = 0.0   edge beam      e - e - e
    z = 1.0   girder G1      o - o - o
    z = 3.0   girder G2      o - o - o
    z = 4.0   edge beam      e - e - e
              x =            0   5   10

Transverse grid lines at x = 0, 5, 10 connect all four longitudinal lines.
"""

import numpy as np
import pytest
import xarray as xr

from osdagbridge.core.bridge_types.plate_girder.results_data import (
    classify_grillage_members,
    build_transverse_lines,
    extract_transverse_results,
    member_local_axes,
    OSP_GROUP_START_EDGE,
    OSP_GROUP_END_EDGE,
    OSP_GROUP_TRANSVERSE_SLAB,
)

LINE_Z = [0.0, 1.0, 3.0, 4.0]
XS = [0.0, 5.0, 10.0]
EDGE_DIST = 1.0


def _grillage():
    nodes, members = {}, {}
    nid = 1
    grid = {}
    for z in LINE_Z:
        for x in XS:
            nodes[nid] = [x, 0.0, z]
            grid[(x, z)] = nid
            nid += 1
    eid = 1
    longitudinal = []
    for z in LINE_Z:
        for xa, xb in zip(XS, XS[1:]):
            members[eid] = [grid[(xa, z)], grid[(xb, z)]]
            longitudinal.append(eid)
            eid += 1
    groups = {OSP_GROUP_START_EDGE: [], OSP_GROUP_END_EDGE: [], OSP_GROUP_TRANSVERSE_SLAB: []}
    for x in XS:
        for za, zb in zip(LINE_Z, LINE_Z[1:]):
            members[eid] = [grid[(x, za)], grid[(x, zb)]]
            key = (OSP_GROUP_START_EDGE if x == XS[0]
                   else OSP_GROUP_END_EDGE if x == XS[-1]
                   else OSP_GROUP_TRANSVERSE_SLAB)
            groups[key].append(eid)
            eid += 1
    return nodes, members, groups, longitudinal


def _dataset(nodes, members):
    """Results for one load case, shaped like the xarray dataset (per-variable Component axis)."""
    force_comps = ["Vx_i", "Vx_j", "Vy_i", "Vy_j", "Vz_i", "Vz_j",
                   "Mx_i", "Mx_j", "My_i", "My_j", "Mz_i", "Mz_j"]
    elems = sorted(members)
    forces = np.zeros((len(elems), len(force_comps)))
    for row, e in enumerate(elems):
        forces[row, force_comps.index("Vy_i")] = 1000.0 * e        # N
        forces[row, force_comps.index("Vy_j")] = -1000.0 * e
        forces[row, force_comps.index("Mx_i")] = 2000.0 * e        # N m
        forces[row, force_comps.index("Mx_j")] = 500.0 * e
    node_ids = sorted(nodes)
    disp_comps = ["x", "y", "z", "theta_x", "theta_y", "theta_z"]
    disp = np.zeros((len(node_ids), len(disp_comps)))
    for row, n in enumerate(node_ids):
        disp[row, disp_comps.index("y")] = -0.001 * n               # m, downward
    return {
        "forces": xr.DataArray(forces, dims=("Element", "Component"),
                               coords={"Element": elems, "Component": force_comps}),
        "displacements": xr.DataArray(disp, dims=("Node", "Component"),
                                      coords={"Node": node_ids, "Component": disp_comps}),
    }


@pytest.fixture
def grillage():
    return _grillage()


def test_partition_with_groups(grillage):
    nodes, members, groups, longitudinal = grillage
    cm = classify_grillage_members(nodes, members, EDGE_DIST, groups)
    assert sorted(cm["longitudinal"]) == sorted(longitudinal)
    # One girder-to-girder element per transverse line (G1-G2); the edge-beam
    # strips are deck overhang, not diaphragms / bracings.
    assert len(cm["end_diaphragms"]) == 2
    assert len(cm["cross_bracings"]) == 1
    assert len(cm["deck_transverse"]) == 6
    all_tags = (cm["longitudinal"] + cm["end_diaphragms"]
                + cm["cross_bracings"] + cm["deck_transverse"])
    assert sorted(all_tags) == sorted(members)          # complete, disjoint partition
    assert set(cm["end_diaphragms"]) <= set(groups[OSP_GROUP_START_EDGE] + groups[OSP_GROUP_END_EDGE])
    assert set(cm["cross_bracings"]) <= set(groups[OSP_GROUP_TRANSVERSE_SLAB])


def test_geometry_fallback_matches_groups(grillage):
    nodes, members, groups, _ = grillage
    with_groups = classify_grillage_members(nodes, members, EDGE_DIST, groups)
    geometric = classify_grillage_members(nodes, members, EDGE_DIST, None)
    for key in ("longitudinal", "end_diaphragms", "cross_bracings", "deck_transverse"):
        assert sorted(with_groups[key]) == sorted(geometric[key])


def test_string_keyed_input_is_accepted(grillage):
    nodes, members, groups, _ = grillage
    s_nodes = {str(k): v for k, v in nodes.items()}
    s_members = {str(k): v for k, v in members.items()}
    cm = classify_grillage_members(s_nodes, s_members, EDGE_DIST, groups)
    assert len(cm["end_diaphragms"]) == 2


def test_lines_are_named_and_ordered(grillage):
    nodes, members, groups, _ = grillage
    lines = build_transverse_lines(nodes, members, EDGE_DIST, groups)
    assert [ln["name"] for ln in lines] == ["ED1", "CB1", "ED2"]
    assert [ln["x"] for ln in lines] == [0.0, 5.0, 10.0]


def test_force_extraction_and_sign_convention(grillage):
    nodes, members, groups, _ = grillage
    ds = _dataset(nodes, members)
    lines = extract_transverse_results(ds, "Fy", nodes, members, EDGE_DIST, groups)
    seg = lines[0]["segments"][0]
    e = seg["element"]
    # Vertical shear: local y == global Y. values = (f_start, -f_end) in kN,
    # the same convention as the girder SFD.
    assert seg["values"] == pytest.approx((1.0 * e, 1.0 * e))


def test_moments_are_rotated_into_member_local_axes(grillage):
    nodes, members, groups, _ = grillage
    ds = _dataset(nodes, members)
    # The synthetic members run along +Z, so local x = +Z, y = +Y and
    # z = x × y = -X: a moment about GLOBAL X is the member's bending moment
    # Mz (sign flipped) and it carries no torsion Tx (= moment about global Z).
    mz = extract_transverse_results(ds, "Mz", nodes, members, EDGE_DIST, groups)
    seg = mz[0]["segments"][0]
    e = seg["element"]
    assert seg["values"] == pytest.approx((-2.0 * e, 0.5 * e))
    assert mz[0]["max"] == pytest.approx(0.5 * e)
    tx = extract_transverse_results(ds, "Mx", nodes, members, EDGE_DIST, groups)
    assert all(v == 0.0 for ln in tx for sg in ln["segments"] for v in sg["values"])


def test_result_does_not_depend_on_element_node_order(grillage):
    nodes, members, groups, _ = grillage
    ds = _dataset(nodes, members)
    ref = extract_transverse_results(ds, "Mz", nodes, members, EDGE_DIST, groups)
    # Reverse the node order of one element and swap its end forces to match
    # (the same physical member, defined from the other end).
    e = ref[0]["segments"][0]["element"]
    flipped = dict(members)
    flipped[e] = list(reversed(members[e]))
    forces = ds["forces"].copy()
    for a in ("Vx", "Vy", "Vz", "Mx", "My", "Mz"):
        i_val = float(forces.sel(Element=e, Component=f"{a}_i"))
        j_val = float(forces.sel(Element=e, Component=f"{a}_j"))
        forces.loc[dict(Element=e, Component=f"{a}_i")] = j_val
        forces.loc[dict(Element=e, Component=f"{a}_j")] = i_val
    ds_flipped = dict(ds, forces=forces)
    got = extract_transverse_results(ds_flipped, "Mz", nodes, flipped, EDGE_DIST, groups)
    assert got[0]["segments"][0]["values"] == pytest.approx(ref[0]["segments"][0]["values"])
    assert got[0]["segments"][0]["nodes"] == ref[0]["segments"][0]["nodes"]


def test_local_axes_of_a_girder_are_the_global_axes():
    assert member_local_axes([0, 0, 0], [5, 0, 0]) == pytest.approx(np.eye(3))


def test_local_axes_of_a_skewed_member_are_orthonormal():
    axes = member_local_axes([0, 0, 0], [1.0, 0, 2.0])
    assert axes @ axes.T == pytest.approx(np.eye(3))
    assert axes[1] == pytest.approx([0, 1, 0])           # y stays vertical
    assert np.linalg.det(axes) == pytest.approx(1.0)     # right-handed


def test_displacement_extraction_reports_sag_in_mm(grillage):
    nodes, members, groups, _ = grillage
    ds = _dataset(nodes, members)
    lines = extract_transverse_results(ds, "Dy", nodes, members, EDGE_DIST, groups)
    seg = lines[1]["segments"][0]
    n1, n2 = seg["nodes"]
    assert seg["values"] == pytest.approx((1.0 * n1, 1.0 * n2))     # -(-0.001 n) m -> n mm


def test_unknown_key_raises(grillage):
    nodes, members, groups, _ = grillage
    with pytest.raises(KeyError):
        extract_transverse_results(_dataset(nodes, members), "Qq", nodes, members,
                                   EDGE_DIST, groups)
