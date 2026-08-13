from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Union

__all__ = [
    "SectionComponent",
    "Point",
    "LineLoadGeometry",
    "PatchLoadGeometry",
    "SectionProperties",
    "MaterialProperties",
    "GrillageGeometry",
    "DeckLayoutProperties",
    "SectionDimsDTO",
    "ISectionDimsDTO",
    "ShearStudParamsDTO",
    "GirderSegmentDTO",
    "SubstructureParametersDTO",
    "BridgeParametersDTO",
]

# ------------------------------------------------------------------
# DTOs for cross-section components
# ------------------------------------------------------------------

@dataclass(frozen=True)
class SectionComponent:
    name: str
    width: float
    z_start: float
    z_end: float

    @property
    def center(self) -> float:
        return 0.5 * (self.z_start + self.z_end)


# ------------------------------------------------------------------
# DTOs for load geometry
# ------------------------------------------------------------------

@dataclass(frozen=True)
class Point:
    x: float
    z: float


@dataclass(frozen=True)
class LineLoadGeometry:
    start: Point
    end: Point


@dataclass(frozen=True)
class PatchLoadGeometry:
    p1: Point
    p2: Point
    p3: Point
    p4: Point


# ------------------------------------------------------------------
# DTOs for bridge geometry and properties (for analyser file)
# ------------------------------------------------------------------

@dataclass(frozen=True)
class SectionProperties:
    """
    Holds cross-section properties for a single grillage member.

    Attributes
    ----------
    A : float
        Cross-sectional area (m^2).
    J : float
        Torsional constant (m^3).
    Iz : float
        Second moment of area about z-axis (m^4).
    Iy : float
        Second moment of area about y-axis (m^4).
    Az : float
        Shear area in z-direction (m^2).
    Ay : float
        Shear area in y-direction (m^2).
    """
    A: float
    J: float
    Iz: float
    Iy: float
    Az: float
    Ay: float


@dataclass(frozen=True)
class SteelProperties:
    """
    Holds custom material properties for a grillage member.

    Attributes
    ----------
    grade : str
        Material type string (e.g. "steel", "concrete").
    E : float
        Elastic modulus (Pa).
    v : float
        Poisson's ratio.
    rho : float
        Density (kN/m^3).
    Fy : float, optional
        Yield strength (Pa). Required for steel.
    E0 : float, optional
        Initial elastic modulus (Pa). Required for steel.
    b : float, optional
        Strain-hardening ratio. Required for steel.
    """
    grade: str
    E: float
    v: float
    rho: float
    Fy: Optional[float] = None
    Fu: Optional[float] = None
    E0: Optional[float] = None
    b: Optional[float] = None

    def __post_init__(self) -> None:
        if self.grade == "steel":
            if any(val is None for val in (self.Fy, self.E0, self.b)):
                raise ValueError(
                    "Fy, E0, and b are all required when material is 'steel'."
                )

@dataclass(frozen=True)
class ConcreteProperties:
    """
    Holds material properties for a concrete grillage member.

    Attributes
    ----------
    grade : str
        Concrete grade designation (e.g. "M25", "M30").
    fck : float
        Characteristic compressive cylinder strength (MPa).
    fctm : float
        Mean axial tensile strength (MPa).
    Ecm : float
        Mean secant modulus of elasticity (GPa).
    """
    grade: str
    fck: float
    fctm: float
    Ecm: float

    def __post_init__(self) -> None:
        if not self.grade:
            raise ValueError("grade must not be empty.")
        if any(val is None for val in (self.fck, self.fctm, self.Ecm)):
            raise ValueError("fck, fctm, and Ecm must not be None.")

@dataclass(frozen=True)
class MaterialProperties:
    """
    Holds material type and its corresponding properties for a grillage member.

    Attributes
    ----------
    steel_prop : SteelProperties 
    concrete_prop : ConcreteProperties
    """
    steel_prop: SteelProperties
    concrete_prop: ConcreteProperties

    def __post_init__(self) -> None:
        if not isinstance(self.steel_prop, SteelProperties):
            raise ValueError("steel_prop must be a SteelProperties instance.")
        if not isinstance(self.concrete_prop, ConcreteProperties):
            raise ValueError("concrete_prop must be a ConcreteProperties instance.")

@dataclass(frozen=True)
class GrillageGeometry:
    """
    Holds grillage grid geometry parameters.

    Attributes
    ----------
    L : float
        Bridge span length (m).
    n_l : int
        Number of longitudinal grid lines.
    n_t : int
        Number of transverse grid lines.
    edge_dist : float
        Edge beam distance / overhang (m). Use 0 for no overhang.
    ext_to_int_dist : float
        Distance from exterior to interior beam (m).
    angle : float
        Skew angle in degrees. Use 0 for a right bridge.
    """
    L: float
    n_l: int
    n_t: int
    edge_dist: float
    ext_to_int_dist: float
    angle: float


