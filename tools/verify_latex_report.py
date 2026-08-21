"""Generate a deterministic PDF from a saved OSI file for report verification."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("osi", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path.cwd())
    parser.add_argument("--stem", default="Report_After")
    args = parser.parse_args()

    with args.osi.open("r", encoding="utf-8") as stream:
        inputs = yaml.safe_load(stream)
    if not isinstance(inputs, dict):
        raise ValueError("OSI file must contain a mapping")

    backend = PlateGirderBridge()
    try:
        backend.set_input(inputs)
        backend.design()
        request = ReportRequest(
            metadata=ReportMetadata(
                project_name="OsdagBridge LaTeX Report Verification",
                project_location="Mumbai (Colaba), Maharashtra",
                designer="Niraj Khumkar",
                reviewer="FOSSEE Osdag Team",
                client="FOSSEE",
                company="FOSSEE Osdag",
                job_number="2026-LATEX",
                subtitle="Rev 0.2",
                report_date="12 August 2026",
                additional_comments="Generated from Report_Before_Input.osi for regression verification.",
            ),
            options=ReportOptions(
                sections=["loads", "analysis", "design_checks", "drawings"],
                include_figures=True,
                include_toc=True,
                include_pdf=True,
            ),
            output_dir=str(args.output_dir.resolve()),
            file_stem=args.stem,
        )
        result = backend.generate_design_report(request, {})
        if not result.pdf_path or not Path(result.pdf_path).is_file():
            raise RuntimeError(f"PDF was not generated; TeX path: {result.tex_path}")
        print(f"PDF={result.pdf_path}")
        print(f"TEX={result.tex_path}")
        return 0
    finally:
        try:
            backend.release()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
