"""Data models for structured engineering design checks."""

from dataclasses import dataclass, field


@dataclass
class DesignCheckResult:
    """
    Represents a single structural design verification check.

    Stores engineering demand, capacity, utilization and code reference
    information in a consistent format.
    """

    check_id: str
    title: str
    code_reference: str
    description: str

    demand: float
    capacity: float

    utilization_ratio: float
    status: str

    metadata: dict = field(default_factory=dict)

    def is_safe(self):
        return self.status.upper() == "PASS"

    def to_dict(self):
        return {
            "check_id": self.check_id,
            "title": self.title,
            "code_reference": self.code_reference,
            "description": self.description,
            "demand": self.demand,
            "capacity": self.capacity,
            "utilization_ratio": self.utilization_ratio,
            "status": self.status,
            "metadata": self.metadata,
        }
