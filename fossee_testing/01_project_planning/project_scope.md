# Project Scope: OsdagBridge Software Testing

## 1. Project Overview

OsdagBridge is a modular, multi-interface structural engineering software application designed for the automated analysis and design of bridge structures compliant with Indian Standard codes. The system features a unified Python core (`osdagbridge.core`) accessible via a desktop Qt GUI (`PySide6`), command-line interface (`osdagbridge.cli`), and web architecture.

This project encompasses testing, validation, issue identification, and documentation for the **FOSSEE Winter Internship 2026 Screening Task**.

---

## 2. In-Scope Modules & Components

Testing activities focus strictly on the following functional areas within OsdagBridge:

### 2.1 Superstructure: Steel-Concrete Composite Plate Girder Bridge
- **Geometric Configuration**:
  - Span length: Single span supported from $12.0\text{ m}$ to $45.0\text{ m}$.
  - Carriageway widths: Single lane, two lane, multi-lane ($4.25\text{ m}$ to $24.0\text{ m}$).
  - Skew angles: Right and skewed alignments ($-60^\circ$ to $+60^\circ$).
  - Transverse geometry: Girder spacing, deck overhang, slab thickness, footpath width, and crash barrier dimensions.
- **Material Models**:
  - Structural Steel: Standard grades (E250, E350, E410, E450) and Custom User-Defined properties.
  - Concrete Deck: Standard grades (M30 to M60) and Custom User-Defined concrete properties.
  - Shear Connectors: Headed studs yield and ultimate tensile capacities.

### 2.2 Loading & Analysis Configurations
- **Dead Loads & Superimposed Dead Loads**: Concrete deck slab, wearing coat, crash barriers, handrails, utilities.
- **Live Loads (IRC:6–2017)**:
  - Class A Wheeled & Tracked
  - Class 70R Wheeled & Tracked
  - Class 70R Bogie Loading
  - Special Vehicle (SV) configurations
  - Congestion factors, impact factors, eccentricity parameters.
- **Environmental Loads**:
  - Wind loads: Drag and lift coefficients, gust factor, exposed frontal area.
  - Seismic loads: Importance factor, response reduction factor, fundamental period, zone factor.
  - Thermal effects: Uniform temperature rise and fall, differential thermal gradient across depth.

### 2.3 Solvers & Analysis Engines
- Verification of grillage discretization model via `ospgrillage` and `OpenSeesPy`.
- Evaluation of internal force envelopes: Max bending moment ($M_u$), max shear force ($V_u$), mid-span deflection ($\delta_{max}$).

### 2.4 User Interface & Visualizations
- **PySide6 Desktop Application**:
  - Basic input page, Additional inputs dialog, Material specification dock.
  - Save project (`.osi`), Load project (`.osi`), Reset inputs.
- **3D CAD Visualization**:
  - OpenCASCADE / pythonocc-core rendering of girder flanges, webs, stiffeners, cross frames, deck slab.
  - Part visibility controls, wireframe mode, coordinate axes, zoom/pan/rotate responsiveness.
- **2D Structural Plots**:
  - Matplotlib integration dock displaying BMD, SFD, Deflection along longitudinal girders across selected load combinations.

### 2.5 Data Contracts & Automation
- Integrity of `input_dict` and `output_dict` keys.
- Automation scripts for dictionary comparison, input validation, and summary reporting.

---

## 3. Out-of-Scope Items

To ensure high depth of coverage on core engineering functions, the following are designated out of scope:
1. **Unimplemented Bridge Types**: Cable-stayed, suspension, and arch bridge types (placeholders in architecture).
2. **Substructure Detailed Design**: Detailed design of pier caps, piers, abutments, and well/pile foundations (focus remains on superstructure girder design).
3. **Web Interface Backend**: Full deployment of Django + React web stack (desktop GUI and core Python APIs serve as primary test targets).
4. **Third-Party Commercial FEA**: Direct verification against proprietary commercial solvers (AASHTO / CSI Bridge / Midas Civil) unless benchmark literature data is explicitly cited.

---

## 4. Testing Assumptions & Limitations

- **Hardware Platform**: 64-bit Windows workstation with dedicated or integrated OpenGL graphics capable of rendering OpenCASCADE CAD viewports.
- **Environment**: Tested within designated Conda / virtual environment containing pinned dependencies (`PySide6`, `pythonocc-core`, `openseespy`, `ospgrillage`).
- **Code Non-Interference**: Testing is strictly non-invasive; tests will identify and document root causes without modifying original application code during testing setup.

---

## 5. Expected Deliverables

1. **Test Documentation**:
   - Master Test Case Register (`test_case_register.csv`)
   - Detailed Markdown test specs (`basic_input_tests.md`, `custom_material_tests.md`, etc.)
   - Test Parameters Catalog (`test_parameters.md`)
2. **Execution & Issue Tracking**:
   - Execution Summary Register (`execution_summary.csv`) supporting 3+ consecutive design runs.
   - Defect Bug Register (`bug_register.csv`) with full root-cause analyses and suggested code fixes.
3. **Automation Tooling**:
   - Python tools (`compare_dictionaries.py`, `validate_inputs.py`, `generate_test_summary.py`).
4. **Comprehensive LaTeX Technical Report**:
   - Compilable LaTeX source structure with 14 modular section chapters, bibliography, and figures.
5. **Demonstration Video & Submission Pack**:
   - Detailed storyboard/plan and completed pre-submission checklist.
