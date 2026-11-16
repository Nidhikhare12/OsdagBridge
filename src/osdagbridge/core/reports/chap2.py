# Chapter 2: Input Parameters — structured tables with repeated headers

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
    KEY_WC_THICKNESS,
)

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex
from osdagbridge.core.reports.latex.tables import ReportTable, KeyValueTable


def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)

    # 1. Project Location Table
    t_loc = KeyValueTable(
        caption=r"\textbf{Project Location}",
        label="subsec:project-location",
        preset=("5.5cm", "8.5cm"),
        headers=("parameter", "value"),
        rows=[
            (r"\textnormal{Project Location}", _tex(m.project_location)),
            (r"\textnormal{Latitude / Longitude}", f"{_render_value(input_dict, 'latitude')}, {_render_value(input_dict, 'longitude')}"),
            (r"\textnormal{Seismic Zone (IRC 6)}", _render_value(input_dict, 'seismic_zone')),
            (r"\textnormal{Basic Wind Speed (IRC 6)}", _render_value(input_dict, 'wind_speed', ' m/s')),
            (r"\textnormal{Shade Temp. Max / Min (IRC 6)}", f"{_render_value(input_dict, 'shade_temp_max', '')} °C / {_render_value(input_dict, 'shade_temp_min', '')} °C"),
        ],
    )

    # 2. Bridge Geometry Table
    t_geom = KeyValueTable(
        caption=r"\textbf{Bridge Geometry}",
        label="subsec:bridge-geometry",
        preset=("5.5cm", "8.5cm"),
        headers=("parameter", "value"),
        rows=[
            (r"\textnormal{Type of Structure}", _render_value(input_dict, KEY_STRUCTURE_TYPE)),
            (r"\textnormal{Span (m)}", _render_value(input_dict, KEY_SPAN, ' m')),
            (r"\textnormal{Carriageway Width (m)}", _render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')),
            (r"\textnormal{Include Median}", _render_value(input_dict, KEY_INCLUDE_MEDIAN)),
            (r"\textnormal{Footpath}", _render_value(input_dict, KEY_FOOTPATH)),
            (r"\textnormal{Skew Angle (degrees)}", f"{_render_value(input_dict, KEY_SKEW_ANGLE, '°')} (IRC 24 Cl. 504.8 limit: $\\pm$15°)"),
        ],
    )

    # 3. Material Selection Table
    t_mat = KeyValueTable(
        caption=r"\textbf{Material Selection}",
        label="subsec:material",
        preset=("5.5cm", "8.5cm"),
        headers=("parameter", "value"),
        rows=[
            (r"\textnormal{Girder Steel Grade (IS 2062)}", _render_value(input_dict, KEY_GIRDER)),
            (r"\textnormal{Cross Bracing Steel Grade}", _render_value(input_dict, KEY_CROSS_BRACING)),
            (r"\textnormal{End Diaphragm Steel Grade}", _render_value(input_dict, KEY_END_DIAPHRAGM)),
            (r"\textnormal{Concrete Deck Grade (IRC 22)}", _render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)),
        ],
    )

    # 4. Typical Section Details
    t_sec = KeyValueTable(
        caption=r"\textbf{Typical Section Details}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            (r"\textnormal{Overall Bridge Width (m)}", _render_value(input_dict, KEY_TS_OVERALL_WIDTH)),
            (r"\textnormal{No. of Girders}", _render_value(input_dict, KEY_TS_NO_OF_GIRDERS)),
            (r"\textnormal{Girder Spacing (m)}", _render_value(input_dict, KEY_TS_GIRDER_SPACING, ' m')),
            (r"\textnormal{Deck Overhang Width (m)}", _render_value(input_dict, KEY_TS_DECK_OVERHANG, ' m')),
            (r"\textnormal{Deck Thickness (mm)}", _render_value(input_dict, KEY_TS_DECK_THICKNESS, ' mm')),
            (r"\textnormal{Footpath Width (m)}", f"{_render_value(input_dict, KEY_TS_FOOTPATH_WIDTH, ' m')} (IRC 5 Cl. 104.3.6 min: 1.5 m)"),
            (r"\textnormal{No. of Traffic Lanes}", f"{_render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT)} (per IRC 5 Cl. 104.3.1)"),
        ],
    )

    # 5. Components Details
    comp_rows = [
        (r"\textnormal{Crash Barrier Type}", _render_value(input_dict, KEY_CB_TYPE)),
        (r"\textnormal{Crash Barrier Load (kN/m)}", _render_value(input_dict, KEY_CB_LOAD)),
    ]
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        comp_rows.append((r"\textnormal{Median Type}", _render_value(input_dict, KEY_MD_TYPE)))
    comp_rows.extend([
        (r"\textnormal{Railing Type}", _render_value(input_dict, KEY_RL_TYPE)),
        (r"\textnormal{Railing Load (kN/m)}", _render_value(input_dict, KEY_RL_LOAD_VALUE)),
        (r"\textnormal{Wearing Course Material}", _render_value(input_dict, KEY_WC_MATERIAL)),
        (r"\textnormal{Wearing Course Thickness (mm)}", _render_value(input_dict, KEY_WC_THICKNESS, ' mm')),
    ])

    t_comp = KeyValueTable(
        caption=r"\textbf{Components Details}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=comp_rows,
    )

    return rf"""
\chapter{{Input Parameters}}

\setlength{{\abovecaptionskip}}{{2pt}}
\setlength{{\belowcaptionskip}}{{2pt}}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{{}}).

\section{{Basic Inputs (User-Defined)}}
\label{{sec:basic-inputs}}

\noindent\textit{{Note: These inputs are mandatory and were provided by the user.}}

{t_loc.dumps()}
\vspace{{0.4cm}}

{t_geom.dumps()}
\vspace{{0.4cm}}

{t_mat.dumps()}
\vspace{{0.4cm}}

\newpage
\section{{Additional Inputs}}
\label{{sec:additional-inputs}}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\vspace{{0.8cm}}

{t_sec.dumps()}

\vspace{{0.8em}}
{t_comp.dumps()}

{_girder_tables(input_dict, n_girders)}

{_bracing_tables(input_dict, n_girders)}

{_shear_connector_table(input_dict, output_dict)}

{_safety_factors_table(input_dict)}
"""


