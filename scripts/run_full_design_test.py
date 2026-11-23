"""Run a real OpenSees analysis + design and generate its design report.

This closes the last GUI/solver gap: no OpenSees or OCC stubs are used for the
analysis itself (OCC is only stubbed because the 3-D viewer is not needed to
produce a report).

    PYTHONPATH=src python scripts/run_full_design_test.py
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# OCC is only needed by the 3-D viewer, not by analysis/report generation.
from gui_smoke_test import (  # noqa: E402
    install_occ_stub, install_navcube_stub, install_module_stub,
)
install_occ_stub()
install_navcube_stub()
install_module_stub("fiona")


def install_osdag_core_stub() -> None:
    """Inert stand-in for the conda-only osdag_core connection designer.

    The report path only needs the design results dictionary; connection
    design itself is irrelevant to layout/footer verification.
    """
    try:
        import osdag_core  # noqa: F401
        return
    except ImportError:
        pass

    class _Designer:
        def set_osdaglogger(self, *args, **kwargs):
            pass

        def func_for_validation(self, *args, **kwargs):
            return None

    pkg = types.ModuleType("osdag_core")
    pkg.__path__ = []
    cli = types.ModuleType("osdag_core.cli")
    cli._get_output_dictionary = lambda module: {}
    pkg.cli = cli
    sys.modules["osdag_core"] = pkg
    sys.modules["osdag_core.cli"] = cli

    paths = {
        "compression_member": (["compression_bolted", "Compression_bolted"],
                               ["compression_welded", "Compression_welded"]),
        "tension_member": (["tension_bolted", "Tension_bolted"],
                           ["tension_welded", "Tension_welded"]),
    }
    for sub, modules in paths.items():
        subpkg = types.ModuleType(f"osdag_core.design_type.{sub}")
        subpkg.__path__ = []
        sys.modules[f"osdag_core.design_type.{sub}"] = subpkg
        for mod_name, cls_name in modules:
            mod = types.ModuleType(
                f"osdag_core.design_type.{sub}.{mod_name}")
            setattr(mod, cls_name, _Designer)
            setattr(subpkg, mod_name, mod)
            sys.modules[f"osdag_core.design_type.{sub}.{mod_name}"] = mod
    design_type = types.ModuleType("osdag_core.design_type")
    design_type.__path__ = []
    sys.modules["osdag_core.design_type"] = design_type
    pkg.design_type = design_type


install_osdag_core_stub()

from osdagbridge.core.bridge_types.plate_girder.defaults import (  # noqa: E402
    BASIC_INPUT_DICT, solve_extend_basic_input_dict,
)
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (  # noqa: E402
    PlateGirderBridge,
)
from osdagbridge.core.reports.report_generator import (  # noqa: E402
    ReportMetadata, ReportOptions, ReportRequest,
    build_report_payload, generate_report,
)
from osdagbridge.core.utils.common import (  # noqa: E402
    KEY_CARRIAGEWAY_WIDTH, KEY_DESIGN_MODE, KEY_DS_REINF_MATERIAL,
    KEY_DO_GAMMA_M0, KEY_DO_GAMMA_M1, KEY_DO_GAMMA_MF, KEY_DO_GAMMA_V,
    KEY_LL_CURVE_RADIUS, KEY_LL_DESIGN_SPEED, KEY_MATERIAL_DECK_ECM,
    KEY_MATERIAL_DECK_FCK, KEY_MATERIAL_DECK_FCTM,
    KEY_MATERIAL_GIRDER_G, KEY_SC_LEFT_SUPPORT, KEY_SC_RIGHT_SUPPORT,
    KEY_SPAN, KEY_TS_GIRDER_SPACING, KEY_TS_NO_OF_GIRDERS,
    KEY_TS_OVERALL_WIDTH,
)


def full_inputs() -> dict:
    """Complete input dictionary matching a filled-in desktop UI form."""
    inputs = dict(BASIC_INPUT_DICT)
    inputs[KEY_SPAN] = 30.0
    inputs[KEY_TS_NO_OF_GIRDERS] = 4
    inputs[KEY_TS_GIRDER_SPACING] = 3.5
    inputs[KEY_CARRIAGEWAY_WIDTH] = 12.0
    inputs[KEY_TS_OVERALL_WIDTH] = 14.0
    inputs[KEY_DESIGN_MODE] = "Optimized"
    inputs[KEY_LL_CURVE_RADIUS] = 300.0
    inputs[KEY_LL_DESIGN_SPEED] = 80.0
    inputs[KEY_MATERIAL_GIRDER_G] = 76.923  # GPa (E=200 GPa, nu=0.3)
    inputs[KEY_MATERIAL_DECK_FCK] = 40.0
    inputs[KEY_MATERIAL_DECK_FCTM] = 3.5
    inputs[KEY_MATERIAL_DECK_ECM] = 35.0  # GPa
    inputs[KEY_DS_REINF_MATERIAL] = "Fe 500"
    inputs[KEY_DO_GAMMA_M0] = 1.10
    inputs[KEY_DO_GAMMA_M1] = 1.25
    inputs[KEY_DO_GAMMA_V] = 1.25
    inputs[KEY_DO_GAMMA_MF] = 1.35
    inputs[KEY_SC_LEFT_SUPPORT] = "Pinned"
    inputs[KEY_SC_RIGHT_SUPPORT] = "Roller"
    # Populate the dynamic per-girder/member keys exactly like the desktop UI.
    solve_extend_basic_input_dict(inputs)
    return inputs


def main() -> int:
    inputs = full_inputs()
    bridge = PlateGirderBridge()
    bridge.set_input(inputs)
    print("Running real OpenSees analysis + design ...")
    bridge.design()
    print(f"Design finished. output_dict keys: {len(bridge.output_dict)}")

    out_dir = str(ROOT / "deliverables")
    stem = "Report_Real_Design"
    os.makedirs(out_dir, exist_ok=True)
    meta = ReportMetadata(
        project_name="Full Design Verification Bridge",
        project_location="Mumbai, Maharashtra",
        designer="OsdagBridge Team", client="FOSSEE", company="IIT Bombay",
        job_number="OB-2026-FULL", subtitle="Rev 0",
        report_date="2026-11-22",
    )
    opts = ReportOptions(
        sections=["loads", "analysis", "design_checks", "drawings"],
        include_figures=True, include_toc=True, include_pdf=True,
    )
    request = ReportRequest(metadata=meta, options=opts,
                            output_dir=out_dir, file_stem=stem)
    payload = build_report_payload(request, dict(bridge.input_dict),
                                   dict(bridge.output_dict))
    result = generate_report(payload, request)
    print(result)
    if not result.pdf_path or not os.path.exists(result.pdf_path):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
