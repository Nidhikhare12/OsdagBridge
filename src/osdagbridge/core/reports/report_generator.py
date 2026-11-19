
# GAPS REPORT — keys used in templates with no canonical KEY_ in common.py

#   FLOW OF REPORT GENERATION

import os, shutil, logging, datetime, tempfile, subprocess
from dataclasses import dataclass, field
from typing import Optional, List, Literal

from osdagbridge.core.utils.common import (
    KEY_DESIGN_MODE,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE
)

from osdagbridge.core.reports.report_utils import _tex
from osdagbridge.core.reports import styles
from .executive_summary import executive_summary
from .chap1 import ch1_project_info
from .chap2 import ch2_input_parameters
from .chap3 import ch3_loads
from .chap4 import ch4_analysis
from .chap5 import ch5_design_checks
from .chap6 import ch6_drawings
from .chap7 import ch7_quantities
from .chap8 import ch8_design_log
from .chap9 import references

logger = logging.getLogger(__name__)

def preamble(project_name, job_number, report_date, report_version='Rev 0'):
    """LaTeX preamble — delegated to the centralized styles module."""
    return styles.preamble(project_name, job_number, report_date,
                           report_version or 'Rev 0')

def title_page(m, osdag_logo, org_logo):
    """Title page — delegated to the centralized styles module."""
    return styles.title_page(m, osdag_logo, org_logo)

def toc_section():
    """TOC styling — delegated to the centralized styles module."""
    return styles.toc_section()

@dataclass
class ReportMetadata:
    project_name: str
    project_location: str
    designer: str
    client: str
    company: str
    group_name: str = ''
    subtitle: str = ''
    job_number: str = ''
    additional_comments: str = ''
    logo_path: Optional[str] = None
    report_date: str = ''
    reviewer: str = ''

@dataclass
class ReportOptions:
    sections: List[str]
    include_figures: bool
    include_toc: bool
    include_pdf: bool

@dataclass
class ReportRequest:
    metadata: ReportMetadata
    options: ReportOptions
    output_dir: str
    file_stem: str

@dataclass
class ReportFigures:
    plan:            Optional[str] = None
    cross_section:   Optional[str] = None
    final_geometry:  Optional[str] = None
    longitudinal_elevation: Optional[str] = None
    girder_3d:       Optional[str] = None
    girder_front:    Optional[str] = None
    girder_top:      Optional[str] = None
    girder_end:      Optional[str] = None
    bm_envelope:     Optional[str] = None
    sf_envelope:     Optional[str] = None
    defl_ll:         Optional[str] = None
    shear_connector: Optional[str] = None
    cross_bracing:   Optional[str] = None

@dataclass
class ReportPayload:
    metadata:         ReportMetadata
    options:          ReportOptions
    inputs:           dict
    analysis_summary: dict
    design_checks:    list
    figures:          ReportFigures
    log_entries:      List[str] = field(default_factory=list)
    output_dict:      dict = field(default_factory=dict)
    figure_data:      dict = field(default_factory=dict)  # {attr: bytes} — cleared after writing to tmpdir

@dataclass
class ReportResult:
    pdf_path: Optional[str]
    tex_path: Optional[str]

