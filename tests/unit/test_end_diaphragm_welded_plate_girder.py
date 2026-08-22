"""
ED Welded Beam → PLATE GIRDER Osdag jobs (Slice 5).

Mocks design_pool so tests do not require live osdag_core design success.
Proves Module / plate mapping / Length mm / Shear/Moment / plate_girder storage.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_rolled_design import (
    envelope_end_diaphragm_vy_mz,
)
from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_welded_design import (
    run_plate_girder_design,
)
from osdagbridge.core.utils.common import (
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_MP_GIRDER_DEPTH,
    KEY_SC_BEARING_LENGTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
)


class _FakeFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _FakeExecutor:
    def __init__(self):
        self.submitted_dicts: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, fn, design_dict):
        self.submitted_dicts.append(design_dict)
        return _FakeFuture({"mock": True})


class _FakeModel:
    def get_element(self, member, options="elements"):
        if member == "start_edge":
            return [101]
        return []


PLATE_GIRDER_MODULE = "PLATE GIRDER"


def test_plate_girder_module_registered_in_connect():
    from osdagbridge.core.utils.connect import (
        MODULE_CLASS_MAP,
        design_dict_plate_girder_welded,
    )
    from osdag_core.design_type.plate_girder.weldedPlateGirder import PlateGirderWelded

    assert design_dict_plate_girder_welded["Module"] == PLATE_GIRDER_MODULE
    assert PLATE_GIRDER_MODULE in MODULE_CLASS_MAP
    assert MODULE_CLASS_MAP[PLATE_GIRDER_MODULE] is PlateGirderWelded


def test_plate_girder_template_has_required_keys():
    from osdagbridge.core.utils.connect import design_dict_plate_girder_welded

    required = {
        "Module",
        "Material",
        "Total.Design_Type",
        "Total.Depth",
        "Web.Thickness",
        "Topflange.Width",
        "TopFlange.Thickness",
        "Bottomflange.Width",
        "BottomFlange.Thickness",
        "Member.Length",
        "Flexure.Type",
        "Support.Width",
        "Web.Philosophy",
        "Torsion.restraint",
        "Warping.restraint",
        "Load.Moment",
        "Load.Shear",
        "Bendingmoment.shape",
        "Optimum.Class",
        "Loading.Condition",
        "Girder.Symmetry",
        "IntermediateStiffener.Spacing",
        "IntermediateStiffener.Thickness",
        "IntermediateStiffener.Thickness.val",
        "LongitudnalStiffener.Data",
        "LongitudnalStiffner.Thickness",
        "LongitudnalStiffner.Thickness.val",
        "Deflection.Max",
    }
    assert required.issubset(design_dict_plate_girder_welded.keys())
    assert design_dict_plate_girder_welded["Total.Design_Type"] == "Customized"
    assert design_dict_plate_girder_welded["Web.Philosophy"] == "Thin Web with ITS"
    assert (
        design_dict_plate_girder_welded["Bendingmoment.shape"]
        == "Uniform Loading with pinned-pinned support"
    )
    assert design_dict_plate_girder_welded["Girder.Symmetry"] == "Symmetrical"


def test_envelope_reuse_unchanged():
    result_data = {
        "loadcases": ["LC1", "Envelope ULS"],
        "forces": {
            "LC1": {
                "101": {"Vy_i": 20000.0, "Vy_j": -8000.0, "Mz_i": 50000.0, "Mz_j": -10000.0},
            },
            "Envelope ULS": {
                "101": {"Vy_i": 1e9, "Vy_j": 0.0, "Mz_i": 1e9, "Mz_j": 0.0},
            },
        },
    }
    vy_kN, mz_kNm = envelope_end_diaphragm_vy_mz(result_data, ["101"])
    assert vy_kN == 20.0
    assert mz_kNm == 50.0


def test_run_plate_girder_design_submits_customized_job():
    fake = _FakeExecutor()
    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake,
    ):
        result = run_plate_girder_design(
            vy_kN=12.5,
            mz_kNm=34.0,
            span_m=2.5,
            support_width_mm=400.0,
            total_depth_mm=300.0,
            web_thickness_mm=8.0,
            top_flange_width_mm=150.0,
            top_flange_thickness_mm=10.0,
            bottom_flange_width_mm=150.0,
            bottom_flange_thickness_mm=10.0,
        )

    assert result == {"mock": True}
    assert len(fake.submitted_dicts) == 1
    job = fake.submitted_dicts[0]
    assert job["Module"] == PLATE_GIRDER_MODULE
    assert job["Total.Design_Type"] == "Customized"
    assert float(job["Total.Depth"]) == 300.0
    assert float(job["Web.Thickness"]) == 8.0
    assert float(job["Topflange.Width"]) == 150.0
    assert float(job["TopFlange.Thickness"]) == 10.0
    assert float(job["Bottomflange.Width"]) == 150.0
    assert float(job["BottomFlange.Thickness"]) == 10.0
    assert float(job["Member.Length"]) == 2500.0  # 2.5 m → mm
    assert float(job["Support.Width"]) == 400.0
    assert float(job["Load.Shear"]) == 12.5
    assert float(job["Load.Moment"]) == 34.0


def test_run_plate_girder_skips_without_bearing_length():
    fake = _FakeExecutor()
    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake,
    ):
        result = run_plate_girder_design(
            vy_kN=12.5,
            mz_kNm=34.0,
            span_m=2.5,
            support_width_mm=0.0,
            total_depth_mm=300.0,
            web_thickness_mm=8.0,
            top_flange_width_mm=150.0,
            top_flange_thickness_mm=10.0,
            bottom_flange_width_mm=150.0,
            bottom_flange_thickness_mm=10.0,
        )
    assert result is None
    assert fake.submitted_dicts == []


def test_ed_welded_branch_reaches_design_pool_and_preserves_props():
    """Integration through design_end_diaphragm_members Welded branch."""
    from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_design import (
        design_end_diaphragm_members,
    )

    suffix = ".G1G2.E1M1"
    spacing = 2.0
    input_dict = {
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_GIRDER_SPACING: spacing,
        KEY_MP_GIRDER_DEPTH: 1.0,
        KEY_SC_BEARING_LENGTH: "400.00",
        f"{KEY_MP_ED_TYPE}{suffix}": "Welded Beam",
        f"{KEY_MP_ED_TOTAL_DEPTH}{suffix}": "300",
        f"{KEY_MP_ED_WEB_THICKNESS}{suffix}": "8",
        f"{KEY_MP_ED_TOP_FLANGE_WIDTH}{suffix}": "150",
        f"{KEY_MP_ED_TOP_FLANGE_THICKNESS}{suffix}": "10",
        f"{KEY_MP_ED_BOTTOM_FLANGE_WIDTH}{suffix}": "150",
        f"{KEY_MP_ED_BOTTOM_FLANGE_THICKNESS}{suffix}": "10",
    }
    result_data = {
        "girders": {
            "G1": {"nodes": [1], "index": 1},
            "G2": {"nodes": [2], "index": 2},
        },
        "members": {"101": (1, 2)},
        "loadcases": ["LC1", "Envelope SLS"],
        "forces": {
            "LC1": {
                "101": {
                    "Vy_i": 20000.0,
                    "Vy_j": -8000.0,
                    "Mz_i": 50000.0,
                    "Mz_j": -10000.0,
                },
            },
            "Envelope SLS": {
                "101": {
                    "Vy_i": 1e9,
                    "Vy_j": 0.0,
                    "Mz_i": 1e9,
                    "Mz_j": 0.0,
                },
            },
        },
    }
    bridge = SimpleNamespace(
        result_data=result_data,
        grillage_model=SimpleNamespace(model=_FakeModel()),
        input_dict=input_dict,
        output_dict={},
        end_diaphragm_design_results=None,
        _query_rolled_beam_section=lambda _des: None,
        _query_crossbracing_section=lambda _des: None,
        _print_enddiaphragm_design_results=lambda *_a, **_k: None,
    )

    fake = _FakeExecutor()
    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake,
    ):
        pair_designs = design_end_diaphragm_members(bridge)

    assert fake.submitted_dicts, "Plate girder job never reached design_pool"
    job = fake.submitted_dicts[0]
    assert job["Module"] == PLATE_GIRDER_MODULE
    assert job["Total.Design_Type"] == "Customized"
    assert float(job["Total.Depth"]) == 300.0
    assert float(job["Web.Thickness"]) == 8.0
    assert float(job["Topflange.Width"]) == 150.0
    assert float(job["TopFlange.Thickness"]) == 10.0
    assert float(job["Bottomflange.Width"]) == 150.0
    assert float(job["BottomFlange.Thickness"]) == 10.0
    assert float(job["Member.Length"]) == spacing * 1000.0
    assert float(job["Support.Width"]) == 400.0
    assert float(job["Load.Shear"]) == 20.0
    assert float(job["Load.Moment"]) == 50.0
    assert pair_designs["G1-G2"]["plate_girder"] == {"mock": True}

    # Existing KEY_TD_ED_PROP_* population preserved (depth mm → H in m)
    h_key = "transverse_member_design.ed.section_properties.end_diaphragm.G1G2.H"
    assert h_key in bridge.output_dict
    assert abs(float(bridge.output_dict[h_key]) - 0.3) < 1e-9