@dataclass(frozen=True)
class DeckLayoutProperties:
    """
    Holds deck cross-section layout properties.

    Attributes
    ----------
    carriageway_width : float
        Width of the carriageway (m).
    crash_barrier_width : float
        Width of each crash barrier (m).
    footpath_width : float
        Width of each footpath (m).
    railing_width : float
        Width of each railing (m).
    median_width : float
        Width of the median (m). Use 0 if no median.
    n_footpaths : int
        Number of footpaths.
    """
    carriageway_width: float
    crash_barrier_width: float
    footpath_width: float
    railing_width: float
    median_width: float
    n_footpaths: int





from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Nested DTOs — only for fields that were dicts in the original config
# ---------------------------------------------------------------------------

@dataclass
class SectionDimsDTO:
    leg_h: float
    leg_w: float
    connection_type: str    # "LONGER_LEG" / "SHORTER_LEG"


@dataclass
class ISectionDimsDTO:
    depth: float
    flange_width: float
    web_thickness: float
    flange_thickness: float


@dataclass
class ShearStudParamsDTO:
    base_diameter: float
    top_diameter: float
    base_height: float
    top_height: float
    num_per_section: int
    transverse_spacing: float
    pitch: float


@dataclass
class GirderSegmentDTO:
    length: float
    D: float
    tw: float
    T_ft: float
    T_fb: float
    B_ft: float
    B_fb: float


# ---------------------------------------------------------------------------
# Main DTO
# ---------------------------------------------------------------------------

@dataclass
class BridgeParametersDTO:

    # --- Material Grades ---
    steel_grade: str
    concrete_grade: str

    # --- Girder ---
    span_length_L: float
    girder_section_d: float
    girder_section_bf: float
    girder_section_bf_b: float
    girder_section_tf: float
    girder_section_tf_b: float
    girder_section_tw: float
    num_girders: int
    girder_spacing: float

    # --- Geometry ---
    skew_angle: float

    # --- Deck ---
    carriageway_width: float
    deck_thickness: float
    footpath_config: str        # "NONE" / "LEFT" / "RIGHT" / "BOTH"
    footpath_width: float
    railing_width: float

    # --- Crash Barrier ---
    barrier_type: str           # "Rigid" / "Semi-Rigid" / "Flexible"
    crash_barrier_subtype: str

    # --- Median ---
    enable_median: bool
    median_type: str

    # --- Railing ---
    rail_count: int
    railing_type: str           # "rcc" / "steel"

    # --- Intermediate Stiffeners ---
    include_intermediate_stiffeners: bool
    intermediate_stiffener_spacing: float
    intermediate_stiffener_thickness: float
    intermediate_stiffener_outstand: Optional[float]

    # --- End Stiffeners ---
    num_end_stiffener_pairs: int
    end_stiffener_thickness: float
    end_stiffener_outstand: Optional[float]

    # --- Longitudinal Stiffeners ---
    include_longitudinal_stiffeners: bool
    num_longitudinal_stiffeners: int
    longitudinal_stiffener_thickness: float
    longitudinal_stiffener_outstand: Optional[float]

    # --- Cross Bracing ---
    cross_bracing_spacing: float
    bracing_type: str           # "X" / "K"
    x_bracket_option: str       # "NONE" / "UPPER" / "LOWER" / "BOTH"
    k_top_bracket: bool

    diagonal_section_type: str
    diagonal_section_dims: SectionDimsDTO
    diagonal_thickness: float

    top_chord_section_type: str
    top_chord_section_dims: SectionDimsDTO
    top_chord_thickness: float

    bottom_chord_section_type: str
    bottom_chord_section_dims: SectionDimsDTO
    bottom_chord_thickness: float

    # --- End Diaphragm ---
    end_diaphragm_type: str     # "Cross Bracing" / "Rolled Beam" / "Welded Beam"
    end_diaphragm_spacing: float
    end_diaphragm_bracing_type: str     # "X" / "K"

    end_diaphragm_diagonal_section_type: str
    end_diaphragm_diagonal_section_dims: SectionDimsDTO
    end_diaphragm_diagonal_thickness: float

    end_diaphragm_top_chord_section_type: str
    end_diaphragm_top_chord_section_dims: SectionDimsDTO
    end_diaphragm_top_chord_thickness: float

    end_diaphragm_bottom_chord_section_type: str
    end_diaphragm_bottom_chord_section_dims: SectionDimsDTO
    end_diaphragm_bottom_chord_thickness: float

    end_diaphragm_section: str
    end_diaphragm_dims: ISectionDimsDTO

    
    shear_stud_params: ShearStudParamsDTO = field(
        default_factory=lambda: ShearStudParamsDTO(
            base_diameter=50,
            top_diameter=70,
            base_height=150,
            top_height=50,
            num_per_section=4,
            transverse_spacing=305,
            pitch=500,
        )
    )

    #while segment lists can
    # remain empty to use the base girder section values.
    girder_segments: list[GirderSegmentDTO] = field(default_factory=list)
    girder_segments_dict: dict[int, list[GirderSegmentDTO]] = field(default_factory=dict)
    stiffeners_dict: dict[int, dict] = field(default_factory=dict)

    # Optional substructure parameters (None = omit substructure from 3-D model)
    substructure: Optional["SubstructureParametersDTO"] = field(default=None)


