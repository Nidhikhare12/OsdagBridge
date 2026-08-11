"""Tests for design check ledger framework."""

from pathlib import Path

from osdagbridge.core.design_ledger import (
    DesignCheckResult,
    DesignLedger,
)
from osdagbridge.core.design_ledger.validators import (
    validate_check,
    validate_ledger,
)
from osdagbridge.core.design_ledger.serializers import (
    ledger_to_dict,
    ledger_to_json,
)


def create_check(status="PASS", ratio=0.75):
    return DesignCheckResult(
        check_id="BG-SHEAR-001",
        title="Shear Capacity Check",
        code_reference="IS 800:2007 Clause 8.4",
        description="Checks shear resistance of girder web.",
        demand=450,
        capacity=600,
        utilization_ratio=ratio,
        status=status,
    )


def test_add_and_retrieve_checks():
    ledger = DesignLedger()

    ledger.add_check(create_check())

    assert len(ledger.get_all_checks()) == 1
    assert ledger.get_all_checks()[0].title == "Shear Capacity Check"


def test_failed_checks_are_detected():

    ledger = DesignLedger()

    ledger.add_check(
        create_check(
            status="FAIL",
            ratio=1.2
        )
    )

    assert len(ledger.get_failed_checks()) == 1


def test_governing_check_returns_highest_utilization():

    ledger = DesignLedger()

    ledger.add_check(create_check(ratio=0.5))
    ledger.add_check(create_check(ratio=0.9))

    governing = ledger.get_governing_check()

    assert governing.utilization_ratio == 0.9


def test_invalid_utilization_is_detected():

    check = create_check(ratio=0.2)

    errors = validate_check(check)

    assert len(errors) > 0


def test_ledger_summary():

    ledger = DesignLedger()

    ledger.add_check(create_check())

    summary = ledger.summary()

    assert summary["total_checks"] == 1
    assert summary["passed"] == 1


def test_json_export(tmp_path):

    ledger = DesignLedger()
    ledger.add_check(create_check())

    output = Path(tmp_path) / "ledger.json"

    ledger_to_json(
        ledger,
        output
    )

    assert output.exists()


def test_dictionary_export():

    ledger = DesignLedger()
    ledger.add_check(create_check())

    data = ledger_to_dict(ledger)

    assert "summary" in data
    assert "checks" in data


def test_validate_ledger():

    ledger = DesignLedger()
    ledger.add_check(create_check())

    errors = validate_ledger(ledger)

    assert errors == []
def test_design_ledger_is_created_from_check_result():
    from osdagbridge.core.bridge_types.plate_girder.designer import DCREngine

    engine = DCREngine.__new__(DCREngine)

    engine.checks = []
    engine.design_ledger = None

    engine._add_check(
        1,
        "Flexure Test",
        "Cl.603.3.1",
        500,
        1000,
        "kN",
        "Test flexure check"
    )

    assert hasattr(engine, "design_ledger")
    assert len(engine.design_ledger.get_all_checks()) == 1
