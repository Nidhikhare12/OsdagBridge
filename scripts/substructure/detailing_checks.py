"""Print / save the substructure detailing checks for the default parameters
(or a pier/pile variant) - IS 456, IRC 112, IS 2911, IRC 78.

Usage:  python scripts/substructure/detailing_checks.py [out.csv]
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from osdagbridge.core.bridge_components.sub_structure.substructure_builder import (  # noqa: E402
    SubstructureParams, substructure_layout, run_detailing_checks,
)

params = SubstructureParams()
supports = substructure_layout(params, span_length=25000, soffit_z=-710, deck_width=16450,
                               girder_y_positions=[-5500, -2750, 0, 2750, 5500])
rows = run_detailing_checks(params, supports, "M35")
cols = ["status", "component", "check", "reference", "required", "provided", "note"]
for r in rows:
    print(f"{r['status']:4s}  {r['component']:10s}  {r['check']:42s}  req {r['required']:>18s}  "
          f"prov {str(r['provided']):>10s}  {r['note']}")
if len(sys.argv) > 1:
    with open(sys.argv[1], "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows({k: r[k] for k in cols} for r in rows)
    print("written", sys.argv[1])