# ---------------------------------------------------------------------------
# Substructure DTO
# ---------------------------------------------------------------------------

@dataclass
class SubstructureParametersDTO:
    """
    Geometric parameters for the bridge substructure: piers, pier caps,
    pile caps, piles, and pier rebar.

    All dimensions in **millimetres** unless stated otherwise.
    Pass an instance of this class as ``BridgeParametersDTO.substructure``
    to include the substructure in the 3-D CAD model.

    Default values strictly match user specifications.
    """

    # --- Pier ---
    num_supports: int = 2
    """Number of support rows along the span (placed at ends by default)."""

    pier_x_positions: Optional[list] = None
    """Explicit X-coords of each support (mm). Auto-derived at ends [0.0, span_length_L] if None."""

    pier_diameter: float = 800.0
    """Outer diameter of each circular pier column (mm)."""

    pier_wall_thickness: float = 0.0
    """Wall thickness for hollow piers (mm).  0 = solid."""

    pier_height: float = 3000.0
    """Height of pier shaft from pile-cap top to pier-cap soffit (mm)."""

    num_piers_per_support: int = 1
    """Number of pier columns in the transverse direction per support."""

    pier_spacing: float = 2000.0
    """Centre-to-centre spacing of pier columns in Y (mm)."""

    # --- Pier cap ---
    pier_cap_top_width: float = 3000.0
    """Transverse width of the wider top face of the trapezoidal pier cap (mm)."""

    pier_cap_bottom_width: float = 1200.0
    """Transverse width of the narrower bottom face of the trapezoidal pier cap (mm)."""

    pier_cap_length: float = 3000.0
    """Alias for pier_cap_top_width; kept for backward compatibility (mm)."""

    pier_cap_depth: float = 600.0
    """Longitudinal depth of the pier cap (mm)."""

    pier_cap_height: float = 600.0
    """Vertical height of the pier cap (mm)."""

    # --- Pile cap ---
    pile_cap_len_x: float = 2200.0
    """Longitudinal length of the pile cap (mm)."""

    pile_cap_len_y: float = 1200.0
    """Transverse width of the pile cap (mm)."""

    pile_cap_thickness: float = 600.0
    """Vertical thickness of the pile cap (mm)."""

    # --- Piles ---
    pile_diameter: float = 400.0
    """Outer diameter of each bored pile (mm)."""

    pile_length: float = 5000.0
    """Length of each pile from pile-cap base downward (mm)."""

    pile_rows: int = 2
    """Number of pile rows in X (longitudinal) per pile cap (2x2 grid = 4 piles total)."""

    pile_cols: int = 2
    """Number of pile columns in Y (transverse) per pile cap (2x2 grid = 4 piles total)."""

    pile_spacing_x: float = 600.0
    """C/C pile spacing in X (mm)."""

    pile_spacing_y: float = 600.0
    """C/C pile spacing in Y (mm)."""

    # --- Pier rebar ---
    include_pier_rebar: bool = True
    """Whether to generate the pier reinforcement cage."""

    rebar_cover: float = 40.0
    """Clear cover to outer face of tie bar (mm)."""

    main_bar_diameter: float = 16.0
    """Diameter of each main vertical bar (mm)."""

    num_main_bars: int = 12
    """Number of main bars around the perimeter."""

    tie_diameter: float = 8.0
    """Diameter of each circular tie/stirrup bar (mm)."""

    tie_spacing: float = 200.0
    """Centre-to-centre spacing of tie rings (mm)."""

    # --- Additional rebar ---
    include_pile_cap_rebar: bool = True
    """Whether to generate pile cap reinforcement grids."""

    include_pier_cap_rebar: bool = True
    """Whether to generate pier cap reinforcement grids."""

    include_pile_rebar: bool = True
    """Whether to generate pile rebar cages."""

    rebar_spacing_long: float = 150.0
    """Longitudinal bar spacing for slab-type rebar grids (mm)."""

    rebar_spacing_trans: float = 200.0
    """Transverse bar spacing for slab-type rebar grids (mm)."""

