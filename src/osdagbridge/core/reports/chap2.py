# Chapter 2: Input Parameters - exact LaTeX template match


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

from osdagbridge.core.reports.report_utils import _render_value, get_girder_entries, _tex

def ch2_input_parameters(m, input_dict, output_dict=None):
    girder_entries = get_girder_entries(input_dict)
    n_girders = len(girder_entries)
    # Median row only shown when the user included a median
    median_row = ""
    if str(input_dict.get(KEY_INCLUDE_MEDIAN, "")).strip().lower() in ("yes", "true", "1"):
        median_row = (r"\textnormal{Median Type} & "
                      + _render_value(input_dict, KEY_MD_TYPE)
                      + r""" \\[6pt]
\hline
""")

    lat = _render_value(input_dict, 'latitude')
    lon = _render_value(input_dict, 'longitude')
    if lat and lon:
        lat_lon_str = f"{lat}, {lon}"
    elif lat or lon:
        lat_lon_str = lat or lon
    else:
        lat_lon_str = "-"

    seismic_zone_str = _render_value(input_dict, 'seismic_zone') or "-"
    wind_speed_str = _render_value(input_dict, 'wind_speed', ' m/s') or "-"

    t_max = _render_value(input_dict, 'shade_temp_max')
    t_min = _render_value(input_dict, 'shade_temp_min')
    if t_max and t_min:
        temp_str = f"{t_max} °C / {t_min} °C"
    elif t_max or t_min:
        temp_str = f"{t_max or t_min} °C"
    else:
        temp_str = "-"

    return r"""
\chapter{Input Parameters}

\setlength{\abovecaptionskip}{2pt}
\setlength{\belowcaptionskip}{2pt}

This section documents all inputs provided to OsdagBridge. User-provided inputs are clearly distinguished from software-assumed defaults. Where the user did not supply a value, the software has applied the IRC/IS code default or an empirical guideline; these are annotated with an asterisk (\sdstar{}).

\section{Basic Inputs (User-Defined)}
\label{sec:basic-inputs}

\noindent\textit{Note: These inputs are mandatory and were provided by the user.}

\begin{table}[H]
\caption{\textbf{Project Location}}
\label{subsec:project-location}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\
\hline
\textnormal{Project Location} & """ + _tex(m.project_location) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Latitude / Longitude} & """ + lat_lon_str + r""" \\
\hline
\textnormal{Seismic Zone (IRC 6)} & """ + seismic_zone_str + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Basic Wind Speed (IRC 6)} & """ + wind_speed_str + r""" \\
\hline
\textnormal{Shade Temp. Max / Min (IRC 6)} & """ + temp_str + r""" \\
\hline
\end{tabular}
\vspace{0.4cm}
\end{table}

\begin{table}[H]
\caption{\textbf{Bridge Geometry}}
\label{subsec:bridge-geometry}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\
\hline
\textnormal{Type of Structure} & """ + (_render_value(input_dict, KEY_STRUCTURE_TYPE)) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Span (m)} & """ + (_render_value(input_dict, KEY_SPAN, ' m')) + r""" \\
\hline
\textnormal{Carriageway Width (m)} & """ + (_render_value(input_dict, KEY_CARRIAGEWAY_WIDTH, ' m')) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Include Median} & """ + (_render_value(input_dict, KEY_INCLUDE_MEDIAN)) + r""" \\
\hline
\textnormal{Footpath} & """ + (_render_value(input_dict, KEY_FOOTPATH)) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Skew Angle (degrees)} & """ + (_render_value(input_dict, KEY_SKEW_ANGLE, '°')) + r""" (IRC 24 Cl. 504.8 limit: $\pm$15°) \\
\hline
\end{tabular}
\end{table}
\vspace{0.4cm}

