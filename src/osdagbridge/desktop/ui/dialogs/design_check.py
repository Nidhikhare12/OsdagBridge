"""Design check computations for the Steel Design dialog.

Each function returns a dictionary with:
- equation: HTML string for displaying the governing equation
- result_label: label for the computed capacity or limit
- result: computed value
- dcr_label: label describing the demand/capacity ratio
- dcr: demand/capacity ratio
- status: "PASS" or "FAIL"
- details: optional extra text for the UI
"""
from copy import deepcopy
from math import pi, sqrt

PASS_LIMIT = 1.0

# Default values are intentionally modest so the UI shows meaningful, non-zero
# utilization numbers even when no analysis results are wired in yet.
DEFAULT_INPUTS = {
    "flexure": {
        "Md": 900.0,
        "Zp": 5.5,
        "fy": 345.0,
        "gamma_m": 1.1,
        "beta_b": 1.0,
    },
    "shear": {
        "Vd": 320.0,
        "Av": 4.0,
        "fy": 345.0,
        "gamma_m": 1.1,
    },
    "interaction": {},
    "ltb": {
        "Md": 900.0,
        "E": 200000.0,
        "Iy": 0.1,
        "LLTB": 12.0,
    },
    "long_trans_shear": {
        "Vd": 190.0,
        "k": 1.0,
        "rho": 0.012,
        "fck": 30.0,
        "b": 0.3,
        "d": 0.5,
        "Asv": 250.0,
        "fy": 415.0,
        "s": 200.0,
    },
    "fatigue": {
        "delta_sigma": 75.0,
        "delta_sigma_c": 120.0,
        "gamma_mf": 1.2,
    },
    "stress": {
        "Md": 1200.0,
        "Z": 5.0,
        "fy": 345.0,
        "gamma_m": 1.1,
    },
    "deflection": {
        "delta": 28.0,
        "L": 18000.0,
        "limit_ratio": 600.0,
    },
}


def build_inputs(overrides=None):
    """Return per-check inputs, merging defaults with optional overrides."""
    base = {key: deepcopy(value) for key, value in DEFAULT_INPUTS.items()}

    # Ensure interaction/ltb reuse the same demand used in flexure/shear by default
    base["interaction"].setdefault("Md", base["flexure"]["Md"])
    base["interaction"].setdefault("Vd", base["shear"]["Vd"])
    base["ltb"].setdefault("Md", base["flexure"]["Md"])

    if overrides:
        for key, values in overrides.items():
            if key not in base or not isinstance(values, dict):
                continue
            base[key].update({k: v for k, v in values.items() if v is not None})

    # Keep dependent defaults synced with any incoming overrides
    base["interaction"]["Md"] = base["flexure"].get("Md", base["interaction"].get("Md", 0.0))
    base["interaction"]["Vd"] = base["shear"].get("Vd", base["interaction"].get("Vd", 0.0))
    base["ltb"]["Md"] = base["flexure"].get("Md", base["ltb"].get("Md", 0.0))

    return base


def _params_for(key, overrides=None):
    params = deepcopy(DEFAULT_INPUTS.get(key, {}))
    if key == "interaction":
        params.setdefault("Md", DEFAULT_INPUTS["flexure"]["Md"])
        params.setdefault("Vd", DEFAULT_INPUTS["shear"]["Vd"])
    if key == "ltb":
        params.setdefault("Md", DEFAULT_INPUTS["flexure"]["Md"])
    if overrides:
        params.update({k: v for k, v in overrides.items() if v is not None})
    return params


def _safe_div(num, denom):
    try:
        return num / denom if denom else float("inf")
    except Exception:
        return float("inf")


def _status(dcr):
    return "PASS" if dcr <= PASS_LIMIT else "FAIL"


def _build_response(equation, result_label, result_value, dcr_label, dcr_value, details=None):
    data = {
        "equation": equation,
        "result_label": result_label,
        "result": result_value,
        "dcr_label": dcr_label,
        "dcr": dcr_value,
        "status": _status(dcr_value),
    }
    if details:
        data["details"] = details
    return data


def compute_flexure(params=None):
    p = _params_for("flexure", params)
    md = p.get("Md", 0.0)
    beta_b = p.get("beta_b", 1.0)
    zp = p.get("Zp", 0.0)
    fy = p.get("fy", 0.0)
    gamma_m = p.get("gamma_m", 1.0)

    mr = beta_b * zp * fy / gamma_m if gamma_m else float("inf")
    dcr = _safe_div(md, mr)

    equation = (
        "M<sub>d</sub> &le; M<sub>r</sub><br/>"
        "M<sub>r</sub> = &beta;<sub>b</sub> Z<sub>p</sub> f<sub>y</sub> / &gamma;<sub>m</sub>"
    )
    return _build_response(equation, "M<sub>r</sub>", mr, "M<sub>d</sub> / M<sub>r</sub>", dcr)


def compute_shear(params=None):
    p = _params_for("shear", params)
    vd = p.get("Vd", 0.0)
    av = p.get("Av", 0.0)
    fy = p.get("fy", 0.0)
    gamma_m = p.get("gamma_m", 1.0)

    vr = _safe_div(av * fy, sqrt(3) * gamma_m) if gamma_m else float("inf")
    dcr = _safe_div(vd, vr)

    equation = (
        "V<sub>d</sub> &le; V<sub>r</sub><br/>"
        "V<sub>r</sub> = A<sub>v</sub> f<sub>y</sub> / (&radic;3 &gamma;<sub>m</sub>)"
    )
    return _build_response(equation, "V<sub>r</sub>", vr, "V<sub>d</sub> / V<sub>r</sub>", dcr)


