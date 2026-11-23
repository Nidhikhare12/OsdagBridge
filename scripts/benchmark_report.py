"""Benchmark report generation (works on both baseline and enhanced trees).

    PYTHONPATH=src python scripts/benchmark_report.py <output_dir> [runs]
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from osdagbridge.core.reports.report_generator import (  # noqa: E402
    ReportMetadata, ReportOptions, ReportRequest,
    build_report_payload, generate_report,
)

INPUTS = {
    "geometry.span": 30.0,
    "typical_section.no_of_girders": 4,
    "geometry.design_mode": "Optimized",
    "typical_section.lane_details.lane_table_count": 2,
    "material.girder.density": 78.5,
    "material.deck.density": 25.0,
    "loading.live_load.irc.class_a": True,
    "loading.live_load.irc.70r_wheeled": True,
    "loading.live_load.footpath_pressure.mode": "Automatic",
    "loading.live_load.footpath_pressure.value": "5.0",
    "loading.wind_load.basic_wind_speed": 40,
    "loading.wind_load.terrain_type": "Plain Terrain",
    "loading.wind_load.avg_exposed_height": 8.0,
    "typical_section.overall_bridge_width": 12.0,
    "typical_section.deck_thickness": 250,
    "wind_speed": 40,
    "seismic_zone": "III",
    "shade_temp_max": 45,
    "shade_temp_min": 10,
    "member_properties.girder_details.section_properties.area": 0.09,
    "member_properties.girder_details.section_properties.mass": 706.5,
}

OUTPUTS = {
    "analysis_summary": {"max_bm": "25000 kNm"},
    "design_checks": [],
    "design_log": ["Design completed successfully"],
    "design_results": {
        "per_girder": {
            f"G{i}": {"checks": [
                {"check_id": 1, "dcr": 0.7 + i * 0.03,
                 "demand": 20000.0, "capacity": 25000.0,
                 "demand_unit": "kNm", "capacity_unit": "kNm"},
            ]}
            for i in range(1, 5)
        }
    },
    "deck_design_results": {},
}


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/opencode/bench"
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    os.makedirs(out, exist_ok=True)
    meta = ReportMetadata(
        project_name="Benchmark Bridge", project_location="Mumbai",
        designer="X", client="FOSSEE", company="IIT Bombay",
        job_number="BENCH", subtitle="Rev 0", report_date="2026-11-22")
    opts = ReportOptions(
        sections=["loads", "analysis", "design_checks", "drawings"],
        include_figures=True, include_toc=True, include_pdf=True)
    req = ReportRequest(metadata=meta, options=opts,
                        output_dir=out, file_stem="bench")
    times = []
    for i in range(runs):
        t0 = time.perf_counter()
        payload = build_report_payload(req, dict(INPUTS), dict(OUTPUTS))
        t1 = time.perf_counter()
        result = generate_report(payload, req)
        t2 = time.perf_counter()
        times.append((t1 - t0, t2 - t1))
        print(f"run {i + 1}: payload={t1 - t0:.3f}s "
              f"generate={t2 - t1:.3f}s pdf={bool(result.pdf_path)}")

    tex = Path(out) / "bench.tex"
    pdf = Path(out) / "bench.pdf"
    endheads = tex.read_text().count(r"\endhead") if tex.exists() else -1
    pages = -1
    if pdf.exists():
        try:
            for line in subprocess.run(
                    ["pdfinfo", str(pdf)], capture_output=True,
                    text=True, check=True).stdout.splitlines():
                if line.startswith("Pages:"):
                    pages = int(line.split()[1])
        except Exception:
            pass
    print(f"SUMMARY endhead={endheads} pages={pages} "
          f"pdf_bytes={pdf.stat().st_size if pdf.exists() else 0} "
          f"avg_payload={sum(x[0] for x in times) / runs:.3f}s "
          f"avg_generate={sum(x[1] for x in times) / runs:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