class ReportDataBridge:
    """Centralized data extraction for the OsdagBridge report."""

    def __init__(self, output_dict: dict, input_dict: dict, payload: "ReportPayload"):
        self.output_dict = output_dict
        self.input_dict = input_dict
        self.payload = payload

    def _cb_forces_dict(self) -> dict:
        """Internal: return crossbracing_forces_dict from output_dict."""
        return self.output_dict.get("crossbracing_forces_dict", {})

    def _cb_pair_designs(self) -> dict:
        """Internal: return crossbracing_design_results from output_dict."""
        return self.output_dict.get("crossbracing_design_results", {})

    def _cb_osdag(self, pair: str, member: str, force_type: str) -> dict:
        """
        Extract the _extract_osdag_summary dict for one member.
        pair      e.g. "G1-G2"
        member    "diagonal" or "chord"
        force_type "tension" or "compression"
        """
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
        try:
            raw = self._cb_pair_designs()[pair][member][force_type]
            return _extract_osdag_summary(raw or {})
        except (KeyError, TypeError):
            return {}

    def get_cb_pairs(self) -> list:
        """Return sorted list of girder pair keys e.g. ['G1-G2', 'G2-G3']."""
        try:
            return sorted(self._cb_forces_dict().get("pairs", {}).keys())
        except Exception:
            return []

    def get_cb_geometry(self) -> dict:
        """Return the geometry sub-dict from forces_dict."""
        return self._cb_forces_dict().get("geometry", {})

    def get_cb_brace_type(self) -> str:
        try:
            return self._cb_forces_dict().get("brace_type", "X")
        except Exception:
            return "X"

    def get_cb_force(self, pair: str, member: str, force_type: str) -> str:
        """
        Return demand force string for table 5.20(a).
        member: "diagonal" or "chord"
        force_type: "tension" or "compression"
        """
        try:
            pairs = self._cb_forces_dict()["pairs"][pair]
            key = f"diag_{force_type}_kN" if member == "diagonal" else f"chord_{force_type}_kN"
            val = pairs.get(key)
            if val is not None:
                return f"{val:.3f}"
        except (KeyError, TypeError):
            pass
        return ""

    def get_cb_nature(self, pair: str, member: str) -> str:
        """Return 'T', 'C', or 'T/C' depending on what forces exist for this member."""
        try:
            pairs = self._cb_forces_dict()["pairs"][pair]
            t_key = "diag_tension_kN"     if member == "diagonal" else "chord_tension_kN"
            c_key = "diag_compression_kN" if member == "diagonal" else "chord_compression_kN"
            has_t = pairs.get(t_key) is not None
            has_c = pairs.get(c_key) is not None
            if has_t and has_c:
                return "T / C"
            if has_t:
                return "T"
            if has_c:
                return "C"
        except (KeyError, TypeError):
            pass
        return ""

    def get_cb_governing_force(self, pair: str, member: str) -> tuple:
        """
        Return (force_kN_str, force_type) for the governing (max absolute) force.
        Used as the single demand value for capacity tables.
        """
        try:
            pairs = self._cb_forces_dict()["pairs"][pair]
            t_key = "diag_tension_kN"     if member == "diagonal" else "chord_tension_kN"
            c_key = "diag_compression_kN" if member == "diagonal" else "chord_compression_kN"
            t_val = pairs.get(t_key)
            c_val = pairs.get(c_key)
            if t_val is not None and c_val is not None:
                if abs(c_val) >= abs(t_val):
                    return (f"{c_val:.3f}", "compression")
                return (f"{t_val:.3f}", "tension")
            if c_val is not None:
                return (f"{c_val:.3f}", "compression")
            if t_val is not None:
                return (f"{t_val:.3f}", "tension")
        except (KeyError, TypeError):
            pass
        return ("", "compression")

    def get_cb_section(self, pair: str, member: str, force_type: str) -> str:
        """Section designation for a member e.g. '75 x 75 x 8'."""
        val = self._cb_osdag(pair, member, force_type).get("section")
        return _tex(val) if val else ""

    def get_cb_capacity(self, pair: str, member: str, force_type: str) -> str:
        """Capacity in kN."""
        val = self._cb_osdag(pair, member, force_type).get("capacity_kN")
        return f"{float(val):.3f}" if val is not None else ""

    def get_cb_efficiency(self, pair: str, member: str, force_type: str) -> str:
        """Utilization ratio (efficiency)."""
        val = self._cb_osdag(pair, member, force_type).get("efficiency")
        return f"{float(val):.3f}" if val is not None else ""

    def get_cb_slenderness(self, pair: str, member: str) -> str:
        """KL/r — same for tension and compression (geometry-based)."""
        for ft in ("compression", "tension"):
            val = self._cb_osdag(pair, member, ft).get("slenderness")
            if val is not None:
                return f"{float(val):.1f}"
        return ""

    def get_cb_status(self, pair: str, member: str, force_type: str) -> str:
        """PASS / FAIL based on UR <= 1.0."""
        try:
            val = self._cb_osdag(pair, member, force_type).get("efficiency")
            if val is not None:
                ur = float(val)
                if ur <= 1.0:
                    return styles.PASS_BLACK
                return styles.FAIL
        except (TypeError, ValueError):
            pass
        return ""

    def get_cb_gov_lc(self, pair: str, member: str, force_type: str) -> str:
        """Governing load case label for member (tension or compression)."""
        try:
            pfx = "diag" if member == "diagonal" else "chord"
            key = f"{pfx}_{force_type}_gov_lc"
            val = self._cb_forces_dict()["pairs"][pair].get(key)
            return _tex(val) if val else ""
        except (KeyError, TypeError):
            return ""

    def get_cb_connection(self, pair: str, member: str, force_type: str) -> str:
        """Return 'Welded' or 'Bolted'."""
        val = self._cb_osdag(pair, member, force_type).get("connection")
        return str(val) if val else ""

    def get_cb_effective_length(self, member: str) -> str:
        """Effective length KL in mm from geometry."""
        try:
            geom = self.get_cb_geometry()
            if member == "diagonal":
                L_m = geom.get("diagonal_length_m", 0)
            else:
                L_m = geom.get("horiz_proj_m", 0)
            return f"{L_m * 1000:.0f}"   # convert m → mm
        except (TypeError, ValueError):
            return ""

    def get_cb_alpha_deg(self) -> str:
        """Diagonal angle in degrees."""
        try:
            return f"{self.get_cb_geometry().get('alpha_deg', 0):.2f}"
        except Exception:
            return ""

