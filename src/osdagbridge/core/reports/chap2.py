# Chapter 2: Input Parameters — exact LaTeX template match


from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_CB_LOAD,
    KEY_CB_TYPE,
    KEY_CROSS_BRACING,
    KEY_DECK_CONCRETE_GRADE_BASIC,
    KEY_DESIGN_MODE,
    KEY_DO_GAMMA_C_BASIC,
    KEY_DO_GAMMA_FLT,
    KEY_DO_GAMMA_M0,
    KEY_DO_GAMMA_M1,
    KEY_DO_GAMMA_MF,
    KEY_DO_GAMMA_S,
    KEY_DO_GAMMA_V,
    KEY_END_DIAPHRAGM,
    KEY_FOOTPATH,
    KEY_GIRDER,
    KEY_INCLUDE_MEDIAN,
    KEY_MD_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_MEMBER_ID,
    KEY_MP_CB_SELECT_GIRDERS,
    KEY_MP_CB_SPACING,
    KEY_MP_CB_TYPE,
    KEY_MP_ED_BRACING_SECTION_DESIGNATION,
    KEY_MP_ED_MEMBER_ID,
    KEY_MP_ED_SELECT_GIRDERS,
    KEY_MP_ED_TYPE,
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS,
    KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH,
    KEY_MP_GIRDER_DEPTH,
    KEY_MP_GIRDER_SYMMETRY,
    KEY_MP_GIRDER_TOP_FLANGE_THICKNESS,
    KEY_MP_GIRDER_TOP_FLANGE_WIDTH,
    KEY_MP_GIRDER_TORSIONAL_RESTRAINT,
    KEY_MP_GIRDER_TYPE,
    KEY_MP_GIRDER_WARPING_RESTRAINT,
    KEY_MP_GIRDER_WEB_THICKNESS,
    KEY_MP_GIRDER_WEB_TYPE,
    KEY_MP_STIFFENER_BEARING_THICKNESS,
    KEY_MP_STIFFENER_INTERMEDIATE,
    KEY_MP_STIFFENER_INTERMEDIATE_SPACING,
    KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS,
    KEY_MP_STIFFENER_LONGITUDINAL,
    KEY_MP_STIFFENER_NO_BEARING_STIFFENERS,
    KEY_MP_STIFFENER_SPACING,
    KEY_RL_LOAD_VALUE,
    KEY_RL_TYPE,
    KEY_SD_SHEAR_DIAMETER,
    KEY_SD_SHEAR_HEIGHT,
    KEY_SD_SHEAR_STUDS_PER_SECTION,
    KEY_SD_SHEAR_ULTIMATE_STRENGTH,
    KEY_SD_SHEAR_YIELD_STRENGTH,
    KEY_SKEW_ANGLE,
    KEY_SPAN,
    KEY_STRUCTURE_TYPE,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS
)

from osdagbridge.core.reports.latex_tables import longtable, note
from osdagbridge.core.reports.report_utils import _render_value, _dim_mm, get_girder_entries, _tex


def _pv(caption, rows, label=None, layout="param_value"):
    """parameter/value table.  rows = [(parameter, value_tex), ...]"""
    body = "\n".join(r"\textnormal{" + p + r"} & " + v + r" \\" + "\n\\hline" for p, v in rows)
    return longtable(layout, caption,
                     ["parameter", "value"], body, label=label) + "\n"


