"""Read the computed ratios used by the report without re-running design."""
from dataclasses import dataclass
from math import isfinite
import re

from osdagbridge.core.utils.common import KEY_TS_NO_OF_GIRDERS


@dataclass(frozen=True)
class Check:
    label: str
    ratio: float
    member: str = ""
    load_case: str = ""
    demand: float | None = None
    capacity: float | None = None
    section: str = ""
    failed: bool = False

    @property
    def status(self):
        return "FAIL" if self.failed or self.ratio > 1 else "PASS"


def nonnegative(value):
    """Convert a finite, nonnegative numeric value, retaining genuine zero."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) and number >= 0 else None


def girder_checks(outputs, inputs):
    """Use normalized DCRs for active girders, including conditional load checks."""
    results = (outputs.get("design_results") or {}).get("per_girder") or {}
    count = nonnegative(inputs.get(KEY_TS_NO_OF_GIRDERS))
    for member, data in results.items():
        match = re.fullmatch(r"G([1-9]\d*)", str(member))
        if not match or (count is not None and int(match[1]) > count):
            continue
        for raw in data.get("checks") or ():
            value = nonnegative(raw.get("dcr"))
            if value is not None:
                yield Check(raw.get("name") or f"Check {raw.get('check_id')}",
                            value, str(member), failed=str(raw.get("status", "")).upper() == "FAIL")
        for load_case, case in (data.get("per_lc") or {}).items():
            if str(load_case).lower().startswith("envelope"):
                continue
            for raw in case.get("checks") or ():
                value = nonnegative(raw.get("dcr"))
                if value is not None:
                    yield Check(raw.get("name") or f"Check {raw.get('id')}",
                                value, str(member), str(load_case),
                                failed=str(raw.get("status", "")).upper() == "FAIL")


def deck_checks(outputs):
    """Deck designer exports dimensionless ratios, with overhang keys when applicable."""
    locations = {"bot": "Sagging", "top": "Hogging", "oh": "Overhang"}
    kinds = {"uls": "flexure", "sls_c": "concrete stress", "sls_s": "steel stress",
             "crack": "crack width", "shear": "one-way shear", "punch": "punching shear"}
    results = outputs.get("deck_design_results") or {}
    for location, label in locations.items():
        for kind, name in kinds.items():
            ratio = nonnegative(results.get(f"ur_{location}_{kind}"))
            if ratio is not None:
                yield Check(f"{label} {name}", ratio)
    for key, name in (("trans_shear", "Interface shear"), ("crack", "Crack control reinforcement"),
                      ("conc_stress", "Composite concrete stress"),
                      ("rebar_stress", "Composite reinforcement stress")):
        ratio = nonnegative(results.get(f"ur_composite_{key}"))
        if ratio is not None:
            yield Check(name, ratio)


def transverse_checks(outputs, *, diaphragm=False):
    """Read each member's own axial design and the corresponding analysed demand."""
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    prefix = "end_diaphragm" if diaphragm else "crossbracing"
    results = outputs.get(f"{prefix}_design_results") or {}
    forces = (outputs.get(f"{prefix}_forces_dict") or {}).get("pairs", {})
    for pair, members in results.items():
        for member in ("diagonal", "chord"):
            raw_member = members.get(member) or {}
            for action in ("compression", "tension"):
                result = _extract_osdag_summary(raw_member.get(action) or {})
                ratio = nonnegative(result.get("efficiency"))
                if ratio is None:
                    continue
                key = f"{'diag' if member == 'diagonal' else member}_{action}"
                pair_forces = forces.get(pair) or {}
                demand = pair_forces.get(f"{key}_kN")
                yield Check(f"{member.capitalize()} {action}", ratio, pair,
                            pair_forces.get(f"{key}_gov_lc") or "",
                            nonnegative(abs(demand)) if isinstance(demand, (int, float)) else nonnegative(demand),
                            nonnegative(result.get("capacity_kN")), result.get("section") or "")


def component_checks(outputs, inputs):
    """Checks by component in the order used in the executive summary and plot."""
    return {
        "Steel Plate Girders": list(girder_checks(outputs, inputs)),
        "Concrete Deck Slab": list(deck_checks(outputs)),
        "Cross Bracing": [],  # exported efficiency has no identified governing denominator
        "End Diaphragms": [],  # governing denominator is not identified in the export
    }


def governing(checks):
    return max(checks, key=lambda check: check.ratio, default=None)


def outcome(checks):
    if not checks:
        return "Not available"
    return "FAIL" if any(check.status == "FAIL" for check in checks) else "PASS"
