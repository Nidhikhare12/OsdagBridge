"""
E2E Test Configuration & Fixtures for OsdagBridge Report Generator
===================================================================
Authoritative Sources:
- LaTeX Report Generator Refactoring & Enhancements.docx.md
- ORIGINAL_REQUEST.md
- OsdagBridge Architecture Survey Handoffs (dev branch)
"""

import os
import sys
import shutil
import subprocess
import tempfile
import unittest.mock
import re
import pytest

# ---------------------------------------------------------------------------
# 1. Environment & Path Bootstrap
# ---------------------------------------------------------------------------
# Ensure TeX compilers (MiKTeX pdflatex, local tectonic) are accessible in PATH
MIKTEX_BIN = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "MiKTeX", "miktex", "bin", "x64")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN_DIR = os.path.join(PROJECT_ROOT, "bin")

for p in (MIKTEX_BIN, BIN_DIR):
    if os.path.exists(p) and p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")

# Ensure openseespy stub is active if openseespy binary wheel is not installed
if "openseespy" not in sys.modules:
    sys.modules["openseespy"] = unittest.mock.MagicMock()
    sys.modules["openseespy.opensees"] = unittest.mock.MagicMock()

# Ensure osdagbridge/src is on sys.path
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_FOOTPATH,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_TS_NO_OF_GIRDERS,
    KEY_DESIGN_MODE,
)
from osdagbridge.core.bridge_types.plate_girder.defaults import (
    BASIC_INPUT_DICT,
    solve_extend_basic_input_dict,
)
from osdagbridge.core.reports.report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportDataBridge,
    build_report_payload,
    generate_report,
)
from osdagbridge.core.boq.boq_generator import calculate_material_quantities


# ---------------------------------------------------------------------------
# 2. LaTeX Parser & Structural Inspector Utilities
# ---------------------------------------------------------------------------
class LaTeXInspector:
    """Helper for inspecting and asserting structural elements in LaTeX source."""

    @staticmethod
    def extract_longtables(tex: str) -> list[dict]:
        """Extract all longtable blocks along with captions and headers."""
        pattern = re.compile(
            r"\\begin\{longtable\}(?:\[.*?\])?\{(.*?)\}(.*?)\\end\{longtable\}",
            re.DOTALL,
        )
        tables = []
        for match in pattern.finditer(tex):
            col_spec = match.group(1).strip()
            body = match.group(2)
            caption_m = re.search(r"\\caption(?:\[.*?\])?\{([^\}]+)\}", body)
            caption = caption_m.group(1).strip() if caption_m else ""
            has_endfirsthead = r"\endfirsthead" in body
            has_endhead = r"\endhead" in body
            tables.append(
                {
                    "col_spec": col_spec,
                    "body": body,
                    "caption": caption,
                    "has_endfirsthead": has_endfirsthead,
                    "has_endhead": has_endhead,
                }
            )
        return tables

    @staticmethod
    def extract_figures(tex: str) -> list[dict]:
        """Extract all figure environments and their graphic paths/captions."""
        pattern = re.compile(
            r"\\begin\{figure\}(?:\[.*?\])?(.*?)\\end\{figure\}",
            re.DOTALL,
        )
        figures = []
        for match in pattern.finditer(tex):
            body = match.group(1)
            caption_m = re.search(r"\\caption(?:\[.*?\])?\{([^\}]+)\}", body)
            caption = caption_m.group(1).strip() if caption_m else ""
            graphics = re.findall(r"\\includegraphics(?:\[.*?\])?\{([^\}]+)\}", body)
            figures.append(
                {
                    "body": body,
                    "caption": caption,
                    "graphics": graphics,
                }
            )
        return figures

    @staticmethod
    def extract_geometry(tex: str) -> dict:
        """Extract geometry parameters from \\usepackage[...]{geometry}."""
        m = re.search(r"\\usepackage\[(.*?)\]\{geometry\}", tex)
        if not m:
            return {}
        params_str = m.group(1)
        params = {}
        for item in params_str.split(","):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                params[k.strip()] = v.strip()
            else:
                params[item] = True
        return params

    @staticmethod
    def has_negative_footer_spacing(tex: str) -> bool:
        """Check whether negative vspace hacks are present in footrule."""
        footrule_blocks = re.findall(
            r"\\renewcommand\{\\footrule\}\{(.*?)\}(?:\n|\r\n)\}", tex, re.DOTALL
        )
        for block in footrule_blocks:
            if re.search(r"\\vspace\{-\d+pt\}", block):
                return True
        # Also check direct occurrence in fancypagestyle
        return bool(re.search(r"\\footrule.*?\\vspace\{-\d+pt\}", tex, re.DOTALL))


