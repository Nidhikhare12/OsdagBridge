"""
Tests for the substructure CAD builders and their IFC export.

Run from the repository root:
    PYTHONPATH=src:tests/integration pytest tests/integration/test_substructure.py -q
"""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from sample_params import sample_params  # noqa: E402

from osdagbridge.core.bridge_components.sub_structure.substructure_builder import (  # noqa: E402
    SubstructureParams, substructure_layout, iter_bars, quantity_summary, run_detailing_checks,
)
from osdagbridge.core.bridge_components.sub_structure.pier_cap.builder import depth_at  # noqa: E402
from osdagbridge.core.bridge_components.sub_structure.reinforcement.builder import (  # noqa: E402
    RebarParams, development_length,
)

TOL = 1e-6


def _layout(skew=0.0, **kw):
    return substructure_layout(
        SubstructureParams(**kw), span_length=25000, soffit_z=-710, deck_width=16450,
        girder_y_positions=[-5500, -2750, 0, 2750, 5500], skew_angle=skew)


# --------------------------------------------------------------------- layout

def test_defaults_match_task_specification():
    p = SubstructureParams()
    assert (p.pier_diameter, p.pier_height) == (800, 3000)
    assert (p.pier_cap_top_width, p.pier_cap_bottom_width, p.pier_cap_depth) == (3000, 1200, 600)
    assert (p.pile_cap_length, p.pile_cap_width, p.pile_cap_depth) == (2200, 1200, 600)
    assert (p.n_piles_per_cap, p.pile_diameter, p.pile_length, p.pile_spacing) == (4, 400, 5000, 600)
    r = p.rebar
    assert (r.main_dia, r.main_spacing, r.tie_dia, r.tie_spacing, r.cover) == (16, 150, 8, 200, 40)


def test_two_support_lines_with_full_stack():
    sups = _layout()
    assert [s["origin"][0] for s in sups] == [0.0, 25000.0]
    for s in sups:
        c = s["components"]
        assert len(c["pier_caps"]) == 1 and len(c["piers"]) == 1
        assert len(c["pile_caps"]) == 1 and len(c["piles"]) == 4
        assert len(c["pedestals"]) == 5
        lv = s["levels"]
        # pier cap -> pier -> pile cap -> piles stack without gaps
        assert lv["pier_top"] == pytest.approx(-600)
        assert lv["pile_cap_top"] == pytest.approx(-3600)
        assert lv["pile_cap_bottom"] == pytest.approx(-4200)
        assert lv["pile_toe"] == pytest.approx(-9200)
    # pedestal top + bearing = girder soffit
    assert sups[0]["origin"][2] + 150 + 100 == pytest.approx(-710)


def test_pier_cap_length_defaults_to_deck_width_and_follows_skew():
    assert _layout()[0]["components"]["pier_caps"][0]["concrete"]["length"] == pytest.approx(16450)
    skewed = _layout(skew=20)[0]
    assert skewed["components"]["pier_caps"][0]["concrete"]["length"] == pytest.approx(
        16450 / math.cos(math.radians(20)))
    assert skewed["rotation_deg"] == -20


def test_pile_grid_is_2x2_at_600_spacing():
    piles = _layout()[0]["components"]["piles"]
    xs = sorted({round(p["concrete"]["base"][0]) for p in piles})
    ys = sorted({round(p["concrete"]["base"][1]) for p in piles})
    assert xs == [-300, 300] and ys == [-300, 300]


def _assert_cylinder_cover(layout, cover):
    c = layout["concrete"]
    (cx, cy, zb), R, H = c["base"], c["radius"], c["height"]
    for bar in layout["bars"]:
        r_bar = bar["dia"] / 2.0
        for x, y, z in bar["path"]:
            if zb - TOL <= z <= zb + H + TOL:     # starter bars leave the element
                assert math.hypot(x - cx, y - cy) + r_bar <= R - cover + 1e-3