\begin{table}[H]
\caption{\textbf{Material Selection}}
\label{subsec:material}
\begin{tabular}{|L{5.5cm}|L{8.5cm}|}
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\
\hline
\textnormal{Girder Steel Grade (IS 2062)} & """ + (_render_value(input_dict, KEY_GIRDER)) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Cross Bracing Steel Grade} & """ + (_render_value(input_dict, KEY_CROSS_BRACING)) + r""" \\
\hline
\textnormal{End Diaphragm Steel Grade} & """ + (_render_value(input_dict, KEY_END_DIAPHRAGM)) + r""" \\
\hline
\rowcolor{OsdagZebra}
\textnormal{Concrete Deck Grade (IRC 22)} & """ + (_render_value(input_dict, KEY_DECK_CONCRETE_GRADE_BASIC)) + r""" \\
\hline
\end{tabular}
\end{table}
\vspace{0.4cm}

\newpage
\section{Additional Inputs}
\label{sec:additional-inputs}

Where the user has modified additional inputs, those values are reported here. Where no modification was made, the software default is shown.

\vspace{0.8cm}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Typical Section Details}}\label{tab:typical-section-details} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Typical Section Details (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Overall Bridge Width (m)} & """ + (_render_value(input_dict, KEY_TS_OVERALL_WIDTH)) + r""" \\[6pt]
\hline
\textnormal{No. of Girders} & """ + (_render_value(input_dict, KEY_TS_NO_OF_GIRDERS)) + r""" \\[6pt]
\hline
\textnormal{Girder Spacing (m)} & """ + (_render_value(input_dict, KEY_TS_GIRDER_SPACING)) + r""" \\[6pt]
\hline
\textnormal{Deck Overhang Width (m)} & """ + (_render_value(input_dict, KEY_TS_DECK_OVERHANG)) + r""" \\[6pt]
\hline
\textnormal{Deck Thickness (mm)} & """ + (_render_value(input_dict, KEY_TS_DECK_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Footpath Width (m)} & """ + ("0.0 (Not provided)" if str(input_dict.get(KEY_FOOTPATH, "")).strip().lower() not in ("yes", "true", "1") else (_render_value(input_dict, KEY_TS_FOOTPATH_WIDTH) + " (IRC 5 Cl. 104.3.6 min: 1.5 m)")) + r""" \\[6pt]
\hline
\textnormal{No. of Traffic Lanes} & """ + (_render_value(input_dict, KEY_WC_LD_LANE_TABLE_COUNT) or "2") + r""" (per IRC 5 Cl. 104.3.1) \\[6pt]
\hline
\end{longtable}

\vspace{0.8em}

\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Components Details}}\label{tab:components-details} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Components Details (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Crash Barrier Type} & """ + (_render_value(input_dict, KEY_CB_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Crash Barrier Load (kN/m)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" \\[6pt]
\hline
""" + median_row + r"""
\textnormal{Railing Type} & """ + (_render_value(input_dict, KEY_RL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Railing Load (kN/m)} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" \\[6pt]
\hline
\textnormal{Wearing Course Material} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" \\[6pt]
\hline
\textnormal{Wearing Course Thickness (mm)} & """ + (_render_value(input_dict, KEY_WC_THICKNESS, ' mm')) + r""" \\[6pt]
\hline
\end{longtable}

""" + _girder_tables(input_dict, n_girders) + r"""

""" + _bracing_tables(input_dict, n_girders) + r"""

""" + _shear_connector_table(input_dict, output_dict) + r"""

""" + _safety_factors_table(input_dict)


def _girder_tables(input_dict, n_girders):
    # Fetch backend-populated labels via exact suffix pattern (defaults.py)
    # KEY_MP_GD_SELECT_GIRDER.G{i}    = 'G{i}'
    # KEY_MP_GD_MEMBER_ID.G{i}.M1     = 'G{i}M1'
    # All other girder/stiffener keys: {BASE_KEY}.G{i}.M1
    n = n_girders if n_girders >= 1 else 1
    girder_entries = get_girder_entries(input_dict)
    if not girder_entries:
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]
    
    entries_for_table = [
        (lbl, mid, i)
        for i, (lbl, mid) in enumerate(
            girder_entries,
            start=1,
        )
    ]

    def _dim_mm(val):
        if val in ("", None):
            return "-"
        try:
            f = float(val)
            if f <= 0:
                return "-"
            if f < 20.0:
                f = f * 1000.0
            if abs(f - round(f)) < 1e-4:
                return f"{int(round(f))}"
            return f"{f:.1f}"
        except (ValueError, TypeError):
            return str(val)

    # Helper: one girder-dimension row
    def _dim_row(g_lbl, i):
        d = _dim_mm(input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.G{i}.M1"))
        tw = _dim_mm(input_dict.get(f"{KEY_MP_GIRDER_WEB_THICKNESS}.G{i}.M1"))
        tfw = _dim_mm(input_dict.get(f"{KEY_MP_GIRDER_TOP_FLANGE_WIDTH}.G{i}.M1"))
        tft = _dim_mm(input_dict.get(f"{KEY_MP_GIRDER_TOP_FLANGE_THICKNESS}.G{i}.M1"))
        bfw = _dim_mm(input_dict.get(f"{KEY_MP_GIRDER_BOTTOM_FLANGE_WIDTH}.G{i}.M1"))
        bft = _dim_mm(input_dict.get(f"{KEY_MP_GIRDER_BOTTOM_FLANGE_THICKNESS}.G{i}.M1"))
        top_flange = f"{tfw} $\\times$ {tft}"
        bot_flange = f"{bfw} $\\times$ {bft}"
        return (f"{g_lbl} & {d} & {tw} & {top_flange} & {bot_flange} \\\\[8pt]\n\\hline\n")

    # Helper: one general-info row
    def _gen_row(g_lbl, m_id, i):
        return (g_lbl + r""" & """ + m_id + r""" & """
                + (_render_value(input_dict, KEY_DESIGN_MODE))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_TYPE}.G{i}.M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_GIRDER_SYMMETRY}.G{i}.M1"))
                + r""" \\[8pt]
\hline
""")

    # Helper: one restraint/stiffener row
    def _rst_row(g_lbl, i):
        tor = _render_value(input_dict, f"{KEY_MP_GIRDER_TORSIONAL_RESTRAINT}.G{i}.M1") or "Restrained"
        warp = _render_value(input_dict, f"{KEY_MP_GIRDER_WARPING_RESTRAINT}.G{i}.M1") or "Restrained"
        restraint = f"{tor}, {warp}"
        web_type = _render_value(input_dict, f"{KEY_MP_GIRDER_WEB_TYPE}.G{i}.M1") or "Thick Web"

        # Intermediate stiffeners
        has_int = str(input_dict.get(f"{KEY_MP_STIFFENER_INTERMEDIATE}.G{i}.M1", "")).strip().lower() in ("yes", "true", "1")
        if has_int:
            s_spc = _render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_SPACING}.G{i}.M1")
            s_thk = _render_value(input_dict, f"{KEY_MP_STIFFENER_INTERMEDIATE_THICKNESS}.G{i}.M1")
            int_str = f"Yes (c/c {s_spc} mm, t = {s_thk} mm)"
        else:
            int_str = "None"

        # Longitudinal stiffeners
        has_long = str(input_dict.get(f"{KEY_MP_STIFFENER_LONGITUDINAL}.G{i}.M1", "")).strip().lower() in ("yes", "true", "1")
        long_str = "Provided" if has_long else "None"

        # Bearing stiffeners
        n_brg = _render_value(input_dict, f"{KEY_MP_STIFFENER_NO_BEARING_STIFFENERS}.G{i}.M1") or "2"
        b_spc = _render_value(input_dict, f"{KEY_MP_STIFFENER_SPACING}.G{i}.M1")
        b_thk = _render_value(input_dict, f"{KEY_MP_STIFFENER_BEARING_THICKNESS}.G{i}.M1")
        if b_spc and b_thk:
            brg_str = f"{n_brg} pairs (c/c {b_spc} mm, t = {b_thk} mm)"
        else:
            brg_str = f"{n_brg} pairs"

        return f"{g_lbl} & {restraint} & {web_type} & {int_str} & {long_str} & {brg_str} \\\\[8pt]\n\\hline\n"

    gen_rows = "".join([_gen_row(g_lbl, m_id, i) for g_lbl, m_id, i in entries_for_table])
    dim_rows = "".join([_dim_row(g_lbl, i) for g_lbl, _, i in entries_for_table])
    rst_rows = "".join([_rst_row(g_lbl, i) for g_lbl, _, i in entries_for_table])

    return (r"""
\newpage

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4.0pt}
\setlength\LTleft{0pt}
\setlength\LTright\fill
            