def compute_interaction(params=None, flexure=None, shear=None):
    p = _params_for("interaction", params)
    md = p.get("Md", 0.0)
    vd = p.get("Vd", 0.0)

    mr = flexure.get("result") if isinstance(flexure, dict) else None
    vr = shear.get("result") if isinstance(shear, dict) else None
    if mr is None:
        mr = compute_flexure().get("result")
    if vr is None:
        vr = compute_shear().get("result")

    dcr = _safe_div(md, mr) + _safe_div(vd, vr)
    equation = "M<sub>d</sub>/M<sub>r</sub> + V<sub>d</sub>/V<sub>r</sub> &le; 1.0"
    return _build_response(equation, "Utilization", dcr, "Combined DCR", dcr)


def compute_ltb(params=None):
    p = _params_for("ltb", params)
    md = p.get("Md", 0.0)
    e_mod = p.get("E", 0.0)
    iy = p.get("Iy", 0.0)
    lltb = p.get("LLTB", 0.0)

    mcr = _safe_div(pi ** 2 * e_mod * iy, lltb ** 2) if lltb else float("inf")
    dcr = _safe_div(md, mcr)

    equation = "M<sub>cr</sub> = (&pi;&sup2; E I<sub>y</sub>) / L<sub>LTB</sub><sup>2</sup>"
    return _build_response(equation, "M<sub>cr</sub>", mcr, "M<sub>d</sub> / M<sub>cr</sub>", dcr)


def compute_long_transverse_shear(params=None):
    p = _params_for("long_trans_shear", params)
    vd = p.get("Vd", 0.0)
    k_coeff = p.get("k", 1.0)
    rho = p.get("rho", 0.0)
    fck = p.get("fck", 0.0)
    b = p.get("b", 0.0)
    d = p.get("d", 0.0)
    asv = p.get("Asv", 0.0)
    fy = p.get("fy", 0.0)
    s = p.get("s", 0.0)

    vrd_c = 0.18 * k_coeff * (100 * rho * fck) ** (1 / 3) * b * d
    vrd_s = _safe_div(asv * fy * d, s)
    vrd = vrd_c + vrd_s
    dcr = _safe_div(vd, vrd)

    equation = (
        "V<sub>rd</sub> = V<sub>rd,c</sub> + V<sub>rd,s</sub><br/>"
        "V<sub>rd,c</sub> = 0.18 k (100 &rho; f<sub>ck</sub>)<sup>1/3</sup> b d<br/>"
        "V<sub>rd,s</sub> = A<sub>sv</sub> f<sub>y</sub> d / s"
    )
    details = f"V<sub>rd,c</sub> = {vrd_c:.3f}, V<sub>rd,s</sub> = {vrd_s:.3f}"
    return _build_response(equation, "V<sub>rd</sub>", vrd, "V<sub>d</sub> / V<sub>rd</sub>", dcr, details=details)


def compute_fatigue(params=None):
    p = _params_for("fatigue", params)
    delta_sigma = p.get("delta_sigma", 0.0)
    delta_sigma_c = p.get("delta_sigma_c", 0.0)
    gamma_mf = p.get("gamma_mf", 1.0)

    delta_sigma_allowable = _safe_div(delta_sigma_c, gamma_mf)
    dcr = _safe_div(delta_sigma, delta_sigma_allowable)

    equation = (
        "&Delta;&sigma; &le; &Delta;&sigma;<sub>allowable</sub><br/>"
        "&Delta;&sigma;<sub>allowable</sub> = &Delta;&sigma;<sub>c</sub> / &gamma;<sub>mf</sub>"
    )
    return _build_response(
        equation,
        "&Delta;&sigma;<sub>allowable</sub>",
        delta_sigma_allowable,
        "&Delta;&sigma; / &Delta;&sigma;<sub>allowable</sub>",
        dcr,
    )


def compute_stress(params=None):
    p = _params_for("stress", params)
    md = p.get("Md", 0.0)
    z = p.get("Z", 0.0)
    fy = p.get("fy", 0.0)
    gamma_m = p.get("gamma_m", 1.0)

    sigma = _safe_div(md, z)
    limit = _safe_div(fy, gamma_m)
    dcr = _safe_div(sigma, limit)

    equation = "&sigma; = M<sub>d</sub> / Z<br/>&sigma; &le; f<sub>y</sub> / &gamma;<sub>m</sub>"
    return _build_response(
        equation,
        "&sigma;",
        sigma,
        "&sigma; / (f<sub>y</sub> / &gamma;<sub>m</sub>)",
        dcr,
    )


def compute_deflection(params=None):
    p = _params_for("deflection", params)
    delta = p.get("delta", 0.0)
    length = p.get("L", 0.0)
    limit_ratio = p.get("limit_ratio", 600.0)

    limit = _safe_div(length, limit_ratio)
    dcr = _safe_div(delta, limit)

    equation = "&delta; &le; L / x"
    details = f"x = {limit_ratio}"
    return _build_response(
        equation,
        "Allowable &delta;",
        limit,
        "&delta; / (L / x)",
        dcr,
        details=details,
    )


def compute_all(overrides=None):
    """Compute all design checks with optional overrides per check key."""
    inputs = build_inputs(overrides or {})

    results = {}
    results["flexure"] = compute_flexure(inputs.get("flexure"))
    results["shear"] = compute_shear(inputs.get("shear"))
    results["interaction"] = compute_interaction(inputs.get("interaction"), results["flexure"], results["shear"])
    results["ltb"] = compute_ltb(inputs.get("ltb"))
    results["shear_long_trans"] = compute_long_transverse_shear(inputs.get("long_trans_shear"))
    results["fatigue"] = compute_fatigue(inputs.get("fatigue"))
    results["stress"] = compute_stress(inputs.get("stress"))
    results["deflection"] = compute_deflection(inputs.get("deflection"))
    return results