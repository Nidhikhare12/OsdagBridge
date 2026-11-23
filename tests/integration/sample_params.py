"""Sample BridgeParametersDTO used by the substructure / IFC tests (copied from
desktop/ui/cad_3d.py::main so the tests run without the Qt GUI)."""
from osdagbridge.core.bridge_types.plate_girder.dto import (
    BridgeParametersDTO, SectionDimsDTO, ISectionDimsDTO, ShearStudParamsDTO,
    GirderSegmentDTO,
)


def sample_params(skew_angle=0.0, **overrides):
    sd = lambda h, w: SectionDimsDTO(leg_h=h, leg_w=w, connection_type="LONGER_LEG")
    kw = dict(
        steel_grade="E 250A", concrete_grade="M35",
        span_length_L=25_000, girder_section_d=900, girder_section_bf=500,
        girder_section_bf_b=500, girder_section_tf=260, girder_section_tf_b=260,
        girder_section_tw=100, num_girders=5, girder_spacing=2_750,
        skew_angle=skew_angle,
        carriageway_width=12_000, deck_thickness=400, footpath_config="BOTH",
        footpath_width=1_500, railing_width=300,
        barrier_type="Rigid", crash_barrier_subtype="IRC-5R",
        enable_median=False, median_type="Raised Kerb",
        rail_count=3, railing_type="rcc",
        include_intermediate_stiffeners=True, intermediate_stiffener_spacing=2_000,
        intermediate_stiffener_thickness=20, intermediate_stiffener_outstand=None,
        num_end_stiffener_pairs=2, end_stiffener_thickness=30, end_stiffener_outstand=None,
        include_longitudinal_stiffeners=False, num_longitudinal_stiffeners=1,
        longitudinal_stiffener_thickness=20, longitudinal_stiffener_outstand=None,
        cross_bracing_spacing=4_000, bracing_type="X", x_bracket_option="BOTH",
        k_top_bracket=True,
        diagonal_section_type="ANGLE", diagonal_section_dims=sd(100, 50), diagonal_thickness=5,
        top_chord_section_type="ANGLE", top_chord_section_dims=sd(80, 40), top_chord_thickness=5,
        bottom_chord_section_type="ANGLE", bottom_chord_section_dims=sd(80, 40), bottom_chord_thickness=5,
        end_diaphragm_type="Cross Bracing", end_diaphragm_spacing=100, end_diaphragm_bracing_type="K",
        end_diaphragm_diagonal_section_type="ANGLE", end_diaphragm_diagonal_section_dims=sd(100, 50),
        end_diaphragm_diagonal_thickness=5,
        end_diaphragm_top_chord_section_type="ANGLE", end_diaphragm_top_chord_section_dims=sd(80, 40),
        end_diaphragm_top_chord_thickness=5,
        end_diaphragm_bottom_chord_section_type="ANGLE", end_diaphragm_bottom_chord_section_dims=sd(80, 40),
        end_diaphragm_bottom_chord_thickness=5,
        end_diaphragm_section="I_SECTION",
        end_diaphragm_dims=ISectionDimsDTO(depth=800, flange_width=250, web_thickness=12, flange_thickness=100),
        shear_stud_params=ShearStudParamsDTO(50, 70, 150, 50, 4, 305, 500),
        girder_segments=[GirderSegmentDTO(25_000, 900, 100, 260, 260, 500, 500)],
        girder_segments_dict={},
    )
    kw.update(overrides)
    return BridgeParametersDTO(**kw)
