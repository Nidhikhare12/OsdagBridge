from dataclasses import dataclass
from math import isfinite

from osdagbridge.core.boq.boq_generator import end_diaphragm_pairs
from osdagbridge.core.utils.common import (
    KEY_DD_HAS_OVERHANG,
    KEY_DD_PUNCH_OK,
    KEY_DD_SHEAR_OK,
    KEY_MP_CB_TYPE,
    KEY_TS_NO_OF_GIRDERS,
)


@dataclass(frozen=True)
class Check:
    name: str
    ur: float | None
    status: str


def check(name, ratio, verdict=None):
    try:
        ratio = float(ratio)
        if not isfinite(ratio) or ratio < 0:
            ratio = None
    except (TypeError, ValueError):
        ratio = None
    status = str(verdict).strip().lower()
    if verdict is False or status in {"fail", "failed", "unsafe", "false"}:
        status = "Fail"
    elif verdict is True or status in {"pass", "passed", "safe", "ok", "true"}:
        status = "Pass"
    elif status in {"warn", "warning"}:
        status = "Warning"
    elif status == "info":
        status = "Info"
    elif ratio is None:
        status = "Incomplete"
    else:
        status = "Pass" if ratio <= 1.0 else "Fail"
    return Check(name, ratio, status)


def verdict(checks):
    statuses = {item.status for item in checks}
    if "Fail" in statuses:
        return "Fail"
    if statuses == {"N/A"}:
        return "N/A"
    if not statuses or "Incomplete" in statuses:
        return "Incomplete"
    if "Warning" in statuses:
        return "Warning"
    return "Pass"


def governing(checks):
    return max((item for item in checks if item.ur is not None),
               key=lambda item: item.ur, default=None)


def design_summary(inputs, outputs):
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    per_girder = (outputs.get("design_results") or {}).get("per_girder") or {}
    count = int(inputs.get(KEY_TS_NO_OF_GIRDERS) or 0)
    girder_ids = dict.fromkeys(
        [f"G{i}" for i in range(1, count + 1)]
        + [key for key in per_girder if not key.startswith("EB")]
    )
    girders = {}
    for key in girder_ids:
        girders[key] = [
            check(item.get("name", ""), item.get("dcr"), item.get("status"))
            for item in per_girder.get(key, {}).get("checks") or []
        ] or [check(key, None)]

    deck = outputs.get("deck_design_results") or {}
    deck_report = outputs.get("deck_report_values") or {}
    deck_statuses = {
        ur_key: deck_report[status_key]
        for ur_key, status_key in (
            ("ur_bot_punch", KEY_DD_PUNCH_OK), ("ur_bot_shear", KEY_DD_SHEAR_OK),
        )
        if status_key in deck_report
    }
    deck_statuses.update(deck.get("check_statuses") or {})
    deck_keys = dict.fromkeys([key for key in deck if key.startswith("ur_")] + list(deck_statuses))
    if deck_report.get(KEY_DD_HAS_OVERHANG):
        deck_keys.update(dict.fromkeys(f"ur_oh_{check}" for check in
                                      ("uls", "sls_c", "sls_s", "crack", "shear", "punch")))
    groups = {
        "Girder": [item for items in girders.values() for item in items],
        "Deck slab": [
            check("Deck " + key[3:].replace("oh_", "overhang ").replace("_", " "),
                  deck.get(key), deck_statuses.get(key))
            for key in deck_keys
        ],
    }
    configured_diaphragms = {pair for pair, _, _ in end_diaphragm_pairs(inputs, outputs, count)}
    diaphragm_pairs = {
        f"G{i}-G{i + 1}" for i in range(1, count)
        if f"G{i}G{i + 1}" in configured_diaphragms
    }
    bracing_pairs = {
        f"G{i}-G{i + 1}" for i in range(1, count)
        if any(value and str(value).strip().lower() not in {"none", "no", "n/a"}
               for key, value in inputs.items()
               if key.startswith(f"{KEY_MP_CB_TYPE}.G{i}G{i + 1}."))
    }
    for label, key, configured in (
        ("Cross bracing", "crossbracing_design_results", bracing_pairs),
        ("End Diaphragm", "end_diaphragm_design_results", diaphragm_pairs),
    ):
        pairs = outputs.get(key) or {}
        items = []
        for pair in dict.fromkeys([*pairs, *sorted(configured)]):
            members = pairs.get(pair) or {}
            if not members and pair not in configured:
                continue
            pair_checks = []
            for member, forces in members.items():
                for force, raw in forces.items():
                    result = _extract_osdag_summary(raw or {})
                    pair_checks.append(check(f"{label} {pair} {member} {force}",
                                             result.get("efficiency"), result.get("status")))
            items.extend(pair_checks or [check(f"{label} {pair}", None)])
        groups[label] = items or [Check(label, None, "N/A")]
    return girders, groups