def _assert_box_cover(layout, cover):
    (x0, y0, z0), (sx, sy, sz) = layout["concrete"]["min"], layout["concrete"]["size"]
    for bar in layout["bars"]:
        r_bar = bar["dia"] / 2.0
        for x, y, z in bar["path"]:
            assert x0 + cover - r_bar - 1e-3 <= x <= x0 + sx - cover + r_bar + 1e-3
            assert y0 + cover - r_bar - 1e-3 <= y <= y0 + sy - cover + r_bar + 1e-3
            assert z0 + cover + r_bar - 1e-3 <= z <= z0 + sz - cover - r_bar + 1e-3


def test_reinforcement_respects_clear_cover():
    s = _layout()[0]
    cover = SubstructureParams().rebar.cover
    for lay in s["components"]["piers"] + s["components"]["piles"]:
        _assert_cylinder_cover(lay, cover)
    for lay in s["components"]["pile_caps"]:
        _assert_box_cover(lay, cover)
    cap = s["components"]["pier_caps"][0]
    cc = cap["concrete"]
    for bar in cap["bars"]:
        for _, y, z in bar["path"]:
            d_local = depth_at(y, length=cc["length"], depth=cc["depth"], end_depth=cc["end_depth"],
                               core_length=cc["core_length"])
            assert cc["z_top"] - d_local + cover + bar["dia"] / 2 - 1e-3 <= z
            assert z <= cc["z_top"] - cover - bar["dia"] / 2 + 1e-3
            assert abs(y) <= cc["length"] / 2 - cover + 1e-3
    for lay in s["components"]["pedestals"]:
        mesh = [b for b in lay["bars"] if b["dia"] == SubstructureParams().rebar.tie_dia]
        _assert_box_cover(dict(lay, bars=mesh), cover)


def test_circular_members_have_at_least_six_bars_and_ties_at_spacing():
    s = _layout()[0]
    for lay in s["components"]["piers"] + s["components"]["piles"]:
        mains = [b for b in lay["bars"] if b["role"] == "MAIN"]
        ties = sorted(b["path"][0][2] for b in lay["bars"] if b["role"] == "LIGATURE")
        assert len(mains) >= 6
        assert all(t2 - t1 == pytest.approx(200) for t1, t2 in zip(ties, ties[1:]))


def test_closed_ties_are_open_polylines_with_lap():
    for b in iter_bars(_layout()):
        if b["closed"]:
            assert b["path"][0] != b["path"][-1]
            assert len(b["path"]) >= 5


def test_quantity_summary():
    q = quantity_summary(_layout())
    assert q["concrete_m3"]["piers"] == pytest.approx(2 * math.pi * 0.4 ** 2 * 3.0)
    head = 4 * math.pi * 0.2 ** 2 * 0.05                       # pile heads inside the cap
    assert q["concrete_m3"]["pile_caps"] == pytest.approx(2 * (2.2 * 1.2 * 0.6 - head))
    assert q["concrete_m3"]["piles"] == pytest.approx(8 * math.pi * 0.2 ** 2 * 5.05)
    assert sum(v["mass_kg"] for v in q["rebar"].values()) > 0


# ------------------------------------------------------------------------ CAD

def test_cad_generator_returns_substructure_shapes():
    pytest.importorskip("OCC")
    from OCC.Core.TopoDS import TopoDS_Shape
    from osdagbridge.core.bridge_types.plate_girder.cad_generator import PlateGirderCADGenerator

    gen = PlateGirderCADGenerator()
    md = gen.generate(sample_params(skew_angle=15))
    for key in ("pier_caps", "pedestals", "piers", "pile_caps", "piles", "substructure_rebars"):
        assert md[key] and all(isinstance(s, TopoDS_Shape) for s in md[key]), key
    gen.model_data = md
    assert gen.create3Dcad() is not None