def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    rv = lambda key, unit="": _render_value(input_dict, key, unit)

    comp_rows = [
        ("Crash Barrier Type", rv(KEY_CB_TYPE)),
        ("Crash Barrier Load (kN/m)", rv(KEY_CB_LOAD)),
    ]
    # Median row only shown when the user included a median
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        comp_rows.append(("Median Type", rv(KEY_MD_TYPE)))
    comp_rows += [
        ("Railing Type", rv(KEY_RL_TYPE)),
        ("Railing Load (kN/m)", rv(KEY_RL_LOAD_VALUE)),
        ("Wearing Course Material", rv(KEY_WC_MATERIAL)),
        ("Wearing Course Thickness (mm)", rv(KEY_WC_THICKNESS, " mm")),
    ]

    return r"""
\chapter{Input Parameters}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}

\vspace{4pt}
""" + _pv("Project Location", [
        ("Project Location", _tex(m.project_location)),
        ("Latitude / Longitude", rv('latitude') + ', ' + rv('longitude')),
        ("Seismic Zone (IRC 6)", rv('seismic_zone')),
        ("Basic Wind Speed (IRC 6)", rv('wind_speed', ' m/s')),
        ("Shade Temp. Max / Min (IRC 6)", rv('shade_temp_max') + r" $^\circ$C / " + rv('shade_temp_min') + r" $^\circ$C"),
    ], label="tab:project-location") + _pv("Bridge Geometry", [
        ("Type of Structure", rv(KEY_STRUCTURE_TYPE)),
        ("Span (m)", rv(KEY_SPAN, ' m')),
        ("Carriageway Width (m)", rv(KEY_CARRIAGEWAY_WIDTH, ' m')),
        ("Include Median", rv(KEY_INCLUDE_MEDIAN)),
        ("Footpath", rv(KEY_FOOTPATH)),
        ("Skew Angle (degrees)", rv(KEY_SKEW_ANGLE, r'$^\circ$') + r" (IRC 24 Cl. 504.8 limit: $\pm 15^\circ$)"),
    ], label="tab:bridge-geometry") + _pv("Material Selection", [
        ("Girder Steel Grade (IS 2062)", rv(KEY_GIRDER)),
        ("Cross Bracing Steel Grade", rv(KEY_CROSS_BRACING)),
        ("End Diaphragm Steel Grade", rv(KEY_END_DIAPHRAGM)),
        ("Concrete Deck Grade (IRC 22)", rv(KEY_DECK_CONCRETE_GRADE_BASIC)),
    ], label="tab:material") + r"""

\clearpage
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\vspace{4pt}
""" + _pv("Typical Section Details", [
        ("Overall Bridge Width (m)", rv(KEY_TS_OVERALL_WIDTH, ' m')),
        ("No. of Girders", rv(KEY_TS_NO_OF_GIRDERS)),
        ("Girder Spacing (m)", rv(KEY_TS_GIRDER_SPACING, ' m')),
        ("Deck Overhang Width (m)", rv(KEY_TS_DECK_OVERHANG, ' m')),
        ("Deck Thickness (mm)", rv(KEY_TS_DECK_THICKNESS, ' mm')),
        ("Footpath Width (m)", rv(KEY_TS_FOOTPATH_WIDTH, ' m') + r" (IRC 5 Cl. 104.3.6 min: 1.5 m)"),
        ("No. of Traffic Lanes", rv(KEY_WC_LD_LANE_TABLE_COUNT) + r" (per IRC 5 Cl. 104.3.1)"),
    ]) + _pv("Components Details", comp_rows) + _girder_tables(input_dict, n_girders) + _bracing_tables(input_dict, n_girders) + _shear_connector_table(input_dict, output_dict) + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    # Backend labels follow the pattern  KEY.G{i}.M1  (defaults.py)
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", "M1") for i in range(1, n + 1)]
    rv = lambda key, unit="": _render_value(input_dict, key, unit)
    mm = lambda key: _dim_mm(input_dict, key)

    gen_rows, dim_rows, rst_rows = [], [], []
    for i, (g_lbl, m_id) in enumerate(girder_entries, start=1):
        gen_rows.append(" & ".join([
            g_lbl, m_id, rv(KEY_DESIGN_MODE), rv(f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"),
            rv(f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1")]) + r" \\" + "\n\\hline")
        # NOTE: dimensions are stored in metres by the designer -> shown in mm
        dim_rows.append(" & ".join([
            g_lbl,
            mm(f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1"),
            mm(f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1"),
            mm(f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1") + ", " + mm(f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1"),
            mm(f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1") + ", " + mm(f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1"),
        ]) + r" \\" + "\n\\hline")
        rst_rows.append(" & ".join([
            g_lbl,
            rv(f"{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1") + ", " + rv(f"{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1"),
            rv(f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1"),
            rv(f"{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1") + "; Spacing: "
            + rv(f"{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1", " mm") + "; Thickness: "
            + rv(f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1", " mm"),
            rv(f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1"),
            "No.: " + rv(f"{KEY_MP_STIFFENER_NO_BEARING_STIFFENERS}.G{i}.M1") + "; Spacing: "
            + rv(f"{KEY_MP_STIFFENER_SPACING}.G{i}.M1", " mm") + "; Thickness: "
            + rv(f"{KEY_MP_STIFFENER_BEARING_THICKNESS}.G{i}.M1", " mm"),
        ]) + r" \\" + "\n\\hline")

    return "\n".join([
        longtable("girder_general", "Girder General Information",
                  ["Girder", "Member ID", "Design Mode", "Girder Type", "Girder Symmetry"],
                  "\n".join(gen_rows)),
        longtable("girder_dims", "Girder Section Dimensions",
                  ["Girder", "Total Depth, D (mm)", r"Web, $t_w$ (mm)",
                   r"Top Flange ($b_{tf}$, $t_{tf}$) mm", r"Bottom Flange ($b_{bf}$, $t_{bf}$) mm"],
                  "\n".join(dim_rows)),
        longtable("girder_restraint", "Girder Restraint and Stiffener Details",
                  ["Girder", "Torsional / Warping Restraint", "Web Philosophy",
                   "Intermediate Stiffeners", "Longitudinal Stiffeners", "Bearing Stiffener"],
                  "\n".join(rst_rows)),
    ])


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    rv = lambda key, unit="": _render_value(input_dict, key, unit)
    cb_rows, ed_rows = [], []
    for i in range(1, n):
        cb_rows.append(" & ".join([
            rv(f"{KEY_MP_CB_SELECT_GIRDERS}.G{i}G{i+1}.B{i}M1"),
            rv(f"{KEY_MP_CB_MEMBER_ID}.G{i}G{i+1}.B{i}M1"),
            rv(f"{KEY_MP_CB_TYPE}.G{i}G{i+1}.B{i}M1"),
            rv(f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.B{i}M1"),
            rv(f"{KEY_MP_CB_SPACING}.G{i}G{i+1}.B{i}M1", " m"),
        ]) + r" \\" + "\n\\hline")
        ed_rows.append(" & ".join([
            rv(f"{KEY_MP_ED_SELECT_GIRDERS}.G{i}G{i+1}.E{i}M1"),
            rv(f"{KEY_MP_ED_MEMBER_ID}.G{i}G{i+1}.E{i}M1"),
            rv(f"{KEY_MP_ED_TYPE}.G{i}G{i+1}.E{i}M1"),
            rv(f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.E{i}M1"),
        ]) + r" \\" + "\n\\hline")
    return "\n".join([
        longtable("bracing_members", "Member Properties: Cross Bracing Details",
                  ["Location", "Member IDs", "Type of Bracing", "Bracing Section", "Spacing (m)"],
                  "\n".join(cb_rows)),
        longtable("diaphragm_members", "Member Properties: End Diaphragm Details",
                  ["Location", "Member IDs", "Type of Bracing", "Bracing Section"],
                  "\n".join(ed_rows)),
    ])


def _shear_connector_table(input_dict, output_dict=None):
    od = output_dict or {}      # stud properties are stored by store_design_results
    rv = lambda key, unit="": _render_value(od, key, unit)
    return r"\label{subsec:shear-connectors}" + "\n" + _pv("Shear Connector Details", [
        ("Stud Diameter (mm)", rv(KEY_SD_SHEAR_DIAMETER, ' mm')),
        ("Stud Height (mm)", rv(KEY_SD_SHEAR_HEIGHT, ' mm')),
        (r"Stud $f_y$ (MPa)", rv(KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa')),
        (r"Stud $f_u$ (MPa)", rv(KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa')),
        ("No. of Studs per Section", rv(KEY_SD_SHEAR_STUDS_PER_SECTION)),
    ])


def _safety_factors_table(input_dict):
    rv = lambda key: _render_value(input_dict, key)
    return r"\label{subsec:safety-factors}" + "\n" + _pv("Partial Safety Factors", [
        (r"$\gamma_{M0}$ (Yielding / Buckling)", rv(KEY_DO_GAMMA_M0)),
        (r"$\gamma_{M1}$ (Ultimate Stress)", rv(KEY_DO_GAMMA_M1)),
        (r"$\gamma_C$ (Concrete, Basic)", rv(KEY_DO_GAMMA_C_BASIC)),
        (r"$\gamma_s$ (Reinforcement)", rv(KEY_DO_GAMMA_S)),
        (r"$\gamma_v$ (Shear Connectors)", rv(KEY_DO_GAMMA_V)),
        (r"$\gamma_{fft}$ (Fatigue Load)", rv(KEY_DO_GAMMA_FLT)),
        (r"$\gamma_{Mft}$ (Fatigue Strength)", rv(KEY_DO_GAMMA_MF)),
    ]) + note(r"All values are per IRC 22 Table 1 unless user-modified.")
