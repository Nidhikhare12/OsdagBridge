"""
End Diaphragm — Welded I-Beam (Plate Girder) Module
===================================================
Encapsulates force resolution and design dispatch for End Diaphragm members configured as Welded I-Beams.
"""

from typing import TYPE_CHECKING
import copy

from osdagbridge.core.bridge_types.plate_girder.transverse_design_utility import TransverseMemberDesignUtility
from osdagbridge.core.bridge_types.plate_girder.results_data import extract_ed_beam_summary
from osdagbridge.core.utils.common import (
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_TS_GIRDER_SPACING,
)
from osdagbridge.core.utils.connect import design_dict_plate_girder_welded, run_calculation

if TYPE_CHECKING:
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge


class EndDiaphragmWelded:
    """
    Handles resolution of beam forces (Vy, Mz) and execution of Osdag Plate Girder
    (Welded Beam) design checks specifically for End Diaphragms.
    """

    def __init__(self, bridge: "PlateGirderBridge", pair_to_elements: dict[str, list[str]]):
        self.bridge = bridge
        self.input_dict = bridge.input_dict
        self.result_data = bridge.result_data
        self.pair_to_elements = pair_to_elements
        self.girder_spacing = float(self.input_dict.get(KEY_TS_GIRDER_SPACING, 0.0))

    def resolve_beam_forces_for_pair(self, pair: str) -> dict:
        """
        Extracts maximum shear force Vy and bending moment Mz for the edge transverse member(s)
        belonging to the given girder pair.
        """
        elements = self.pair_to_elements.get(pair, [])
        return TransverseMemberDesignUtility.resolve_beam_forces(self.result_data, elements)

    def run_welded_beam_design(self, pair: str, beam_forces: dict, member_suffix: str) -> dict:
        """
        Calls Osdag's Plate Girder (Welded Beam) design module for a single pair and enriches
        the result with demand and capacity information.
        """
        depth = float(self.input_dict.get(f"{KEY_MP_ED_TOTAL_DEPTH}{member_suffix}") or 0.0)
        web_t = float(self.input_dict.get(f"{KEY_MP_ED_WEB_THICKNESS}{member_suffix}") or 0.0)
        top_w = float(self.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_WIDTH}{member_suffix}") or 0.0)
        bot_w = float(self.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_WIDTH}{member_suffix}") or 0.0)
        top_t = float(self.input_dict.get(f"{KEY_MP_ED_TOP_FLANGE_THICKNESS}{member_suffix}") or 0.0)
        bot_t = float(self.input_dict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_THICKNESS}{member_suffix}") or 0.0)

        material = (
            self.input_dict.get(f"member_properties.material{member_suffix}")
            or self.input_dict.get("member_properties.material")
            or "E 250 (Fe 410 W)A"
        )

        d = copy.deepcopy(design_dict_plate_girder_welded)
        d["Total.Depth"] = str(int(depth))
        d["Web.Thickness"] = str(int(web_t))
        d["Topflange.Width"] = str(int(top_w))
        d["TopFlange.Thickness"] = str(int(top_t))
        d["Bottomflange.Width"] = str(int(bot_w))
        d["BottomFlange.Thickness"] = str(int(bot_t))
        d["Member.Length"] = str(int(self.girder_spacing * 1000))
        d["Load.Moment"] = str(float(beam_forces.get("moment_kNm", 0.1)))
        d["Load.Shear"] = str(float(beam_forces.get("shear_kN", 0.1)))
        d["Deflection.Max"] = float(self.girder_spacing * 1000)
        if material:
            d["Material"] = material

        try:
            raw_res = run_calculation(d)
        except Exception as e:
            print(f"  [EndDiaphragmWelded] Welded beam design failed for pair {pair}: {e}")
            raw_res = {}

        return extract_ed_beam_summary(raw_res, beam_forces)
