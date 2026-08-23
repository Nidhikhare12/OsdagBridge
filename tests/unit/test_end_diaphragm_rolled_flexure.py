"""
ED Rolled Beam → Flexure simply-supported Osdag jobs (Slice 4).

Mocks design_pool so tests do not require live osdag_core design success.
Proves Module / Shear / Moment / Length and governing Vy/Mz envelope.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_rolled_design import (
    envelope_end_diaphragm_vy_mz,
    run_simply_supported_design,
)
from osdagbridge.core.utils.common import (
    KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_TYPE,
    KEY_MP_GIRDER_DEPTH,
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


FLEXURE_MODULE = "Flexural Members - Simply Supported"


def test_flexure_module_registered_in_connect():
    from osdagbridge.core.utils.connect import (
        MODULE_CLASS_MAP,
        design_dict_flexure_simply_supported,
    )

    assert design_dict_flexure_simply_supported["Module"] == FLEXURE_MODULE
    assert FLEXURE_MODULE in MODULE_CLASS_MAP
    assert design_dict_flexure_simply_supported["Loading.Condition"] == "Normal"
    assert design_dict_flexure_simply_supported["Torsion.restraint"] == "Fully Restrained"
    assert (
        design_dict_flexure_simply_supported["Warping.restraint"]
        == "Both flanges fully restrained"
    )


def test_envelope_skips_envelope_lc_and_takes_max_abs():
    result_data = {
        "loadcases": ["LC1", "LC2", "Envelope ULS"],
        "forces": {
            "LC1": {
                "101": {"Vy_i": 10000.0, "Vy_j": -5000.0, "Mz_i": 20000.0, "Mz_j": -10000.0},
            },
            "LC2": {
                "101": {"Vy_i": -30000.0, "Vy_j": 1000.0, "Mz_i": 5000.0, "Mz_j": -40000.0},
            },
            # Would win if not skipped (N / N·m)
            "Envelope ULS": {
                "101": {"Vy_i": 999999.0, "Vy_j": 0.0, "Mz_i": 999999.0, "Mz_j": 0.0},
            },
        },
    }
    vy_kN, mz_kNm = envelope_end_diaphragm_vy_mz(result_data, ["101"])
    # LC1: max(|10k|,|5k|)=10k N → 10 kN; max(|20k|,|10k|)=20k N·m → 20 kNm
    # LC2: max(|30k|,|1k|)=30k N → 30 kN; max(|5k|,|40k|)=40k → 40 kNm
    assert vy_kN == 30.0
    assert mz_kNm == 40.0


def test_envelope_uses_my_vz_when_mz_vy_absent():
    """Transverse ED members often store flexure/shear in My / Vz."""
    result_data = {
        "loadcases": ["LC1"],
        "forces": {
            "LC1": {
                "101": {"Vz_i": 20000.0, "Vz_j": -8000.0, "My_i": 13759.0, "My_j": 0.0},
            },
        },
    }
    vy_kN, mz_kNm = envelope_end_diaphragm_vy_mz(result_data, ["101"])
    assert vy_kN == 20.0
    assert mz_kNm == 13.759


def test_resolve_ed_flexure_demands_estimates_moment_when_analysis_mz_zero():
    from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_rolled_design import (
        resolve_ed_flexure_demands,
    )

    vy, mz = resolve_ed_flexure_demands(85.761, 0.0, 2.225)
    assert vy == 85.761
    assert mz == round(85.761 * 2.225 / 4.0, 3)

    vy2, mz2 = resolve_ed_flexure_demands(85.761, 13.7, 2.225)
    assert (vy2, mz2) == (85.761, 13.7)


def test_run_simply_supported_design_submits_flexure_job():
    fake = _FakeExecutor()
    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake,
    ):
        result = run_simply_supported_design(
            vy_kN=12.5,
            mz_kNm=34.0,
            span_m=2.5,
            section_designation="ISMB 300",
        )

    assert result == {"mock": True}
    assert len(fake.submitted_dicts) == 1
    job = fake.submitted_dicts[0]
    assert job["Module"] == FLEXURE_MODULE
    assert float(job["Load.Shear"]) == 12.5
    assert float(job["Load.Moment"]) == 34.0
    assert job["Member.Length"] == "2.5"
    assert job["Member.Designation"] == ["ISMB 300"]


def test_ed_rolled_branch_reaches_design_pool_with_expected_contract():
    """Integration through design_end_diaphragm_members Rolled branch."""
    from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_design import (
        design_end_diaphragm_members,
    )

    suffix = ".G1G2.E1M1"
    spacing = 2.0
    input_dict = {
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_GIRDER_SPACING: spacing,
        KEY_MP_GIRDER_DEPTH: 1.0,
        f"{KEY_MP_ED_TYPE}{suffix}": "Rolled Beam",
        f"{KEY_MP_ED_IS_SECTION}{suffix}": "ISMB 250",
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
        _query_rolled_beam_section=lambda _des: {
            "H": 0.25, "B": 0.125, "tw": 0.006, "tF": 0.008,
            "M": 37.0, "A": 47.0, "Iz": 4000.0, "Iv": 200.0,
            "rz": 9.0, "rv": 2.0, "Zz": 300.0, "Zv": 50.0,
            "Zuz": 350.0, "Zuv": 60.0,
        },
        _query_crossbracing_section=lambda _des: None,
        _print_enddiaphragm_design_results=lambda *_a, **_k: None,
    )

    fake = _FakeExecutor()
    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake,
    ):
        pair_designs = design_end_diaphragm_members(bridge)

    assert fake.submitted_dicts, "Flexure job never reached design_pool"
    job = fake.submitted_dicts[0]
    assert job["Module"] == FLEXURE_MODULE
    assert float(job["Load.Shear"]) == 20.0   # max(20k, 8k) N → 20 kN
    assert float(job["Load.Moment"]) == 50.0  # max(50k, 10k) N·m → 50 kNm
    assert job["Member.Length"] == str(spacing)
    assert job["Member.Designation"] == ["ISMB 250"]

    assert pair_designs["G1-G2"]["simply_supported"] == {"mock": True}
    assert bridge.output_dict.get(
        "member_properties.end_diaphragm_details.is_section.G1G2"
    ) == "ISMB 250" or any(
        "is_section" in k and bridge.output_dict[k] == "ISMB 250"
        for k in bridge.output_dict
    )
