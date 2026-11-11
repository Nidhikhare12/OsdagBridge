"""Generate a synthetic report for layout verification, not engineering acceptance."""
from pathlib import Path
import sys
import os
import runpy
import json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
fixtures = runpy.run_path(str(ROOT / "tests/integration/conftest.py"))
from osdagbridge.core.reports.report_generator import ReportMetadata, ReportOptions, ReportRequest, build_report_payload, generate_report
inputs = fixtures["default_bridge_inputs"].__wrapped__()
outputs = fixtures["default_bridge_outputs"].__wrapped__(inputs)
request = ReportRequest(
    metadata=ReportMetadata(project_name="OsdagBridge report verification - synthetic fixture",
                            project_location="Test fixture", designer="Report regression", client="Test", company="OsdagBridge",
                            subtitle="Layout and data-mapping test; not a completed engineering design"),
    options=ReportOptions(sections=["loads", "analysis", "design_checks", "drawings"],
                          include_figures=True, include_toc=True, include_pdf=True),
    output_dir=str(ROOT / "docs/reports"), file_stem="Report_After")
case_path = ROOT / "docs/reports/verification_case.json"
case_path.write_text(json.dumps({"kind":"synthetic report fixture; not a solved design", "inputs":inputs, "outputs":outputs}, indent=2, default=str), encoding="utf-8")
result = generate_report(build_report_payload(request, inputs, outputs), request)
print(result)
if not result.pdf_path:
    raise SystemExit("Report compilation failed; inspect Report_After.log")
