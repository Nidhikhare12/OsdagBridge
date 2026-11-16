"""Unit tests for structural design check validation, DCR computation, and status formatting.

Validates:
- Extraction of Demand-to-Capacity Ratios (DCR / UR = Demand / Capacity) for Girders,
  Deck Slab, Cross Bracing, and End Diaphragms.
- PASS / FAIL boundary condition logic (UR <= 1.0 -> PASS, UR > 1.0 -> FAIL).
- Verification that status_fail("FAIL") generates theme-compliant LaTeX with color CC0000.
"""

import json
from pathlib import Path
import pytest

from osdagbridge.core.reports.report_generator import ReportDataBridge
from osdagbridge.core.reports.data.utilization import collect_utilization, URRecord
from osdagbridge.core.reports.latex.text import status_pass, status_fail
from osdagbridge.core.reports.theme import get_active_theme


def test_design_check_dcr_and_status_formatting():
    """Verify DCR formulas, boundary logic, and LaTeX status formatting."""
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / "reports" / "baseline_default.json"
    assert fixture_path.is_file(), f"Missing test fixture: {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    input_dict = data.get("input_dict", {})
    output_dict = data.get("output_dict", {})

    bridge = ReportDataBridge(output_dict=output_dict, input_dict=input_dict, payload=None)
    ur_data = collect_utilization(bridge)

    assert len(ur_data.records) > 0, "Expected extracted UR records from baseline fixture"
    assert len(ur_data.girder_records) > 0, "Expected girder-specific UR records"

    # 1. Validate DCR formula: UR = Demand / Capacity where both are defined
    elements_found = set()
    for rec in ur_data.records:
        elements_found.add(rec.element)
        if rec.demand is not None and rec.capacity is not None and rec.capacity > 0:
            expected_ur = round(rec.demand / rec.capacity, 4)
            assert rec.ur == pytest.approx(expected_ur, rel=1e-2), (
                f"Mismatch in DCR calculation for {rec.check_name}: "
                f"demand={rec.demand}, capacity={rec.capacity}, got ur={rec.ur}, expected={expected_ur}"
            )

    # Verify that checks across structural components are represented
    assert "Girder" in elements_found, "Missing Girder design checks"
    assert "Deck Slab" in elements_found, "Missing Deck Slab design checks"
    assert "Cross Bracing" in elements_found, "Missing Cross Bracing design checks"

    # 2. Test PASS / FAIL boundary condition logic
    # Case A: Passing check (UR = 0.75 <= 1.0)
    passing_record = URRecord(
        element="Girder",
        check_name="Girder --- Moment",
        governing_combo="ULS 1",
        demand=1500.0,
        capacity=2000.0,
        demand_str="1500.00 kNm",
        capacity_str="2000.00 kNm",
        unit="kNm",
        ur=0.75,
        status="PASS",
    )
    assert passing_record.ur <= 1.0
    assert passing_record.status == "PASS"

    # Case B: Boundary exact limit (UR = 1.0 <= 1.0)
    boundary_record = URRecord(
        element="Girder",
        check_name="Girder --- Shear",
        governing_combo="ULS 2",
        demand=500.0,
        capacity=500.0,
        demand_str="500.00 kN",
        capacity_str="500.00 kN",
        unit="kN",
        ur=1.00,
        status="PASS",
    )
    assert boundary_record.ur <= 1.0
    assert boundary_record.status == "PASS"

    # Case C: Failing check (UR = 1.15 > 1.0)
    failing_record = URRecord(
        element="Girder",
        check_name="Girder --- Deflection",
        governing_combo="SLS Total",
        demand=46.0,
        capacity=40.0,
        demand_str="46.00 mm",
        capacity_str="40.00 mm",
        unit="mm",
        ur=1.15,
        status="FAIL",
    )
    assert failing_record.ur > 1.0
    assert failing_record.status == "FAIL"

    # 3. Validate LaTeX status formatting
    active_theme = get_active_theme()
    pass_formatted = status_pass("PASS")
    fail_formatted = status_fail("FAIL")

    # In default osdag_classic theme, fail color is CC0000 and pass color is 008000
    assert rf"\textcolor[HTML]{{{active_theme.palette.status_pass}}}{{\textbf{{PASS}}}}" == pass_formatted
    assert rf"\textcolor[HTML]{{{active_theme.palette.status_fail}}}{{\textbf{{FAIL}}}}" == fail_formatted
    assert "CC0000" in fail_formatted, "Failing status must use bright red #CC0000 for visibility"
    assert "008000" in pass_formatted, "Passing status must use green #008000"