def _format_project_location(pl_data):
    if not pl_data:
        return ''
    if isinstance(pl_data, str):
        try:
            import ast
            pl_dict = ast.literal_eval(pl_data)
        except Exception:
            return pl_data
    elif isinstance(pl_data, dict):
        pl_dict = pl_data
    else:
        return str(pl_data)
    
    method = pl_dict.get('method')
    data = pl_dict.get('data', {})
    
    if method == 'location_name':
        dist = data.get('district', '')
        state = data.get('state', '')
        if dist and state:
            return f"{dist}, {state}"
        return dist or state or r''
    elif method == 'map':
        lat = data.get('latitude', '')
        lon = data.get('longitude', '')
        if lat and lon:
            try:
                from osdagbridge.core.bridge_types.plate_girder.ui_fields_project_location import DB_PATH
                from osdagbridge.core.data.project_location.database import Database
                db = Database(DB_PATH)
                db.connect()
                nearest = db.get_nearest_station_temperature(float(lat), float(lon))
                db.close()
                if nearest:
                    return f"{nearest['station']}, {nearest['state']}"
            except Exception as e:
                logger.warning(f"Reverse geocode error: {e}")
            return f"Lat: {lat}°, Lon: {lon}°"
        return 'Map Location'
    elif method == 'custom_data':
        return 'Custom Location Data'
    
    return str(pl_data)

