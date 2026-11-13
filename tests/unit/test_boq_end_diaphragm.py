"""End-diaphragm steel take-off (boq_generator) — hand-calculated checks.

Bridge: 3 girders (2 pairs), spacing s = 2.0 m, girder depth D = 1.0 m,
X-bracing end diaphragms at both supports, section area A = 10 cm^2.
  h = 0.85 D = 0.85 m;  diagonal L = sqrt(2.0^2 + 0.85^2) = 2.17313 m
  diaphragms = 2 pairs x 2 supports = 4
  chords  : 4 x 10e-4 x 2.0     x 7.85 = 0.0628 t -> "0.06"
  diagonal: 8 x 10e-4 x 2.17313 x 7.85 = 0.13647 t -> "0.14"
"""
from osdagbridge.core.boq.boq_generator import _end_diaphragm_quantities
from osdagbridge.core.utils.common import KEY_MP_GIRDER_DEPTH

D = "member_properties.end_diaphragm_details"
P = "transverse_member_design.ed.section_properties"


def _inputs(ed_type="Cross Bracing", top="Yes"):
    d = {KEY_MP_GIRDER_DEPTH: 1.0}
    for g in (1, 2):
        for end in (1, 2):
            sfx = f".G{g}G{g + 1}.E{g}M{end}"
            d[f"{D}.type{sfx}"] = ed_type
            d[f"{D}.bracing_type{sfx}"] = "X-Bracing"
            d[f"{D}.top_chord{sfx}"] = top
            d[f"{D}.bottom_chord{sfx}"] = "Yes"
    return d


def _outputs(area=10.0):
    return {f"{P}.{m}.G{g}G{g + 1}.A": area
            for g in (1, 2) for m in ("end_diaphragm", "top_chord", "bottom_chord")}


def test_matches_hand_calculation():
    q = _end_diaphragm_quantities(_inputs(), _outputs(), n_girders=3, spacing=2.0)
    assert (q["ed_top_qty"], q["ed_top_wt_total"]) == ("4", "0.06")
    assert (q["ed_bot_qty"], q["ed_bot_wt_total"]) == ("4", "0.06")
    assert (q["ed_diag_qty"], q["ed_diag_wt_total"]) == ("8", "0.14")
    assert "2.17" in q["ed_diag_vol_formula"]


def test_disabled_top_chord_is_zero_not_missing():
    q = _end_diaphragm_quantities(_inputs(top="No"), _outputs(), n_girders=3, spacing=2.0)
    assert (q["ed_top_qty"], q["ed_top_wt_total"]) == ("0", "0.00")
    assert q["ed_diag_wt_total"] == "0.14"


def test_missing_section_area_is_na_not_zero():
    q = _end_diaphragm_quantities(_inputs(), {}, n_girders=3, spacing=2.0)
    assert all(q[f"{p}_wt_total"] == "N.A." for p in ("ed_top", "ed_bot", "ed_diag"))


def test_rolled_beam_end_diaphragm_is_na():
    q = _end_diaphragm_quantities(_inputs(ed_type="Rolled Beam"), _outputs(), n_girders=3, spacing=2.0)
    assert q["ed_diag_wt_total"] == "N.A."
