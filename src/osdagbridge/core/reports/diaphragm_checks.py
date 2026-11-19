from math import isfinite

from osdagbridge.core.utils.common import KEY_MP_ED_TYPE


def _number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def diaphragm_checks(outputs):
    from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

    forces = (outputs.get("end_diaphragm_forces_dict") or {}).get("pairs", {})
    designs = outputs.get("end_diaphragm_design_results") or {}
    prefix = KEY_MP_ED_TYPE.rsplit(".", 1)[0] + "."
    kinds = {}
    for key, kind in outputs.items():
        if key.startswith(prefix) and key.endswith(".type"):
            pair_id = key[len(prefix):-len(".type")]
            if pair_id.startswith("G") and pair_id.count("G") == 2:
                first, second = pair_id[1:].split("G")
                if first.isdigit() and second.isdigit():
                    kinds[f"G{first}-G{second}"] = kind

    for pair in dict.fromkeys([*kinds, *forces, *designs]):
        members = designs.get(pair, {})
        pair_forces = forces.get(pair, {})
        kind = kinds.get(pair) or ("Cross Bracing" if members or pair_forces else "")
        found = False
        for member, stem in (("diagonal", "diag"), ("chord", "chord")):
            for direction in ("tension", "compression"):
                raw = members.get(member, {}).get(direction) or {}
                demand = _number(pair_forces.get(f"{stem}_{direction}_kN"))
                if not raw and demand is None:
                    continue
                found = True
                result = _extract_osdag_summary(raw)
                ratio = _number(result.get("efficiency"))
                status = raw.get("Design.Status", raw.get("Member.Status", raw.get("Optimum.Status")))
                if isinstance(status, bool):
                    status = "PASS" if status else "FAIL"
                combo = pair_forces.get(f"{stem}_{direction}_gov_lc") or ""
                if not status and ratio is None:
                    status = "Unavailable"
                yield (pair, kind, member, direction, combo, demand,
                       _number(result.get("capacity_kN")), ratio, status or "")
        if not found:
            yield (pair, kind, "", "", "", None, None, None, "Check unavailable")