def test_substructure_can_be_disabled():
    pytest.importorskip("OCC")
    from osdagbridge.core.bridge_types.plate_girder.cad_generator import PlateGirderCADGenerator
    md = PlateGirderCADGenerator().generate(sample_params(include_substructure=False))
    assert md["piers"] == [] and md["substructure_rebars"] == []


# ------------------------------------------------------------------------ IFC

@pytest.fixture(scope="module")
def ifc_file(tmp_path_factory):
    ifcopenshell = pytest.importorskip("ifcopenshell")
    from osdagbridge.core.ifc_export_bridge.export_ifc_handler import PlateGirderIfcExportHandler
    path = str(tmp_path_factory.mktemp("ifc") / "bridge.ifc")
    result = []
    PlateGirderIfcExportHandler(sample_params(skew_angle=20), path,
                                lambda ok, msg: result.append(ok)).export()
    assert result == [True]
    return ifcopenshell.open(path)


def test_ifc_contains_super_and_substructure(ifc_file):
    f = ifc_file
    assert f.by_type("IfcPlate") and f.by_type("IfcSlab")              # superstructure
    assert len(f.by_type("IfcColumn")) == 2
    assert len([b for b in f.by_type("IfcBeam") if b.ObjectType == "PierCap"]) == 2
    assert [x.PredefinedType for x in f.by_type("IfcFooting")] == ["PILE_CAP"] * 2
    assert len(f.by_type("IfcPile")) == 8
    assert len(f.by_type("IfcReinforcingBar")) > 500
    storeys = {s.Name for s in f.by_type("IfcBuildingStorey")}
    assert {"Superstructure", "Substructure", "Foundation"} <= storeys


def test_ifc_is_schema_and_rule_valid(ifc_file):
    import ifcopenshell.validate
    log = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(ifc_file, log, express_rules=True)
    assert log.statements == []


def test_ifc_elements_have_relative_placements_and_quantities(ifc_file):
    import ifcopenshell.util.element as ue
    for pile in ifc_file.by_type("IfcPile"):
        support = pile.ObjectPlacement.PlacementRelTo            # support frame
        storey = support.PlacementRelTo                          # storey (global)
        assert storey == ue.get_container(pile).ObjectPlacement
        assert ue.get_psets(pile)["Qto_PileBaseQuantities"]["NetVolume"] == pytest.approx(
            math.pi * 0.2 ** 2 * 5.05)                           # 5 m + 50 mm head in cap
        assert ue.get_material(pile).Name.startswith("Concrete")
    bar = ifc_file.by_type("IfcReinforcingBar")[0]
    assert bar.ObjectPlacement.PlacementRelTo.PlacementRelTo.PlacementRelTo is not None
    assert ue.get_type(bar) is not None
    assert ue.get_psets(bar)["Qto_ReinforcingElementBaseQuantities"]["Weight"] > 0


def test_ifc_geometry_tessellates_and_matches_quantities(ifc_file):
    import ifcopenshell.geom
    import ifcopenshell.util.shape as us
    import ifcopenshell.util.element as ue
    s = ifcopenshell.geom.settings()
    for cls in ("IfcColumn", "IfcFooting", "IfcPile", "IfcBeam"):
        for e in ifc_file.by_type(cls):
            if cls == "IfcBeam" and e.ObjectType != "PierCap":
                continue
            shape = ifcopenshell.geom.create_shape(s, e)
            qto = next(v for k, v in ue.get_psets(e).items() if k.startswith("Qto_"))
            # geometry is the gross solid (pile-cap net volume excludes pile heads)
            assert us.get_volume(shape.geometry) == pytest.approx(qto["GrossVolume"], rel=0.01)
    for bar in ifc_file.by_type("IfcReinforcingBar"):
        ifcopenshell.geom.create_shape(s, bar)       # raises if a bar cannot be built


# ------------------------------------------------------------- hammerhead cap