def build_report_payload(request, input_dict, output_dict):
    try:
        rd  = request.metadata.report_date or datetime.date.today().isoformat()
        lp  = request.metadata.logo_path
        raw_pl = request.metadata.project_location or input_dict.get('project.location') or ''
        pl = _format_project_location(raw_pl)

        md = ReportMetadata(
            project_name  = request.metadata.project_name,
            project_location = pl,
            designer      = request.metadata.designer,
            client        = request.metadata.client,
            company       = request.metadata.company,
            group_name    = request.metadata.group_name,
            subtitle      = request.metadata.subtitle,
            job_number    = request.metadata.job_number,
            additional_comments = request.metadata.additional_comments,
            logo_path     = lp,
            report_date   = rd,
            reviewer      = getattr(request.metadata, 'reviewer', ''))

        try:
            import ast
            if isinstance(raw_pl, str) and '{' in raw_pl:
                pl_dict = ast.literal_eval(raw_pl)
            elif isinstance(raw_pl, dict):
                pl_dict = raw_pl
            else:
                pl_dict = {}
                
            if pl_dict and isinstance(pl_dict, dict):
                data = pl_dict.get('data', {})
                weather = pl_dict.get('weather_data', {})
                
                lat_val = data.get('latitude') or weather.get('latitude')
                lon_val = data.get('longitude') or weather.get('longitude')
                
                if 'latitude' not in input_dict and lat_val:
                    input_dict['latitude'] = lat_val
                if 'longitude' not in input_dict and lon_val:
                    input_dict['longitude'] = lon_val
                    
                if 'seismic_zone' not in input_dict and weather.get('zone'):
                    input_dict['seismic_zone'] = weather.get('zone')
                if 'wind_speed' not in input_dict and weather.get('wind_speed'):
                    input_dict['wind_speed'] = weather.get('wind_speed')
                if 'shade_temp_max' not in input_dict and weather.get('max_temp'):
                    input_dict['shade_temp_max'] = weather.get('max_temp')
                if 'shade_temp_min' not in input_dict and weather.get('min_temp'):
                    input_dict['shade_temp_min'] = weather.get('min_temp')
        except Exception as e:
            logger.warning(f"Failed to parse project location data: {e}")

        for _tkey in (KEY_TL_BRIDGE_TEMP_MIN, KEY_TL_BRIDGE_TEMP_MAX,
                      KEY_TL_TEMP_RISE, KEY_TL_TEMP_FALL):
            if not input_dict.get(_tkey) and output_dict.get(_tkey):
                input_dict[_tkey] = output_dict[_tkey]

        if not input_dict.get(KEY_TL_BRIDGE_TEMP_MIN):
            try:
                max_str = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
                min_str = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
                if max_str and min_str:
                    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017
                    res   = IRC6_2017.cl_215_2_effective_bridge_temperature(
                                float(max_str), float(min_str), 'metallic', False)
                    t_min = res.get('T_min', 0)
                    t_max = res.get('T_max', 0)
                    mean  = (t_max + t_min) / 2.0
                    input_dict[KEY_TL_BRIDGE_TEMP_MIN] = f"{t_min:.2f}"
                    input_dict[KEY_TL_BRIDGE_TEMP_MAX] = f"{t_max:.2f}"
                    input_dict[KEY_TL_TEMP_RISE]       = f"{t_max - mean:.2f}"
                    input_dict[KEY_TL_TEMP_FALL]       = f"{mean - t_min:.2f}"
            except Exception as _te:
                logger.warning(f"Could not compute temperature values for report: {_te}")

        asum = {}
        if output_dict:
            asum = output_dict.get('analysis_summary', {})
   

        dc = []
        le = []
        if output_dict:
            if 'design_checks' in output_dict:
                dc = output_dict['design_checks']
            if 'design_log' in output_dict:
                le = output_dict['design_log']

        if not le:
            try:
                from osdagbridge.core.utils.logger import bridge_logger
                le = bridge_logger.get_success_log()
            except Exception as _le:
                logger.warning("Could not read design log from logger: %s", _le)

        return ReportPayload(metadata=md, options=request.options, inputs=input_dict,
                             analysis_summary=asum, design_checks=dc,
                             figures=ReportFigures(), log_entries=le,
                             output_dict=output_dict or {})

    except Exception as exc:
        logger.warning("build_report_payload error: %s", exc)
        return ReportPayload(
            metadata=request.metadata, options=request.options,
            inputs={}, analysis_summary={}, design_checks=[],
            figures=ReportFigures(), log_entries=[],
            output_dict={})

