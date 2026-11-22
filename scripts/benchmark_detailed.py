"""Detailed per-stage timing of the OsdagBridge report pipeline.

Monkey-patches the real functions/subprocess call used by generate_report so
the stage timings come from an unmodified production run.
"""

from __future__ import annotations

import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gui_smoke_test import install_opensees_stub  # noqa: E402
install_opensees_stub()

from osdagbridge.core.reports import styles, charts  # noqa: E402
from osdagbridge.core.reports.report_generator import (  # noqa: E402
    ReportMetadata, ReportOptions, ReportRequest,
    build_report_payload, generate_report,
)
from benchmark_report import INPUTS, OUTPUTS  # noqa: E402

TIMES: dict[str, list[float]] = {}


def timed(name, fn):
    def wrapper(*a, **k):
        t = time.perf_counter()
        try:
            return fn(*a, **k)
        finally:
            TIMES.setdefault(name, []).append(time.perf_counter() - t)
    return wrapper


styles.apply_global_styles = timed("style_postprocess", styles.apply_global_styles)
charts.utilization_ratio_figure = timed("ur_chart", charts.utilization_ratio_figure)
charts.material_quantity_figure = timed("material_chart", charts.material_quantity_figure)

_real_run = subprocess.run


def _timed_run(*a, **k):
    cmd = a[0] if a else k.get("args", [])
    if isinstance(cmd, list) and any("pdflatex" in str(x) for x in cmd):
        return timed("pdflatex_draft" if "-draftmode" in cmd else "pdflatex_final",
                     _real_run)(*a, **k)
    return _real_run(*a, **k)


subprocess.run = _timed_run


def main() -> int:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    out = "/tmp/opencode/detailed_bench"
    os.makedirs(out, exist_ok=True)
    meta = ReportMetadata(project_name="Perf", project_location="Mumbai",
                          designer="X", client="FOSSEE", company="IIT Bombay",
                          job_number="PERF", subtitle="Rev 0",
                          report_date="2026-11-22")
    opts = ReportOptions(sections=["loads", "analysis", "design_checks", "drawings"],
                         include_figures=True, include_toc=True, include_pdf=True)
    req = ReportRequest(metadata=meta, options=opts,
                        output_dir=out, file_stem="perf")

    total = []
    for _ in range(runs):
        t0 = time.perf_counter()
        payload = build_report_payload(req, dict(INPUTS), dict(OUTPUTS))
        t1 = time.perf_counter()
        TIMES.setdefault("payload", []).append(t1 - t0)
        generate_report(payload, req)
        total.append(time.perf_counter() - t0)

    print(f"runs={runs}")
    for name in ("payload", "ur_chart", "material_chart", "style_postprocess",
                 "pdflatex_draft", "pdflatex_final"):
        vals = TIMES.get(name, [])
        if vals:
            print(f"{name:20s} mean={statistics.mean(vals):.3f}s "
                  f"min={min(vals):.3f}s max={max(vals):.3f}s n={len(vals)}")
    print(f"{'TOTAL pipeline':20s} mean={statistics.mean(total):.3f}s "
          f"min={min(total):.3f}s max={max(total):.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
