"""Container and management utilities for design check results."""

from .models import DesignCheckResult


class DesignLedger:
    """
    Stores and manages structural design verification results.

    A single ledger can contain multiple checks from different
    design modules and provide common access patterns for reports,
    GUI components and future automation.
    """

    def __init__(self):
        self._checks = []

    def add_check(self, check: DesignCheckResult):
        """Add a design verification result to the ledger."""
        self._checks.append(check)

    def get_all_checks(self):
        """Return all stored checks."""
        return self._checks

    def get_failed_checks(self):
        """Return checks that did not pass."""
        return [
            check
            for check in self._checks
            if not check.is_safe()
        ]

    def get_governing_check(self):
        """
        Return the check with the highest utilization ratio.

        The governing check represents the most critical
        design verification condition.
        """
        if not self._checks:
            return None

        return max(
            self._checks,
            key=lambda check: check.utilization_ratio
        )

    def summary(self):
        """Return a simple design verification summary."""
        return {
            "total_checks": len(self._checks),
            "passed": len(
                [
                    check
                    for check in self._checks
                    if check.is_safe()
                ]
            ),
            "failed": len(self.get_failed_checks()),
            "governing_check": (
                self.get_governing_check().title
                if self.get_governing_check()
                else None
            ),
        }

    def to_dict(self):
        """Serialize complete ledger data."""
        return [
            check.to_dict()
            for check in self._checks
        ]
