"""Export the sample bridge (superstructure + substructure) to IFC4 without the GUI.

Uses the same path as File -> Save 3D Model -> IFC (PlateGirderIfcExportHandler).

Usage (from the repo root):
    python scripts/substructure/export_sample_ifc.py [out_dir] [skew_deg ...]
    python scripts/substructure/export_sample_ifc.py samples 0 10
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "..", "src"), os.path.join(HERE, "..", "..", "tests", "integration")]

from sample_params import sample_params  # noqa: E402
from osdagbridge.core.ifc_export_bridge.export_ifc_handler import PlateGirderIfcExportHandler  # noqa: E402

out_dir = sys.argv[1] if len(sys.argv) > 1 else "samples"
skews = [float(a) for a in sys.argv[2:]] or [0.0, 10.0]
os.makedirs(out_dir, exist_ok=True)
for skew in skews:
    path = os.path.join(out_dir, f"osdagbridge_super_sub_skew{int(skew)}.ifc")
    PlateGirderIfcExportHandler(sample_params(skew), path,
                                lambda ok, msg: print(("OK  " if ok else "ERR ") + msg)).export()
