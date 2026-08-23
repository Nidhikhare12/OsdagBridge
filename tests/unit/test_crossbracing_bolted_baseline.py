"""
Regression baseline for Intermediate Cross Bracing → Bolted Osdag jobs.

Purpose
-------
Capture the *current* Bolted job contract (Module string, Axial, Length)
before module splits / Welded wiring. Mock the process pool so tests do not
require a full GUI, grillage model, or live osdag_core design run.

Limitation (learning.mdc §15)
-----------------------------
Green tests here prove the Bolted *job-list contract* for a frozen forces_dict.
They are not proof that a full Design click in the UI is correct.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "crossbracing_forces_dict_bolted_min.json"
)


class _FakeFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _FakeExecutor:
    """Minimal stand-in for ProcessPoolExecutor used by run_member_designs."""

    def __init__(self):
        self.submitted_dicts: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, fn, design_dict):
        self.submitted_dicts.append(design_dict)
        return _FakeFuture({"mock": True})


def _run_jobs(forces_dict: dict, input_dict: dict) -> tuple[dict, list[dict]]:
    from osdagbridge.core.bridge_types.plate_girder.cross_bracing_design import (
        run_member_designs,
    )

    fake_pool = _FakeExecutor()

    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake_pool,
    ):
        results = run_member_designs(forces_dict, input_dict=input_dict)

    return results, fake_pool.submitted_dicts


@pytest.fixture
def bolted_forces_dict() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_bolted_and_welded_modules_are_registered_in_connect():
    from osdagbridge.core.utils.connect import (
        MODULE_CLASS_MAP,
        design_dict_struts_bolted,
        design_dict_struts_welded,
        design_dict_tension_bolted,
        design_dict_tension_welded,
    )

    for d in (
        design_dict_tension_bolted,
        design_dict_struts_bolted,
        design_dict_tension_welded,
        design_dict_struts_welded,
    ):
        assert d["Module"] in MODULE_CLASS_MAP


def test_run_member_designs_emits_bolted_jobs_for_fixture(bolted_forces_dict):
    """Golden: frozen forces_dict → Bolted tension/compression jobs only."""
    from osdagbridge.core.bridge_types.plate_girder.cross_bracing_design import (
        run_member_designs,
    )
    from osdagbridge.core.utils.connect import (
        design_dict_struts_bolted,
        design_dict_tension_bolted,
    )

    fake_pool = _FakeExecutor()

    with patch(
        "osdagbridge.core.utils.connect.design_pool",
        return_value=fake_pool,
    ):
        results = run_member_designs(bolted_forces_dict)

    assert "G1-G2" in results
    assert results["G1-G2"]["diagonal"]["tension"] == {"mock": True}
    assert results["G1-G2"]["diagonal"]["compression"] == {"mock": True}
    assert results["G1-G2"]["chord"]["tension"] == {"mock": True}
    assert "compression" not in results["G1-G2"].get("chord", {})

    jobs = fake_pool.submitted_dicts
    assert len(jobs) == 3

    by_key = {(j["Module"], float(j["Load.Axial"]), j["Member.Length"]): j for j in jobs}

    assert (
        design_dict_tension_bolted["Module"],
        10.0,
        "1500",
    ) in by_key
    assert (
        design_dict_struts_bolted["Module"],
        20.0,
        "1500",
    ) in by_key
    assert (
        design_dict_tension_bolted["Module"],
        5.0,
        "1000",
    ) in by_key

    # Existing Bolted path must not accidentally submit welded modules.
    welded_modules = {
        "Tension Member Design - Welded to End Gusset",
        "Struts Welded to End Gusset",
    }
    assert welded_modules.isdisjoint({j["Module"] for j in jobs})


def test_run_member_designs_emits_welded_jobs_for_explicit_pair_choice(
    bolted_forces_dict,
):
    from osdagbridge.core.utils.common import KEY_MP_CB_BRACING_CONNECTION
    from osdagbridge.core.utils.connect import (
        design_dict_struts_welded,
        design_dict_tension_welded,
    )

    _, jobs = _run_jobs(
        bolted_forces_dict,
        {f"{KEY_MP_CB_BRACING_CONNECTION}.G1G2.B1M1": "Welded"},
    )

    assert len(jobs) == 3
    assert {j["Module"] for j in jobs} == {
        design_dict_tension_welded["Module"],
        design_dict_struts_welded["Module"],
    }
    assert {(float(j["Load.Axial"]), j["Member.Length"]) for j in jobs} == {
        (10.0, "1500"),
        (20.0, "1500"),
        (5.0, "1000"),
    }


def test_run_member_designs_defaults_missing_connection_to_bolted(
    bolted_forces_dict,
):
    from osdagbridge.core.utils.connect import (
        design_dict_struts_bolted,
        design_dict_tension_bolted,
    )

    _, jobs = _run_jobs(bolted_forces_dict, {})

    assert {j["Module"] for j in jobs} == {
        design_dict_tension_bolted["Module"],
        design_dict_struts_bolted["Module"],
    }


def test_run_member_designs_resolves_connections_independently_per_pair(
    bolted_forces_dict,
):
    from osdagbridge.core.utils.common import KEY_MP_CB_BRACING_CONNECTION
    from osdagbridge.core.utils.connect import (
        design_dict_struts_bolted,
        design_dict_struts_welded,
        design_dict_tension_bolted,
        design_dict_tension_welded,
    )

    forces_dict = copy.deepcopy(bolted_forces_dict)
    forces_dict["pairs"]["G2-G3"] = {
        "diag_tension_kN": 30.0,
        "diag_compression_kN": 40.0,
        "chord_tension_kN": 15.0,
        "chord_compression_kN": None,
    }
    _, jobs = _run_jobs(
        forces_dict,
        {
            f"{KEY_MP_CB_BRACING_CONNECTION}.G1G2.B1M1": "Welded",
            f"{KEY_MP_CB_BRACING_CONNECTION}.G2G3.B2M1": "Bolted",
        },
    )

    module_by_force = {float(job["Load.Axial"]): job["Module"] for job in jobs}
    assert module_by_force[10.0] == design_dict_tension_welded["Module"]
    assert module_by_force[20.0] == design_dict_struts_welded["Module"]
    assert module_by_force[5.0] == design_dict_tension_welded["Module"]
    assert module_by_force[30.0] == design_dict_tension_bolted["Module"]
    assert module_by_force[40.0] == design_dict_struts_bolted["Module"]
    assert module_by_force[15.0] == design_dict_tension_bolted["Module"]


@pytest.mark.parametrize("value", ["", "not-a-connection"])
def test_run_member_designs_defaults_blank_or_invalid_connection_to_bolted(
    bolted_forces_dict,
    value,
):
    from osdagbridge.core.utils.common import KEY_MP_CB_BRACING_CONNECTION

    _, jobs = _run_jobs(
        bolted_forces_dict,
        {f"{KEY_MP_CB_BRACING_CONNECTION}.G1G2.B1M1": value},
    )

    assert all("Welded" not in job["Module"] for job in jobs)
    assert all(
        job["Module"]
        in {
            "Tension Member Design - Bolted to End Gusset",
            "Struts Bolted to End Gusset",
        }
        for job in jobs
    )


def test_run_member_designs_falls_back_to_nonblank_pair_member(
    bolted_forces_dict,
):
    from osdagbridge.core.utils.common import KEY_MP_CB_BRACING_CONNECTION

    _, jobs = _run_jobs(
        bolted_forces_dict,
        {
            f"{KEY_MP_CB_BRACING_CONNECTION}.G1G2.B1M1": "",
            f"{KEY_MP_CB_BRACING_CONNECTION}.G1G2.B1M2": "Welded",
        },
    )

    assert jobs
    assert all("Welded" in job["Module"] for job in jobs)
