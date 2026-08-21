"""
ED Cross Bracing → Bolted/Welded Osdag job selection (Slice 3).

Mocks design_pool so tests do not require live osdag_core or a full UI.
Proves Module / Axial / Length for a minimal end-edge force setup.
Does not prove a full Design click in the UI.
"""

from __future__ import annotations

import math
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from osdagbridge.core.utils.common import (
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_BRACING_TYPE,
    KEY_MP_ED_BOTTOM_CHORD,
    KEY_MP_ED_TOP_CHORD,
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
        # One start-edge element spanning G1 node → G2 node.
        if member in ("start_edge", "end_edge"):
            return [101] if member == "start_edge" else []
        return []


def _expected_lengths(spacing_m: float, depth_m: float, bracing_type: str = "X-Bracing"):
    h = depth_m * 0.85
    horiz = spacing_m if bracing_type in ("X", "X-Bracing") else spacing_m / 2.0
    l_d = math.sqrt(horiz**2 + h**2)
    cos_a = math.cos(math.atan2(h, horiz))
    return round(l_d * 1000), round(spacing_m * 1000), cos_a


def _make_bridge(*, connection=None, omit_connection_key: bool = False):
    """Minimal bridge that reaches ED Cross Bracing Osdag job construction."""
    suffix = ".G1G2.E1M1"
    spacing = 1.0
    depth = 1.0
    # Vz_i in N: +10000 → 10 kN tension; -20000 → -20 kN → compression envelopes.
    vz_tens = 10000.0
    vz_comp = -20000.0

    input_dict = {
        KEY_TS_NO_OF_GIRDERS: 2,
        KEY_TS_GIRDER_SPACING: spacing,
        KEY_MP_GIRDER_DEPTH: depth,
        f"{KEY_MP_ED_TYPE}{suffix}": "Cross Bracing",
        f"{KEY_MP_ED_BRACING_TYPE}{suffix}": "X-Bracing",
        f"{KEY_MP_ED_TOP_CHORD}{suffix}": True,
        f"{KEY_MP_ED_BOTTOM_CHORD}{suffix}": True,
    }
    if not omit_connection_key:
        input_dict[f"{KEY_MP_ED_BRACING_CONNECTION}{suffix}"] = connection

    result_data = {
        "girders": {
            "G1": {"nodes": [1], "index": 1},
            "G2": {"nodes": [2], "index": 2},
        },
        "members": {
            "101": (1, 2),
        },
        "loadcases": ["LC1", "LC2", "Envelope ULS"],
        "forces": {
            "LC1": {"101": {"Vz_i": vz_tens}},
            "LC2": {"101": {"Vz_i": vz_comp}},
            "Envelope ULS": {"101": {"Vz_i": 999999.0}},
        },
    }

    bridge = SimpleNamespace(
        result_data=result_data,
        grillage_model=SimpleNamespace(model=_FakeModel()),
        input_dict=input_dict,
        output_dict={},
        end_diaphragm_design_results=None,
        _query_crossbracing_section=lambda _des: None,
        _query_rolled_beam_section=lambda _des: None,
        _print_enddiaphragm_design_results=lambda *_a, **_k: None,
    )
    return bridge, spacing, depth, vz_tens, vz_comp


def _run_ed_jobs(bridge) -> list[dict]:
    from osdagbridge.core.bridge_types.plate_girder.end_diaphragm_design import (
        design_end_diaphragm_members,
    )

    fake = _FakeExecutor()
    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake,
    ):
        design_end_diaphragm_members(bridge)
    return fake.submitted_dicts


def test_ed_cross_bracing_explicit_welded_selects_welded_modules():
    from osdagbridge.core.utils.connect import (
        design_dict_struts_welded,
        design_dict_tension_welded,
    )

    bridge, *_ = _make_bridge(connection="Welded")
    jobs = _run_ed_jobs(bridge)

    assert jobs
    assert {j["Module"] for j in jobs} == {
        design_dict_tension_welded["Module"],
        design_dict_struts_welded["Module"],
    }


def test_ed_cross_bracing_explicit_bolted_selects_bolted_modules():
    from osdagbridge.core.utils.connect import (
        design_dict_struts_bolted,
        design_dict_tension_bolted,
    )

    bridge, *_ = _make_bridge(connection="Bolted")
    jobs = _run_ed_jobs(bridge)

    assert jobs
    assert {j["Module"] for j in jobs} == {
        design_dict_tension_bolted["Module"],
        design_dict_struts_bolted["Module"],
    }


@pytest.mark.parametrize(
    "connection_kwargs",
    [
        {"omit_connection_key": True},
        {"connection": ""},
        {"connection": "not-a-connection"},
        {"connection": None},
    ],
)
def test_ed_cross_bracing_missing_blank_invalid_default_to_bolted(connection_kwargs):
    from osdagbridge.core.utils.connect import (
        design_dict_struts_bolted,
        design_dict_tension_bolted,
    )

    bridge, *_ = _make_bridge(**connection_kwargs)
    jobs = _run_ed_jobs(bridge)

    assert jobs
    assert {j["Module"] for j in jobs} == {
        design_dict_tension_bolted["Module"],
        design_dict_struts_bolted["Module"],
    }
    assert all("Welded" not in j["Module"] for j in jobs)


def test_ed_cross_bracing_axial_and_length_contract():
    """Governing forces and member lengths must match the existing ED formulas."""
    from osdagbridge.core.utils.connect import (
        design_dict_struts_bolted,
        design_dict_tension_bolted,
    )

    bridge, spacing, depth, vz_tens, vz_comp = _make_bridge(connection="Bolted")
    l_diag_mm, l_chord_mm, cos_a = _expected_lengths(spacing, depth, "X-Bracing")

    chord_t = round((vz_tens / 1000.0), 3)
    chord_c = round(abs(vz_comp / 1000.0), 3)
    diag_t = round((vz_tens / 1000.0) / cos_a, 3)
    diag_c = round(abs((vz_comp / 1000.0) / cos_a), 3)

    jobs = _run_ed_jobs(bridge)
    assert len(jobs) == 4

    by_key = {
        (j["Module"], float(j["Load.Axial"]), j["Member.Length"]): j for j in jobs
    }

    assert (
        design_dict_tension_bolted["Module"],
        diag_t,
        str(l_diag_mm),
    ) in by_key
    assert (
        design_dict_struts_bolted["Module"],
        diag_c,
        str(l_diag_mm),
    ) in by_key
    assert (
        design_dict_tension_bolted["Module"],
        chord_t,
        str(l_chord_mm),
    ) in by_key
    assert (
        design_dict_struts_bolted["Module"],
        chord_c,
        str(l_chord_mm),
    ) in by_key


def test_ed_cross_bracing_welded_preserves_axial_and_length():
    from osdagbridge.core.utils.connect import (
        design_dict_struts_welded,
        design_dict_tension_welded,
    )

    bridge, spacing, depth, vz_tens, vz_comp = _make_bridge(connection="Welded")
    l_diag_mm, l_chord_mm, cos_a = _expected_lengths(spacing, depth, "X-Bracing")
    diag_t = round((vz_tens / 1000.0) / cos_a, 3)

    jobs = _run_ed_jobs(bridge)
    modules = {j["Module"] for j in jobs}
    assert design_dict_tension_welded["Module"] in modules
    assert design_dict_struts_welded["Module"] in modules

    axials_lengths = {(float(j["Load.Axial"]), j["Member.Length"]) for j in jobs}
    assert (diag_t, str(l_diag_mm)) in axials_lengths
    assert (round(abs(vz_comp / 1000.0), 3), str(l_chord_mm)) in axials_lengths