def test_hammerhead_cap_tapers_from_core_to_tips():
    cap = _layout()[0]["components"]["pier_caps"][0]["concrete"]
    assert cap["style"] == "HAMMERHEAD"
    depths = {round(st["y"]): st["depth"] for st in cap["stations"]}
    assert depths[round(-cap["length"] / 2)] == pytest.approx(300)     # tips: 0.5 D
    assert depths[round(cap["core_length"] / 2)] == pytest.approx(600)  # over pier: full D
    assert cap["core_length"] == pytest.approx(800 + 2 * 300)


def test_trapezoidal_style_is_a_prism():
    cap = _layout(pier_cap_style="TRAPEZOIDAL")[0]["components"]["pier_caps"][0]["concrete"]
    assert len(cap["stations"]) == 2
    assert cap["volume_mm3"] == pytest.approx((3000 + 1200) / 2 * 600 * 16450)


def test_cap_volume_matches_occ_solid():
    pytest.importorskip("OCC")
    from OCC.Core.GProp import GProp_GProps
    from OCC.Core.BRepGProp import brepgprop
    from osdagbridge.core.bridge_components.sub_structure.pier_cap.builder import build_pier_cap
    for style in ("HAMMERHEAD", "TRAPEZOIDAL"):
        lay = _layout(pier_cap_style=style)[0]["components"]["pier_caps"][0]
        props = GProp_GProps()
        brepgprop.VolumeProperties(build_pier_cap(lay)["concrete"], props)
        assert props.Mass() == pytest.approx(lay["concrete"]["volume_mm3"], rel=1e-6)


# ------------------------------------------------------------------ detailing

def test_bars_are_bent_and_anchored():
    s = _layout()[0]["components"]
    pier_main = [b for b in s["piers"][0]["bars"] if b["role"] == "MAIN"]
    assert all(len(b["path"]) == 4 for b in pier_main)          # L-bends at foot and head
    u_bars = [b for b in s["pile_caps"][0]["bars"] if b["dia"] == 16]
    assert all(len(b["path"]) == 4 for b in u_bars)             # bottom mat U-bars
    cap_main = [b for b in s["pier_caps"][0]["bars"] if b["role"] == "MAIN"]
    assert all(len(b["path"]) >= 4 for b in cap_main)           # bent at both tips
    assert s["pedestals"][0]["bars"]                            # pedestal steel present


def test_development_length_is456():
    # Ld = 0.87 fy phi / (4 tau_bd), tau_bd(M35) = 1.7 x 1.6
    assert development_length(16, 35) == pytest.approx(0.87 * 500 * 16 / (4 * 1.7 * 1.6))


def test_detailing_checks_flag_task_defaults_and_clear_when_fixed():
    p = SubstructureParams()
    warn = {c["check"] for c in run_detailing_checks(p, _layout()) if c["status"] == "WARN"}
    assert {"Pile spacing", "Edge clearance beyond outer pile face"} <= warn
    fixed = SubstructureParams(pile_spacing=1200, pile_cap_width=1900, pile_cap_length=1900,
                               pile_cap_depth=650, rebar=RebarParams(cover=50))
    sups = substructure_layout(fixed, span_length=25000, soffit_z=-710, deck_width=16450,
                               girder_y_positions=[0.0])
    checks = run_detailing_checks(fixed, sups)
    assert len(checks) >= 18
    assert [c["check"] for c in checks if c["status"] == "WARN"] == []


def test_ifc_girders_and_pedestals_match_design(ifc_file):
    webs = [p for p in ifc_file.by_type("IfcPlate") if (p.Name or "").startswith("Girder Web")]
    assert len(webs) == 5                                       # DTO num_girders
    peds = [e for e in ifc_file.by_type("IfcBuildingElementProxy") if e.ObjectType == "Pedestal"]
    assert len(peds) == 2 * 5
    cap = next(b for b in ifc_file.by_type("IfcBeam") if b.ObjectType == "PierCap")
    assert cap.Representation.Representations[0].Items[0].is_a("IfcFacetedBrep")
