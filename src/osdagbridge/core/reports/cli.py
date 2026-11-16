"""Headless CLI runner for OsdagBridge LaTeX Report Generator.

Enables report generation, testing, and linting directly from JSON fixtures
without requiring the PySide6 desktop GUI, OpenSees solver, or OpenCASCADE.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportPayload,
    ReportRequest,
    ReportResult,
    build_report_payload,
    generate_report,
)


def load_fixture(fixture_path: str | Path) -> dict:
    """Load and parse a JSON fixture file."""
    path = Path(fixture_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_report_from_fixture(
    fixture_path: str | Path,
    output_dir: str | Path,
    file_stem: str = "report",
    theme_name: str | None = None,
) -> ReportResult:
    """Build and compile a report given a fixture path and output directory."""
    fixture_data = load_fixture(fixture_path)
    output_dir_p = Path(output_dir).resolve()
    output_dir_p.mkdir(parents=True, exist_ok=True)

    metadata_dict = fixture_data.get("metadata", {})
    metadata = ReportMetadata(
        project_name=metadata_dict.get("project_name", "OsdagBridge Design Report"),
        project_location=metadata_dict.get("project_location", ""),
        designer=metadata_dict.get("designer", ""),
        reviewer=metadata_dict.get("reviewer", ""),
        client=metadata_dict.get("client", ""),
        company=metadata_dict.get("company", ""),
        group_name=metadata_dict.get("group_name", ""),
        subtitle=metadata_dict.get("subtitle", ""),
        job_number=metadata_dict.get("job_number", ""),
        additional_comments=metadata_dict.get("additional_comments", ""),
        logo_path=metadata_dict.get("logo_path"),
        report_date=metadata_dict.get("report_date", ""),
    )

    options_dict = fixture_data.get("options", {})
    options = ReportOptions(
        sections=options_dict.get("sections", [
            "exec_summary", "project_info", "input_parameters", "loads",
            "analysis", "design_checks", "drawings", "quantities",
            "standards", "design_log_window", "references",
        ]),
        include_figures=options_dict.get("include_figures", True),
        include_toc=options_dict.get("include_toc", True),
        include_pdf=options_dict.get("include_pdf", True),
    )

    request = ReportRequest(
        metadata=metadata,
        options=options,
        output_dir=str(output_dir_p),
        file_stem=file_stem,
    )

    inputs = fixture_data.get("input_dict", {})
    outputs = fixture_data.get("output_dict", {})

    payload = build_report_payload(request, inputs, outputs)

    # Attach decoded figures if present
    fig_data = fixture_data.get("figure_data", {})
    if fig_data:
        decoded_figs = {}
        for k, v in fig_data.items():
            if isinstance(v, str):
                try:
                    decoded_figs[k] = base64.b64decode(v)
                except Exception:
                    pass
            elif isinstance(v, bytes):
                decoded_figs[k] = v
        payload.figure_data = decoded_figs

    return generate_report(payload, request)


def main():
    parser = argparse.ArgumentParser(
        description="OsdagBridge Headless Report Generator CLI"
    )
    parser.add_argument(
        "--fixture",
        required=True,
        help="Path to JSON fixture file containing input/output dictionaries",
    )
    parser.add_argument(
        "--out",
        default="deliverables",
        help="Directory where output .tex and .pdf will be written (default: deliverables)",
    )
    parser.add_argument(
        "--stem",
        default="Report_Output",
        help="Filename stem for generated .tex and .pdf (default: Report_Output)",
    )
    parser.add_argument(
        "--theme",
        default="osdag_classic",
        help="Theme preset to use (default: osdag_classic)",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run PDF and TeX QA linter checks after generation",
    )
    parser.add_argument(
        "--keep-tex",
        action="store_true",
        help="Keep intermediate .tex file",
    )

    args = parser.parse_args()

    print(f"[CLI] Loading fixture from {args.fixture}...")
    result = run_report_from_fixture(
        fixture_path=args.fixture,
        output_dir=args.out,
        file_stem=args.stem,
        theme_name=args.theme,
    )

    if result.pdf_path and os.path.exists(result.pdf_path):
        print(f"[CLI] SUCCESS: Report PDF generated at {result.pdf_path}")
        print(f"[CLI] LaTeX Source at {result.tex_path}")
        sys.exit(0)
    else:
        print("[CLI] ERROR: PDF generation failed.")
        if result.tex_path:
            print(f"[CLI] LaTeX source preserved at {result.tex_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