def _girder_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]

    entries_for_table = [
        (lbl, mid, i)
        for i, (lbl, mid) in enumerate(girder_entries, start=1)
    ]

    # 1. Girder General Information
    t_gen = ReportTable(
        columns="|L{2.2cm}|L{1.8cm}|p{3.8cm}|p{3.8cm}|p{3.8cm}|",
        caption=r"\textbf{Girder General Information}",
        header_rows=[["Girder", "Member ID", "Design Mode", "Girder Type", "Girder Symmetry"]],
    )
    for g_lbl, m_id, i in entries_for_table:
        t_gen.add_row([
            g_lbl,
            m_id,
            _render_value(input_dict, KEY_DESIGN_MODE),
            _render_value(input_dict, f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"),
            _render_value(input_dict, f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1"),
        ])

    # 2. Girder Section Dimensions
    t_dim = ReportTable(
        columns="|L{1.8cm}|L{2.3cm}|L{1.8cm}|p{4.8cm}|p{4.8cm}|",
        caption=r"\textbf{Girder Section Dimensions}",
        header_rows=[[
            "Girder",
            "Total Depth, D (mm)",
            r"Web, $t_w$ (mm)",
            r"Top Flange (b\textsubscript{tf}, t\textsubscript{tf}) mm",
            r"Bottom Flange (b\textsubscript{bf}, t\textsubscript{bf}) mm",
        ]],
    )
    for g_lbl, _, i in entries_for_table:
        t_dim.add_row([
            g_lbl,
            _render_value(input_dict, f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1", " mm"),
            _render_value(input_dict, f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1", " mm"),
            f"{_render_value(input_dict, f'{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1', ' mm')}, {_render_value(input_dict, f'{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1', ' mm')}",
            f"{_render_value(input_dict, f'{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1', ' mm')}, {_render_value(input_dict, f'{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1', ' mm')}",
        ])

    # 3. Girder Restraint and Stiffener Details
    t_rst = ReportTable(
        columns="|L{1.4cm}|p{2.2cm}|p{2.2cm}|p{3.0cm}|p{2.4cm}|p{2.2cm}|",
        caption=r"\textbf{Girder Restraint and Stiffener Details}",
        header_rows=[[
            "Girder",
            "Torsional / Warping Restraint",
            "Web Philosophy",
            "Intermediate Stiffeners",
            "Longitudinal Stiffeners",
            "Bearing Stiffener",
        ]],
    )
    for g_lbl, _, i in entries_for_table:
        t_rst.add_row([
            g_lbl,
            f"{_render_value(input_dict, f'{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1')}, {_render_value(input_dict, f'{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1')}",
            _render_value(input_dict, f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1"),
            f"{_render_value(input_dict, f'{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1')}; Spacing: {_render_value(input_dict, f'{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1', ' mm')}; Thickness: {_render_value(input_dict, f'{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1', ' mm')}",
            _render_value(input_dict, f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1"),
            f"No.: {_render_value(input_dict, f'{KEY_MP_STIFFENER_NO_BEARING_STIFFENERS}.G{i}.M1')}; Spacing: {_render_value(input_dict, f'{KEY_MP_STIFFENER_SPACING}.G{i}.M1', ' mm')}; Thickness: {_render_value(input_dict, f'{KEY_MP_STIFFENER_BEARING_THICKNESS}.G{i}.M1', ' mm')}",
        ])

    return rf"""
\newpage

\vspace{{0.4em}}
\noindent

\vspace{{4pt}}
{t_gen.dumps()}

\vspace{{0.6em}}

\vspace{{4pt}}
{t_dim.dumps()}

\vspace{{0.6em}}

\vspace{{4pt}}
{t_rst.dumps()}
"""


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    panels = [
        (
            _render_value(input_dict, f"{KEY_MP_CB_SELECT_GIRDERS}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_CB_MEMBER_ID}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_SELECT_GIRDERS}.G{i}G{i+1}.E{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_MEMBER_ID}.G{i}G{i+1}.E{i}M1"),
            i,
        )
        for i in range(1, n)
    ]

    t_cb = ReportTable(
        columns="|L{2.2cm}|L{2.2cm}|L{3.0cm}|L{2.5cm}|C{2.0cm}|",
        caption=r"\textbf{Member Properties: Cross Bracing Details}",
        header_rows=[["Location", "Member IDs", "Type of Bracing", "Bracing Section", "Spacing (m)"]],
    )
    for cb_loc, cb_ids, _, _, i in panels:
        t_cb.add_row([
            cb_loc,
            cb_ids,
            _render_value(input_dict, f"{KEY_MP_CB_TYPE}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_CB_SPACING}.G{i}G{i+1}.B{i}M1", " m"),
        ])

    t_ed = ReportTable(
        columns="|L{2.5cm}|L{2.5cm}|L{3.5cm}|L{3.5cm}|",
        caption=r"\textbf{Member Properties: End Diaphragm Details}",
        header_rows=[["Location", "Member IDs", "Type of Bracing", "Bracing Section"]],
    )
    for _, _, ed_loc, ed_ids, i in panels:
        t_ed.add_row([
            ed_loc,
            ed_ids,
            _render_value(input_dict, f"{KEY_MP_ED_TYPE}.G{i}G{i+1}.E{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.E{i}M1"),
        ])

    return rf"""
\newpage

\vspace{{0.4em}}

{t_cb.dumps()}

\vspace{{0.4em}}
\noindent

{t_ed.dumps()}
"""


def _shear_connector_table(input_dict, output_dict=None):
    od = output_dict or {}
    t_sc = KeyValueTable(
        caption=r"\textbf{Shear Connector Details}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            (r"\textnormal{Stud Diameter (mm)}", _render_value(od, KEY_SD_SHEAR_DIAMETER, " mm")),
            (r"\textnormal{Stud Height (mm)}", _render_value(od, KEY_SD_SHEAR_HEIGHT, " mm")),
            (r"\textnormal{Stud $f_y$ (MPa)}", _render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, " MPa")),
            (r"\textnormal{Stud $f_u$ (MPa)}", _render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, " MPa")),
            (r"\textnormal{No. of Studs per Section}", _render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION)),
        ],
    )
    return rf"""
\label{{subsec:shear-connectors}}

\vspace{{2.2em}}

\vspace{{0.4em}}
{t_sc.dumps()}
"""


def _safety_factors_table(input_dict):
    t_sf = KeyValueTable(
        caption=r"\textbf{Partial Safety Factors}",
        preset=("5.5cm", "10.0cm"),
        headers=("parameter", "value"),
        rows=[
            (r"\textnormal{$\gamma_{M0}$ (Yielding / Buckling)}", _render_value(input_dict, KEY_DO_GAMMA_M0)),
            (r"\textnormal{$\gamma_{M1}$ (Ultimate Stress)}", _render_value(input_dict, KEY_DO_GAMMA_M1)),
            (r"\textnormal{$\gamma_C$ (Concrete, Basic)}", _render_value(input_dict, KEY_DO_GAMMA_C_BASIC)),
            (r"\textnormal{$\gamma_s$ (Reinforcement)}", _render_value(input_dict, KEY_DO_GAMMA_S)),
            (r"\textnormal{$\gamma_v$ (Shear Connectors)}", _render_value(input_dict, KEY_DO_GAMMA_V)),
            (r"\textnormal{$\gamma_{fft}$ (Fatigue Load)}", _render_value(input_dict, KEY_DO_GAMMA_FLT)),
            (r"\textnormal{$\gamma_{Mft}$ (Fatigue Strength)}", _render_value(input_dict, KEY_DO_GAMMA_MF)),
        ],
    )
    return rf"""
\label{{subsec:safety-factors}}

\vspace{{2.2em}}

\vspace{{0.3em}}
\noindent\textit{{Note: All values are per IRC 22 Table 1 unless user-modified.}}

\vspace{{0.4em}}
{t_sf.dumps()}
"""
