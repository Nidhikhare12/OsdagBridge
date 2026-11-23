"""Generate a self-contained sample OsdagBridge design report.

The script builds a representative ReportPayload (no GUI or OpenSees run is
required) and compiles it through the real report generator.  It is used to
produce the `Report_Before.pdf` / `Report_After.pdf` comparison deliverables.

Usage
-----
    PYTHONPATH=src python scripts/generate_sample_reports.py <output_dir> <file_stem>
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# The report module imports results_data, which imports openseespy at module
# level.  Report generation itself never calls OpenSees, so a tiny stub is
# sufficient and keeps this demo independent of the solver installation.
_stub_pkg = types.ModuleType("openseespy")
_stub_ops = types.ModuleType("openseespy.opensees")
_stub_pkg.opensees = _stub_ops
sys.modules.setdefault("openseespy", _stub_pkg)
sys.modules.setdefault("openseespy.opensees", _stub_ops)

from osdagbridge.core.reports.report_generator import (  # noqa: E402
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    build_report_payload,
    generate_report,
)
from osdagbridge.core.utils.common import (  # noqa: E402
    KEY_DESIGN_MODE,
    KEY_LL_CURVE_RADIUS,
    KEY_LL_DESIGN_SPEED,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_SPAN,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_TERRAIN_TYPE,
)


def sample_inputs() -> dict:
    return {
        KEY_SPAN: 30.0,
        KEY_TS_NO_OF_GIRDERS: 4,
        KEY_DESIGN_MODE: "Optimized",
        KEY_WC_LD_LANE_TABLE_COUNT: 2,
        KEY_MATERIAL_GIRDER_DENSITY: 78.5,
        KEY_MATERIAL_DECK_DENSITY: 25.0,
        KEY_LL_IRC_CLASS_A: True,
        KEY_LL_IRC_70R_WHEELED: True,
        KEY_LL_CURVE_RADIUS: 300.0,
        KEY_LL_DESIGN_SPEED: 80.0,
        KEY_LL_FOOTPATH_PRESSURE_MODE: "Automatic",
        KEY_LL_FOOTPATH_PRESSURE_VALUE: "5.0",
        KEY_WL_BASIC_WIND_SPEED: 40,
        KEY_WL_TERRAIN_TYPE: "Plain Terrain",
        KEY_WL_AVG_EXPOSED_HEIGHT: 8.0,
        KEY_TS_OVERALL_WIDTH: 12.0,
        KEY_TS_DECK_THICKNESS: 0.25,
        "wind_speed": 40,
        "seismic_zone": "III",
        "shade_temp_max": 45,
        "shade_temp_min": 10,
        "project.location": "Mumbai, Maharashtra",
        "member_properties.girder_details.section_properties.area": 0.09,
        "member_properties.girder_details.section_properties.mass": 706.5,
    }


def sample_outputs() -> dict:
    return {
        "analysis_summary": {
            "max_bm": "25000 kNm",
            "max_sf": "1200 kN",
            "max_deflection": "18 mm",
        },
        "design_checks": [],
        "design_log": [
            "Project inputs validated",
            "Geometry created successfully",
            "Analysis completed successfully",
            "Design completed successfully",
        ],
        "design_results": {
            "per_girder": {
                girder: {
                    "checks": [
                        {
                            "check_id": 1,
                            "dcr": dcr,
                            "demand": 20500.0 * dcr / 0.82,
                            "capacity": 25000.0,
                            "demand_unit": "kNm",
                            "capacity_unit": "kNm",
                        },
                        {
                            "check_id": 2,
                            "dcr": 0.64,
                            "demand": 780.0,
                            "capacity": 1200.0,
                            "demand_unit": "kN",
                            "capacity_unit": "kN",
                        },
                    ]
                }
                for girder, dcr in (("G1", 0.72), ("G2", 0.76),
                                    ("G3", 0.79), ("G4", 0.82))
            }
        },
        "deck_design_results": {},
        "cross_bracing_design_results": {
            "CB-1": {
                "diagonal": {"compression": {"capacity_kN": 900.0, "efficiency": 0.71}}
            }
        },
    }


def request_for(output_dir: str, file_stem: str) -> ReportRequest:
    meta = ReportMetadata(
        project_name="Sample Steel Girder Bridge",
        project_location="Mumbai, Maharashtra",
        designer="OsdagBridge Team",
        client="FOSSEE",
        company="IIT Bombay",
        job_number="OB-2026-001",
        subtitle="Rev 0",
        report_date="2026-11-21",
    )
    opts = ReportOptions(
        sections=["loads", "analysis", "design_checks", "drawings"],
        include_figures=True,
        include_toc=True,
        include_pdf=True,
    )
    return ReportRequest(metadata=meta, options=opts,
                         output_dir=output_dir, file_stem=file_stem)


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "deliverables")
    stem = sys.argv[2] if len(sys.argv) > 2 else "Report"
    os.makedirs(out, exist_ok=True)
    req = request_for(out, stem)
    payload = build_report_payload(req, sample_inputs(), sample_outputs())
    result = generate_report(payload, req)
    print(result)
    if not result.pdf_path or not os.path.exists(result.pdf_path):
        raise SystemExit("PDF generation failed")


if __name__ == "__main__":
    main()
