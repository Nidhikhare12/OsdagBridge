# OsdagBridge Testing Submission
**Author:** Pujari Abhiram  
**Programme:** B.Tech Civil Engineering, 3rd Year  
**Task:** FOSSEE/Osdag Bridge Module Screening Test  
**Supervisor:** Nidhikhare12  
**Repository:** https://github.com/Nidhikhare12/OsdagBridge (branch: dev)

---

## Folder Structure

```
submission/
├── test_cases/
│   ├── TC01_Baseline_18m.osi          ← Span 20 m, E 350A, M40
│   ├── TC02_Consecutive_24m.osi       ← Span 24 m, Skew 15°, consecutive run
│   └── TC03_Custom_Material.osi       ← Span 24 m, custom_steel_450_570 + custom_concrete_45_1.6
├── figures/
│   ├── fig_dock_op.png                ← Full window: inputs + 3D model + Output Dock
│   ├── fig_d_b.png                    ← 3D bridge model angled view (TC03)
│   └── fig_plots.png                  ← 3D model with member overlays
├── report/
│   ├── generate_report.py             ← Python script used to generate the PDF
│   └── testing_report.pdf             ← Compiled testing report (9 sections)
├── logs/
│   └── input_dict_comparison.json     ← Key input_dict values extracted from all 3 .osi files
├── issues/
│   ├── issue_1_segment_table_bug.md   ← GitHub Issue #1: stale segment tables (ready to post)
│   └── issue_2_crossbracing_db_bug.md ← GitHub Issue #2: cross-bracing DB table name mismatch
└── README.md                          ← This file
```

---

## How to Reproduce the Test Cases

### Prerequisites
```bash
conda create -n osdagbridge-env python=3.12
conda activate osdagbridge-env
pip install -e .
pip install openseespy==3.8.0.0 opsvis==1.3.8 PySide6==6.11.3 reportlab
```
> **Note:** On Windows 11 with Smart App Control enabled, conda-forge DLLs (PySide6, numpy C extensions) will be blocked. Disable Smart App Control in Windows Security → App & Browser Control before running.

### Running the Tests
1. Launch the application: `python -m osdagbridge` (or via the installed entry point)
2. Enter inputs as specified in `report/testing_report.pdf`, Section 3 (Test Case Matrix)
3. Click **Design**, then **Save Input** after each run

### Opening .osi Files
`.osi` files are YAML. Open in any text editor or parse with:
```python
import yaml
with open("TC01_Baseline_18m.osi") as f:
    d = yaml.safe_load(f)
print(d["geometry.span"])  # 20.0
```

---

## Bugs Found

| # | File | Severity | Summary |
|---|------|----------|---------|
| A | defaults.py ~L555 | Critical | Girder segment tables G2–G8 retain old span after consecutive run |
| B | crossbracingforces.py ~L658 / Intg_osdag.sqlite | Critical | Cross-bracing skipped: `no such table: Material` |
| C | designer.py ~L309-315 | High | ValueError on missing shear modulus in headless/OSI reload |
| D | defaults.py ~L908 | High | TypeError when carriageway width is None |

Full details with code snippets and suggested fixes: see `report/testing_report.pdf`, Section 7.  
GitHub-ready markdown for the two critical issues: see `issues/` folder.

---

## Screenshots

| File | Contents |
|------|----------|
| `fig_dock_op.png` | Full OsdagBridge window showing Basic Inputs, 3D model at 24 m span with cross bracings visible, and Output Dock DCR values for G1 under SW load case |
| `fig_d_b.png` | Rotated 3D bridge model — deck hidden, girders and cross bracings visible, skewed end clearly shown |
| `fig_plots.png` | 3D structural model with Bridge, Girder, Deck, and Cross Bracing visibility toggled |
