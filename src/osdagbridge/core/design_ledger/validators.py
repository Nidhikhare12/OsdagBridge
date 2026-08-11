"""Validation rules for design ledger entries."""

from .models import DesignCheckResult


def validate_check(check: DesignCheckResult):
    """
    Validate consistency of a design check result.

    Returns a list of validation errors.
    Empty list means the check is valid.
    """

    errors = []

    if check.capacity <= 0:
        errors.append("Capacity must be greater than zero.")

    if check.demand < 0:
        errors.append("Demand cannot be negative.")

    expected_ratio = check.demand / check.capacity if check.capacity else 0

    if abs(expected_ratio - check.utilization_ratio) > 0.01:
        errors.append(
            "Utilization ratio does not match demand/capacity."
        )

    if check.utilization_ratio <= 1 and check.status.upper() != "PASS":
        errors.append(
            "Check should pass when utilization ratio is <= 1."
        )

    if check.utilization_ratio > 1 and check.status.upper() == "PASS":
        errors.append(
            "Check cannot pass when utilization ratio is > 1."
        )

    return errors


def validate_ledger(ledger):
    """
    Validate all checks stored inside a ledger.
    """

    errors = []

    for check in ledger.get_all_checks():
        errors.extend(validate_check(check))

    return errors
