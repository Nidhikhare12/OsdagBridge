"""Dependency-light helpers for bridge-wide design-check aggregation."""

from collections.abc import Mapping
import math


def aggregate_bridge_category_urs(per_girder_results: dict) -> dict:
    """Return the governing finite, non-negative DCR for each category.

    The winning category row retains its sub-check detail and records the
    girder that governs that category. Invalid, missing, negative, NaN and
    infinite values are ignored rather than entering the bridge envelope.
    """
    envelope = {}
    if not isinstance(per_girder_results, Mapping):
        return envelope

    for girder_name, girder_result in per_girder_results.items():
        if not isinstance(girder_result, Mapping):
            continue
        categories = girder_result.get("category_urs", {}) or {}
        if not isinstance(categories, Mapping):
            continue
        for category_no, category in categories.items():
            if not isinstance(category, Mapping):
                continue
            try:
                category_no = int(category_no)
                candidate = float(category.get("max_dcr"))
            except (TypeError, ValueError):
                continue
            if not math.isfinite(candidate) or candidate < 0:
                continue
            current = envelope.get(category_no)
            if current is None or candidate > float(current["max_dcr"]):
                envelope[category_no] = dict(category, max_dcr=candidate,
                                              governing_girder=str(girder_name))
    return envelope
