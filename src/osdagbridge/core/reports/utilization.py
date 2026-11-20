"""Read the computed ratios used by the report without re-running design."""
from dataclasses import dataclass
from math import isfinite
import re

from osdagbridge.core.utils.common import (
    KEY_DD_MU_BOT, KEY_DD_MU_OH, KEY_DD_MU_TOP, KEY_DD_SHEAR_VRDC,
    KEY_DD_VRD_C_MPA, KEY_TS_NO_OF_GIRDERS,
)


# Earlier exports did not label the fallback. Use their recorded denominator
# where available. The overhang shear denominators were not exported.
_LEGACY_DECK_CAPACITIES = {
    "ur_bot_uls": KEY_DD_MU_BOT,
    "ur_top_uls": KEY_DD_MU_TOP,
    "ur_oh_uls": KEY_DD_MU_OH,
    "ur_bot_shear": KEY_DD_SHEAR_VRDC,
    "ur_bot_punch": KEY_DD_VRD_C_MPA,
    "ur_oh_shear": None,
    "ur_oh_punch": None,
}


@dataclass(frozen=True)
class Check:
    label: str
    ratio: float | None
    member: str = ""
    load_case: str = ""
    demand: float | None = None
    capacity: float | None = None
    section: str = ""
    failed: bool = False

    @property
    def status(self):
        if self.failed:
            return "FAIL"
        if self.ratio is None:
            return "Not available"
        return "FAIL" if self.ratio > 1 else "PASS"


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
    unavailable = results.get("ur_unavailable_capacity")
    capacities = outputs.get("deck_report_values") or {}
    for location, label in locations.items():
        for kind, name in kinds.items():
            key = f"ur_{location}_{kind}"
            ratio = nonnegative(results.get(key))
            legacy_ambiguous = (
                unavailable is None and key in _LEGACY_DECK_CAPACITIES and ratio == 9.999
                and not nonnegative(capacities.get(_LEGACY_DECK_CAPACITIES[key]))
            )
            if key in (unavailable or ()) or legacy_ambiguous:
                yield Check(f"{label} {name}", None)
            elif ratio is not None:
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
                            nonnegative(result.get("capacity_kN")) if action == "tension" else None,
                            result.get("section") or "")


def component_checks(outputs, inputs):
    """Checks by component in the order used in the executive summary and plot."""
    return {
        "Steel Plate Girders": list(girder_checks(outputs, inputs)),
        "Concrete Deck Slab": list(deck_checks(outputs)),
        "Cross Bracing": [],  # exported efficiency has no identified governing denominator
        "End Diaphragms": [],  # governing denominator is not identified in the export
    }


def governing(checks):
    return max((check for check in checks if check.ratio is not None),
               key=lambda check: check.ratio, default=None)


def outcome(checks):
    statuses = {check.status for check in checks}
    if "FAIL" in statuses:
        return "FAIL"
    return "PASS" if statuses == {"PASS"} else "Not available"
