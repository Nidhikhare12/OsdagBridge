"""
PlateGirderBridge.design_deck_slab() must pass the deck concrete modulus to
deckdesign.design_deck_slab() in MPa (issue #148).

ConcreteProperties.Ecm is stored in GPa (dto.py), while deckdesign documents Ecm
in MPa and computes the modular ratio as alpha_e = Es / Ecm (_cracked_section).
Passing the GPa value gave alpha_e = 6061 instead of 6.06 for M40 / Fe 500.
"""

import pytest

from osdagbridge.core.bridge_types.plate_girder import deckdesign
from osdagbridge.core.bridge_types.plate_girder.dto import (
    ConcreteProperties, MaterialProperties, SteelProperties,
)
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.utils.common import (
    KEY_DS_REINF_MATERIAL, KEY_DS_STUD_HEIGHT, KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
)


def test_deck_design_receives_ecm_in_mpa(monkeypatch):
    calls = []

    def fake_design_deck_slab(input_dict, **kwargs):
        calls.append(kwargs)
        return {}, {}

    monkeypatch.setattr(deckdesign, "design_deck_slab", fake_design_deck_slab)

    bridge = PlateGirderBridge()
    bridge.input_dict = {KEY_DS_REINF_MATERIAL: "Fe 500", KEY_MP_GIRDER_TOP_FLANGE_WIDTH: 0.5,
                         KEY_DS_STUD_HEIGHT: "100"}
    bridge.material_props = MaterialProperties(
        steel_prop=SteelProperties(grade="E 350A", E=200e9, v=0.3, rho=78500.0, Fy=350e6),
        concrete_prop=ConcreteProperties(grade="M40", fck=40.0, fctm=3.0, Ecm=33.0),  # GPa, as in the DB
    )
    bridge.design_results = {}
    bridge.output_dict = {}
    bridge.design_deck_slab()

    (kwargs,) = calls
    assert kwargs["Ecm"] == pytest.approx(33_000.0)  # MPa

    # Default deck, bottom mat: 12 mm bars at 175 mm (646 mm2/m), d = 194 mm.
    x, _, alpha_e = deckdesign._cracked_section(646.0, 194.0, kwargs["Es"], kwargs["Ecm"])
    assert alpha_e == pytest.approx(6.06, abs=0.01)  # was 6060.6
    assert x == pytest.approx(35.3, abs=0.1)  # neutral axis depth (mm), was 189.4