# ---------------------------------------------------------------------------
# 3. Pytest Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def latex_inspector():
    return LaTeXInspector()


@pytest.fixture
def default_bridge_inputs():
    """Generates synthetic bridge inputs for report-only tests; no solver is run."""
    inputs = dict(BASIC_INPUT_DICT)
    inputs.update(
        {
            KEY_SPAN: 30.0,
            KEY_CARRIAGEWAY_WIDTH: 7.5,
            KEY_FOOTPATH: "Both",
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_70R_WHEELED: True,
            KEY_LL_IRC_70R_TRACKED: False,
            KEY_LL_FOOTPATH_PRESSURE_VALUE: 4.0,  # kN/m^2
            KEY_DESIGN_MODE: "Optimized",
        }
    )
    solve_extend_basic_input_dict(inputs)
    # Defaults expansion sets vehicle defaults; selection belongs to the saved case.
    from osdagbridge.core.utils import common as K
    for name in ("CLASS_A", "70R_WHEELED", "70R_TRACKED", "AA_WHEELED", "AA_TRACKED", "CLASS_SV", "70R_BOGIE", "CLASS_FATIGUE"):
        inputs[getattr(K, "KEY_LL_IRC_" + name)] = name in {"CLASS_A", "70R_WHEELED"}
    return inputs


@pytest.fixture
def default_bridge_outputs(default_bridge_inputs):
    """Provides representative design results, DCRs, and material take-offs."""
    # Synthetic results for report tests only; not an engineering validation case.
    from osdagbridge.core.utils import common as K
    return {
        "design_results": {"per_girder": {
            f"G{i}": {"checks": [{"check_id": 1, "name": "Moment", "demand": 120 + i,
                                   "capacity": 100, "dcr": (120 + i) / 100,
                                   "demand_unit": "kN-m", "capacity_unit": "kN-m"}]}
            for i in range(1, 6)}},
        "deck_report_values": {K.KEY_DD_M_ULS_SAG: 65, K.KEY_DD_MU_BOT: 85},
        "crossbracing_design_results": {},
    }


@pytest.fixture
def default_report_metadata():
    """Generates standard project metadata for reports."""
    return ReportMetadata(
        project_name="OsdagBridge Plate Girder Design Verification",
        project_location="Mumbai, Maharashtra",
        designer="Senior Bridge Engineer",
        client="Ministry of Road Transport and Highways",
        company="FOSSEE, IIT Bombay",
        subtitle="End-to-End Test Run",
    )


@pytest.fixture
def default_report_options():
    """Standard report options including all chapters."""
    return ReportOptions(
        sections=["loads", "analysis", "design_checks", "drawings"],
        include_figures=True,
        include_toc=True,
        include_pdf=True,
    )


@pytest.fixture
def report_request_factory(tmp_path, default_report_metadata, default_report_options):
    """Factory fixture creating ReportRequest pointing to an isolated temp directory."""
    def _create_request(file_stem="Test_Report"):
        return ReportRequest(
            metadata=default_report_metadata,
            options=default_report_options,
            output_dir=str(tmp_path),
            file_stem=file_stem,
        )
    return _create_request


@pytest.fixture
def compile_latex_file():
    """Helper fixture to compile a .tex file to PDF using the available compiler."""
    def _compile(tex_path: str, output_dir: str) -> tuple[int, str, str]:
        # Choose compiler: pdflatex (MiKTeX) or tectonic
        pdflatex_bin = shutil.which("pdflatex")
        tectonic_bin = shutil.which("tectonic")

        if pdflatex_bin:
            cmd = [pdflatex_bin, "-interaction=nonstopmode", os.path.basename(tex_path)]
            cwd = os.path.dirname(tex_path)
            # Run twice for cross-references
            subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            pdf_out = os.path.splitext(tex_path)[0] + ".pdf"
            return res.returncode, res.stdout, res.stderr
        elif tectonic_bin:
            cmd = [tectonic_bin, "-Z", f"search-path={PROJECT_ROOT}", tex_path, "-o", output_dir]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return res.returncode, res.stdout, res.stderr
        else:
            pytest.skip("PDF integration requires pdflatex or tectonic on PATH")

    return _compile
