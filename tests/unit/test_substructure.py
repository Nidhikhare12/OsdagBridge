"""
Unit tests for substructure builders, CAD generator integration, and IFC export.
Uses standard library unittest.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, 'src')

from osdagbridge.core.bridge_components.sub_structure.pier.builder import build_pier
from osdagbridge.core.bridge_components.sub_structure.pier_cap.builder import build_pier_cap
from osdagbridge.core.bridge_components.sub_structure.pier_rebar.builder import build_pier_rebar
from osdagbridge.core.bridge_components.foundation.pile_cap.builder import build_pile_cap
from osdagbridge.core.bridge_components.foundation.pile.builder import build_piles

from osdagbridge.core.bridge_types.plate_girder.dto import (
    BridgeParametersDTO,
    SubstructureParametersDTO,
    SectionDimsDTO,
    ISectionDimsDTO,
    ShearStudParamsDTO,
)
from osdagbridge.core.bridge_types.plate_girder.cad_generator import PlateGirderCADGenerator
from osdagbridge.core.ifc_export_bridge.bridge_cad_extraction import PlateGirderIFCExtractor
from osdagbridge.core.ifc_export_bridge.bridge_ifc_generator import BridgeIfcGenerator


def _make_dummy_dto(with_substructure=True):
    sub = SubstructureParametersDTO() if with_substructure else None
    return BridgeParametersDTO(
        steel_grade="E250",
        concrete_grade="M35",
        span_length_L=20000.0,
        girder_section_d=1500.0,
        girder_section_bf=400.0,
        girder_section_bf_b=400.0,
        girder_section_tf=25.0,
        girder_section_tf_b=25.0,
        girder_section_tw=12.0,
        num_girders=2,
        girder_spacing=2500.0,
        skew_angle=0.0,
        carriageway_width=7500.0,
        deck_thickness=200.0,
        footpath_config="NONE",
        footpath_width=1500.0,
        railing_width=375.0,
        barrier_type="Rigid",
        crash_barrier_subtype="IRC-5R",
        enable_median=False,
        median_type="Raised Kerb",
        rail_count=3,
        railing_type="rcc",
        include_intermediate_stiffeners=True,
        intermediate_stiffener_spacing=2000.0,
        intermediate_stiffener_thickness=12.0,
        intermediate_stiffener_outstand=180.0,
        num_end_stiffener_pairs=2,
        end_stiffener_thickness=20.0,
        end_stiffener_outstand=180.0,
        include_longitudinal_stiffeners=False,
        num_longitudinal_stiffeners=1,
        longitudinal_stiffener_thickness=12.0,
        longitudinal_stiffener_outstand=180.0,
        cross_bracing_spacing=5000.0,
        bracing_type="X",
        x_bracket_option="NONE",
        k_top_bracket=False,
        diagonal_section_type="ANGLE",
        diagonal_section_dims=SectionDimsDTO(leg_h=100.0, leg_w=100.0, connection_type="LONGER_LEG"),
        diagonal_thickness=10.0,
        top_chord_section_type="ANGLE",
        top_chord_section_dims=SectionDimsDTO(leg_h=100.0, leg_w=100.0, connection_type="LONGER_LEG"),
        top_chord_thickness=10.0,
        bottom_chord_section_type="ANGLE",
        bottom_chord_section_dims=SectionDimsDTO(leg_h=100.0, leg_w=100.0, connection_type="LONGER_LEG"),
        bottom_chord_thickness=10.0,
        end_diaphragm_type="Cross Bracing",
        end_diaphragm_spacing=0.0,
        end_diaphragm_bracing_type="X",
        end_diaphragm_diagonal_section_type="ANGLE",
        end_diaphragm_diagonal_section_dims=SectionDimsDTO(leg_h=100.0, leg_w=100.0, connection_type="LONGER_LEG"),
        end_diaphragm_diagonal_thickness=10.0,
        end_diaphragm_top_chord_section_type="ANGLE",
        end_diaphragm_top_chord_section_dims=SectionDimsDTO(leg_h=100.0, leg_w=100.0, connection_type="LONGER_LEG"),
        end_diaphragm_top_chord_thickness=10.0,
        end_diaphragm_bottom_chord_section_type="ANGLE",
        end_diaphragm_bottom_chord_section_dims=SectionDimsDTO(leg_h=100.0, leg_w=100.0, connection_type="LONGER_LEG"),
        end_diaphragm_bottom_chord_thickness=10.0,
        end_diaphragm_section="I_SECTION",
        end_diaphragm_dims=ISectionDimsDTO(depth=300.0, flange_width=150.0, web_thickness=8.0, flange_thickness=12.0),
        substructure=sub,
    )


class TestSubstructure(unittest.TestCase):

    def test_pier_builder_solid(self):
        res = build_pier(pier_height=4000.0, pier_diameter=1200.0, wall_thickness=0.0, num_piers=2)
        self.assertIn("pier_shafts", res)
        self.assertEqual(len(res["pier_shafts"]), 2)

    def test_pier_builder_hollow(self):
        res = build_pier(pier_height=4000.0, pier_diameter=1200.0, wall_thickness=200.0, num_piers=2)
        self.assertIn("pier_shafts", res)
        self.assertEqual(len(res["pier_shafts"]), 2)

    def test_pier_cap_builder(self):
        res = build_pier_cap(cap_length=5000.0, cap_depth=800.0, cap_height=1000.0)
        self.assertIn("pier_caps", res)
        self.assertEqual(len(res["pier_caps"]), 1)

    def test_pile_cap_builder(self):
        res = build_pile_cap(cap_len_x=4000.0, cap_len_y=4000.0, cap_thickness=1200.0)
        self.assertIn("pile_caps", res)
        self.assertEqual(len(res["pile_caps"]), 1)

    def test_piles_builder(self):
        res = build_piles(pile_diameter=600.0, pile_length=12000.0, pile_rows=2, pile_cols=3)
        self.assertIn("piles", res)
        self.assertEqual(len(res["piles"]), 6)

    def test_pier_rebar_builder(self):
        res = build_pier_rebar(
            pier_height=4000.0,
            pier_diameter=1200.0,
            num_main_bars=12,
            tie_spacing=200.0,
            num_piers=2,
        )
        self.assertIn("pier_rebar", res)
        self.assertGreater(len(res["pier_rebar"]), 0)

    def test_cad_generator_integration(self):
        gen = PlateGirderCADGenerator()
        dto = _make_dummy_dto(with_substructure=True)
        res = gen.generate(dto)

        self.assertIn("pier_shafts", res)
        self.assertIn("pier_caps", res)
        self.assertIn("pile_caps", res)
        self.assertIn("piles", res)
        self.assertIn("pier_rebar", res)

    def test_ifc_export_substructure(self):
        import ifcopenshell

        dto = _make_dummy_dto(with_substructure=True)
        gen = PlateGirderCADGenerator()
        gen.model_data = gen.generate(dto)

        extractor = PlateGirderIFCExtractor(dto)
        extracted = extractor.extract()

        self.assertIn("substructure", extracted)
        sub = extracted["substructure"]
        self.assertGreater(len(sub.get("pier_shafts", [])), 0)
        self.assertGreater(len(sub.get("pier_caps", [])), 0)
        self.assertGreater(len(sub.get("pile_caps", [])), 0)
        self.assertGreater(len(sub.get("piles", [])), 0)
        self.assertGreater(len(sub.get("pier_rebar", [])), 0)

        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            ifc_path = tmp.name

        try:
            ifc_gen = BridgeIfcGenerator(ifc_path)
            ifc_gen.generate_from_extracted_data(extracted, gen)
            self.assertTrue(os.path.exists(ifc_path))
            self.assertGreater(os.path.getsize(ifc_path), 1000)

            # Open and inspect the exported IFC model
            model = ifcopenshell.open(ifc_path)
            piles = model.by_type("IfcPile")
            self.assertGreater(len(piles), 0)

            # Verify that every pile uses an upward +Z extrusion vector and positive depth
            for pile in piles:
                placement = pile.ObjectPlacement.RelativePlacement
                # Axis direction must be positive Z (0, 0, 1) to prevent inverted rendering in BIM viewers
                self.assertAlmostEqual(placement.Axis.DirectionRatios[0], 0.0)
                self.assertAlmostEqual(placement.Axis.DirectionRatios[1], 0.0)
                self.assertAlmostEqual(placement.Axis.DirectionRatios[2], 1.0)

                # Base Z must be lower than pile top (pile extends downward from cap)
                self.assertLess(placement.Location.Coordinates[2], -4.0)

                # Representation solid depth must equal pile length (5.0 m)
                rep = pile.Representation.Representations[0]
                solid = rep.Items[0]
                self.assertEqual(solid.is_a(), "IfcExtrudedAreaSolid")
                self.assertAlmostEqual(solid.Depth, 5.0)

            # Verify pier cap beams and footings exist
            footings = model.by_type("IfcFooting")
            self.assertGreater(len(footings), 0)

        finally:
            if os.path.exists(ifc_path):
                os.remove(ifc_path)


if __name__ == "__main__":
    unittest.main()