from osdagbridge.core.boq.boq_generator import calculate_material_quantities

_FIGURE_MAP = [
    ('plan',                  'plan.png'),
    ('cross_section',         'cross_section.png'),
    ('final_geometry',        'final_geometry.png'),
    ('longitudinal_elevation','longitudinal_elevation.png'),
    ('girder_3d',             'girder_3d.png'),
    ('girder_top',            'girder_top.png'),
    ('section_preview',       'section_preview.png'),
    ('stiffener_preview',     'stiffener_preview.png'),
    ('cb_diagram',            'cb_diagram.png'),
    ('cb_bracing',            'cb_bracing.png'),
    ('cb_top_chord',          'cb_top_chord.png'),
    ('cb_bottom_chord',       'cb_bottom_chord.png'),
    ('ed_diagram',            'ed_diagram.png'),
    ('ed_bracing',            'ed_bracing.png'),
    ('ed_top_chord',          'ed_top_chord.png'),
    ('ed_bottom_chord',       'ed_bottom_chord.png'),
    ('bm_envelope',           'bm_envelope.png'),
    ('sf_envelope',           'sf_envelope.png'),
    ('defl_ll',               'defl_ll.png'),
]

def _collect_utilization_ratios(output_dict: dict, bridge) -> dict:
    """Worst utilization ratio per primary element for the §5.5 chart."""
    urs = {}

    def max_dcr(checks):
        best = None
        for chk in checks or []:
            try:
                d = float(chk.get("dcr") or chk.get("ur") or 0.0)
            except (TypeError, ValueError):
                continue
            if best is None or d > best:
                best = d
        return best

    try:
        per_girder = (output_dict.get("design_results", {}) or {}).get("per_girder", {}) or {}
    except Exception:
        pg = {}
    g_best = None
    for girder, gd in per_girder.items():
        if str(girder).startswith("EB"):
            continue
        for lc, ld in (gd.get("per_lc") or {}).items():
            d = max_dcr(ld.get("checks"))
            if d is not None and (g_best is None or d > g_best):
                g_best = d
        d = max_dcr(gd.get("checks"))
        if d is not None and (g_best is None or d > g_best):
            g_best = d
    if g_best is not None:
        urs["Steel Plate Girders"] = g_best

    def scan_ur(obj, depth=0):
        best = None
        if depth > 6:
            return None
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = str(k).lower()
                if kl in ("ur", "dcr", "utilization", "utilization_ratio") or "dcr" in kl or kl.endswith("_ur"):
                    try:
                        f = float(v)
                        if 0 < f < 100 and (best is None or f > best):
                            best = f
                    except (TypeError, ValueError):
                        pass
                else:
                    d = scan_ur(v, depth + 1)
                    if d is not None and (best is None or d > best):
                        best = d
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                d = scan_ur(v, depth + 1)
                if d is not None and (best is None or d > best):
                    best = d
        return best

    deck = scan_ur(output_dict.get("deck_design_results", {}) or {})
    if deck is not None:
        urs["Concrete Deck Slab"] = deck

    cb_best = None
    try:
        _cb_pairs = bridge.get_cb_pairs()
    except Exception:
        _cb_pairs = []
    for pair in _cb_pairs:
        for member in ("diagonal", "chord"):
            for ftype in ("tension", "compression"):
                try:
                    eff = bridge.get_cb_efficiency(pair, member, ftype)
                    ur = float(eff)
                except Exception:
                    continue
                if cb_best is None or ur > cb_best:
                    cb_best = ur
    if cb_best is not None:
        urs["Cross Bracing"] = cb_best

    ed = scan_ur(output_dict.get("end_diaphragm_design_results", {}) or {})
    if ed is not None:
        urs["End Diaphragms"] = ed

    return urs