\vspace{4pt}
\begin{longtable}{|C{1.8cm}|C{2.0cm}|C{3.0cm}|C{3.6cm}|C{4.4cm}|}
\caption{\textbf{Girder General Information}}\label{tab:girder-general-info} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Girder} & \textbf{Member ID} & \textbf{Design Mode} & \textbf{Girder Type} & \textbf{Girder Symmetry} \\[6pt]
\hline
\endfirsthead
\multicolumn{5}{c}{\small\textit{Girder General Information (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Girder} & \textbf{Member ID} & \textbf{Design Mode} & \textbf{Girder Type} & \textbf{Girder Symmetry} \\[6pt]
\hline
\endhead
\hline
\multicolumn{5}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
"""
            + gen_rows
            + r"""\end{longtable}

\vspace{0.6em}

\vspace{4pt}
\setlength{\tabcolsep}{4.0pt}
\setlength\LTleft{0pt}
\setlength\LTright\fill
\begin{longtable}{|C{1.8cm}|C{2.8cm}|C{2.4cm}|C{4.3cm}|C{4.3cm}|}
\caption{\textbf{Girder Section Dimensions}}\label{tab:girder-section-dimensions} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Girder} & \textbf{Total Depth, D (mm)} & \textbf{Web, $t_w$ (mm)} & \textbf{Top Flange (mm)} & \textbf{Bottom Flange (mm)} \\[6pt]
\hline
\endfirsthead
\multicolumn{5}{c}{\small\textit{Girder Section Dimensions (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Girder} & \textbf{Total Depth, D (mm)} & \textbf{Web, $t_w$ (mm)} & \textbf{Top Flange (mm)} & \textbf{Bottom Flange (mm)} \\[6pt]
\hline
\endhead
\hline
\multicolumn{5}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
"""
            + dim_rows
            + r"""\end{longtable}

\clearpage
\noindent
\setlength{\tabcolsep}{3.5pt}
\setlength\LTleft{0pt}
\setlength\LTright\fill
\begin{longtable}{|C{1.5cm}|L{2.8cm}|C{2.4cm}|L{3.2cm}|C{2.8cm}|L{3.8cm}|}
\caption{\textbf{Girder Restraint and Stiffener Details}}\label{tab:girder-restraint-details} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Girder} & \textbf{Restraint} & \textbf{\makecell{Web\\Philosophy}} & \textbf{\makecell{Intermediate\\Stiffeners}} & \textbf{\makecell{Longitudinal\\Stiffeners}} & \textbf{\makecell{Bearing\\Stiffeners}} \\*[6pt]
\hline
\endfirsthead
\multicolumn{6}{c}{\small\textit{Girder Restraint and Stiffener Details (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Girder} & \textbf{Restraint} & \textbf{\makecell{Web\\Philosophy}} & \textbf{\makecell{Intermediate\\Stiffeners}} & \textbf{\makecell{Longitudinal\\Stiffeners}} & \textbf{\makecell{Bearing\\Stiffeners}} \\*[6pt]
\hline
\endhead
\hline
\multicolumn{6}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
"""
            + rst_rows
            + r"""\end{longtable}
""")


def _bracing_tables(input_dict, n_girders):
    n = n_girders if n_girders >= 2 else 2
    panels = [
        (
            _render_value(input_dict, f"{KEY_MP_CB_SELECT_GIRDERS}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_CB_MEMBER_ID}.G{i}G{i+1}.B{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_SELECT_GIRDERS}.G{i}G{i+1}.E{i}M1"),
            _render_value(input_dict, f"{KEY_MP_ED_MEMBER_ID}.G{i}G{i+1}.E{i}M1"),
            i
        )
        for i in range(1, n)
    ]

    # Helper: one cross-bracing row (all locations share same bracing config)
    def _cb_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_TYPE}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.B{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_CB_SPACING}.G{i}G{i+1}.B{i}M1", ' m'))
                + r""" \\[6pt]
\hline
""")

    # Helper: one end-diaphragm row (all locations share same config)
    def _ed_row(location, member_ids, i):
        return (location + r""" & """ + member_ids + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_TYPE}.G{i}G{i+1}.E{i}M1"))
                + r""" & """
                + (_render_value(input_dict, f"{KEY_MP_ED_BRACING_SECTION_DESIGNATION}.G{i}G{i+1}.E{i}M1"))
                + r""" \\[6pt]
\hline
""")

    cb_rows = "".join([_cb_row(cb_loc, cb_ids, i) for cb_loc, cb_ids, _, _, i in panels])
    ed_rows = "".join([_ed_row(ed_loc, ed_ids, i) for _, _, ed_loc, ed_ids, i in panels])

    return (r"""
\newpage

\vspace{0.4em}
\setlength{\tabcolsep}{4pt}
\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|L{2.5cm}|L{2.5cm}|L{3.5cm}|L{3.5cm}|C{2.5cm}|}
\caption{\textbf{Member Properties: Cross Bracing Details}}\label{tab:cb-details} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} \\[6pt]
\hline
\endfirsthead
\multicolumn{5}{c}{\small\textit{Member Properties: Cross Bracing Details (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} & \textbf{Spacing (m)} \\[6pt]
\hline
\endhead
\hline
\multicolumn{5}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
"""
+ cb_rows
+ r"""\end{longtable}

\vspace{0.4em}
\noindent
\setlength{\tabcolsep}{4pt}
\setlength\LTleft{0pt}
\setlength\LTright{\fill}

\begin{longtable}{|L{2.8cm}|L{2.8cm}|L{4.4cm}|L{4.4cm}|}
\caption{\textbf{Member Properties: End Diaphragm Details}}\label{tab:ed-details} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} \\[6pt]
\hline
\endfirsthead
\multicolumn{4}{c}{\small\textit{Member Properties: End Diaphragm Details (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Location} & \textbf{Member IDs} & \textbf{Type of Bracing} & \textbf{Bracing Section} \\[6pt]
\hline
\endhead
\hline
\multicolumn{4}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
"""
+ ed_rows
+ r"""\end{longtable}
""")


def _shear_connector_table(input_dict, output_dict=None):
    # Stud computed properties live in output_dict (populated by store_design_results)
    od = output_dict or {}
    return r"""
\label{subsec:shear-connectors}

\vspace{2.2em}

\vspace{0.4em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Shear Connector Details}}\label{tab:shear-connector-details} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Shear Connector Details (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{Stud Diameter (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_DIAMETER, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Stud Height (mm)} & """ + (_render_value(od, KEY_SD_SHEAR_HEIGHT, ' mm')) + r""" \\[6pt]
\hline
\textnormal{Stud $f_y$ (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_YIELD_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textnormal{Stud $f_u$ (MPa)} & """ + (_render_value(od, KEY_SD_SHEAR_ULTIMATE_STRENGTH, ' MPa')) + r""" \\[6pt]
\hline
\textnormal{No. of Studs per Section} & """ + (_render_value(od, KEY_SD_SHEAR_STUDS_PER_SECTION)) + r""" \\[6pt]
\hline
\end{longtable}
"""

def _safety_factors_table(input_dict):
    return r"""
\clearpage
\label{subsec:safety-factors}

\vspace{0.4em}
\noindent\textit{Note: All values are per IRC 22 Table 1 unless user-modified.}

\vspace{0.4em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Partial Safety Factors}}\label{tab:partial-safety-factors} \\
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*[6pt]
\hline
\endfirsthead
\multicolumn{2}{c}{\small\textit{Partial Safety Factors (continued from previous page)}} \\[4pt]
\hline
\rowcolor{OsdagHeaderBg}
\textbf{Parameter} & \textbf{Value} \\*[6pt]
\hline
\endhead
\hline
\multicolumn{2}{r}{\small\textit{Continued on next page}} \\
\endfoot
\hline
\endlastfoot
\textnormal{$\gamma_{\mathrm{m0}}$ (Yielding / Buckling)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M0)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{\mathrm{m1}}$ (Ultimate Stress)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_M1)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{\mathrm{c}}$ (Concrete, Basic)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_C_BASIC)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{\mathrm{s}}$ (Reinforcement)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_S)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{\mathrm{v}}$ (Shear Connectors)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_V)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{\mathrm{fft}}$ (Fatigue Load)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_FLT)) + r""" \\[6pt]
\hline
\textnormal{$\gamma_{\mathrm{Mft}}$ (Fatigue Strength)} & """ + (_render_value(input_dict, KEY_DO_GAMMA_MF)) + r""" \\[6pt]
\hline
\end{longtable}
"""