def generate_report(payload, request):
    """Compile the full OsdagBridge Design Report to PDF (+ .tex source)."""
    tex_path = None
    try:
        compiler = 'pdflatex'
        try:
            import importlib
            module = importlib.import_module('osdag_latex_env.__main__')
            latex_env = getattr(module, 'OsdagLatexEnv')()
            if latex_env.pdflatex:
                compiler = str(latex_env.pdflatex)
                if latex_env.bin_dir:
                    os.environ['PATH'] = str(latex_env.bin_dir) + os.pathsep + os.environ.get('PATH', '')
        except Exception as e:
            logger.info("osdag_latex_env not found or failed to load. (%s)", e)
            
        logger.info("Compiler: %s", compiler)

        os.makedirs(request.output_dir, exist_ok=True)

        pdf_path = os.path.join(request.output_dir, request.file_stem + '.pdf')
        tex_path = os.path.join(request.output_dir, request.file_stem + '.tex')

        with tempfile.TemporaryDirectory() as tmp_dir:

            tmp_images = os.path.join(tmp_dir, 'images')
            os.makedirs(tmp_images, exist_ok=True)
            fig_paths = {}
            for attr, img_bytes in list(payload.figure_data.items()):
                if img_bytes:
                    p = os.path.join(tmp_images, attr + '.png')
                    with open(p, 'wb') as fh:
                        fh.write(img_bytes)
                    fig_paths[attr] = p.replace('\\', '/')
            payload.figure_data.clear()  # bytes no longer needed — free RAM now

            tmp_assets = os.path.join(tmp_dir, 'assets')
            os.makedirs(tmp_assets, exist_ok=True)

            osdag_logo_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'ResourceFiles', 'vectors', 'Osdag Logo.png')
            iit_logo_src   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'IIT Bombay Logo.png')

            osdag_logo_latex = None
            if os.path.exists(osdag_logo_src):
                shutil.copy2(osdag_logo_src, os.path.join(tmp_assets, 'osdag_logo.png'))
                osdag_logo_latex = 'assets/osdag_logo.png'

            org_logo_latex = None
            org_logo_src = payload.metadata.logo_path if (payload.metadata.logo_path and os.path.exists(payload.metadata.logo_path)) else (iit_logo_src if os.path.exists(iit_logo_src) else None)
            if org_logo_src:
                shutil.copy2(org_logo_src, os.path.join(tmp_assets, 'org_logo.png'))
                org_logo_latex = 'assets/org_logo.png'

            quantities = calculate_material_quantities(payload.inputs, payload.output_dict)
            payload.inputs.update(quantities)

            try:
                from osdagbridge.core.reports.charts import material_quantity_figures
                for name, png in material_quantity_figures(payload.inputs).items():
                    path = os.path.join(tmp_images, name + '.png')
                    with open(path, 'wb') as fh:
                        fh.write(png)
                    fig_paths[name] = path.replace('\\', '/')
            except Exception as exc:
                logger.warning("Material charts failed: %s", exc)

            bridge = ReportDataBridge(payload.output_dict, payload.inputs, payload)

            try:
                urs = _collect_utilization_ratios(payload.output_dict, bridge)
                from osdagbridge.core.reports.charts import ur_summary_figure
                png = ur_summary_figure(urs)
                if png:
                    path = os.path.join(tmp_images, 'chart_ur_summary.png')
                    with open(path, 'wb') as fh:
                        fh.write(png)
                    fig_paths['chart_ur_summary'] = path.replace('\\', '/')
            except Exception as exc:
                logger.warning("UR chart failed: %s", exc)
            span_m = float(payload.inputs.get(KEY_SPAN, 0) or 0)

            doc_parts = []
            doc_parts.append(preamble(payload.metadata.project_name, payload.metadata.job_number, payload.metadata.report_date, payload.metadata.subtitle or 'Rev 0'))
            doc_parts.append(title_page(payload.metadata, osdag_logo_latex, org_logo_latex))

            if payload.options.include_toc:
                doc_parts.append(toc_section())

            secs = payload.options.sections

            doc_parts.append(executive_summary(payload.inputs, payload.output_dict, fig_paths))
            doc_parts.append(ch1_project_info(payload.metadata))
            doc_parts.append(ch2_input_parameters(payload.metadata, payload.inputs, payload.output_dict))

            if 'loads' in secs:
                doc_parts.append(ch3_loads(payload.inputs))
            if 'analysis' in secs:
                doc_parts.append(ch4_analysis(payload.analysis_summary, fig_paths, bridge, span_m))
            if 'design_checks' in secs:
                doc_parts.append(ch5_design_checks(payload.design_checks, bridge, fig_paths))
            if 'drawings' in secs and payload.options.include_figures:
                doc_parts.append(ch6_drawings(fig_paths))

            doc_parts.append(ch7_quantities(payload.inputs, fig_paths))

            mode = str(payload.inputs.get(KEY_DESIGN_MODE, "Optimized")).strip().lower()
            is_custom = mode in {"custom", "customized"}
        

            doc_parts.append(ch8_design_log(payload.log_entries, payload.inputs))

            doc_parts.append(references())
            doc_parts.append(r"\end{document}")

            full_tex = "\n".join(doc_parts)

            tmp_tex = os.path.join(tmp_dir, request.file_stem + '.tex')
            tmp_pdf = os.path.join(tmp_dir, request.file_stem + '.pdf')

            with open(tmp_tex, 'w', encoding='utf-8') as f:
                f.write(full_tex)

            compile_ok = True
            for run in range(2):
                try:
                    kwargs = {
                        'cwd': tmp_dir,
                        'stdout': subprocess.PIPE,
                        'stderr': subprocess.PIPE,
                        'check': False,
                        'env': os.environ.copy()
                    }
                    if os.name == 'nt':
                        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

                    res = subprocess.run(
                        [compiler, '-interaction=nonstopmode', request.file_stem + '.tex'],
                        **kwargs
                    )
                    if res.returncode != 0:
                        compile_ok = False
                        logger.warning("pdflatex run %d exited with code %d", run + 1, res.returncode)
                except Exception as exc:
                    compile_ok = False
                    logger.warning("pdflatex run %d failed: %s", run + 1, exc)

            if os.path.exists(tmp_tex):
                shutil.copy2(tmp_tex, tex_path)

            pdf_valid = False
            if os.path.exists(tmp_pdf):
                try:
                    with open(tmp_pdf, 'rb') as fh:
                        header = fh.read(8)
                        fh.seek(0, os.SEEK_END)
                        size = fh.tell()
                    pdf_valid = header.startswith(b'%PDF-') and size > 1024
                except OSError:
                    pdf_valid = False

            if pdf_valid:
                shutil.copy2(tmp_pdf, pdf_path)
            elif compile_ok:
                logger.warning("pdflatex exited cleanly but output PDF is missing or invalid")

        if os.path.exists(pdf_path):
            try:
                with open(pdf_path, 'rb') as fh:
                    valid = fh.read(5) == b'%PDF-'
            except OSError:
                valid = False
            if valid:
                logger.info("Report generated: %s", pdf_path)
                return ReportResult(pdf_path=pdf_path, tex_path=tex_path)
            logger.error("PDF at %s failed %PDF- header validation", pdf_path)
            try:
                os.remove(pdf_path)
            except OSError:
                pass

        logger.error("pdflatex ran but no valid PDF was produced.")
        if 'res' in locals():
            logger.error("pdflatex STDOUT:\n%s", res.stdout.decode('utf-8', 'ignore'))
            logger.error("pdflatex STDERR:\n%s", res.stderr.decode('utf-8', 'ignore'))
        return ReportResult(pdf_path=None, tex_path=tex_path)

    except Exception as exc:
        logger.error("generate_report failed: %s", exc, exc_info=True)
        if tex_path and os.path.exists(tex_path):
            return ReportResult(pdf_path=None, tex_path=tex_path)
        return ReportResult(pdf_path=None, tex_path=None)
