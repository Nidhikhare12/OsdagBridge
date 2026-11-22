# Multi-Run Stability & State Isolation Test Specifications

## 1. Overview & Objectives

In interactive desktop engineering applications, users frequently perform multiple iterative design runs in a single session—adjusting spans, changing material grades, and re-running solvers without restarting the application.

A critical failure mode in structural software is **state pollution**, where variables, cached OpenCASCADE 3D entities, solver nodes, or output dictionaries persist across runs, corrupting subsequent analyses.

This test suite evaluates:
1. **Determinism**: Identical inputs on consecutive runs yield bit-for-bit identical results.
2. **State Isolation**: Modifying a parameter in Run 2 does not leave phantom values in Run 3.
3. **Memory & Resource Management**: No accumulation of dangling AIS graphics contexts or PySide widgets across repeated design cycles.

---

## 2. Multi-Run Test Protocol

Every multi-run test follows the 3-Run Protocol:
- **Run 1**: Baseline Configuration (e.g., $L = 25\text{ m}$). Execute analysis $\rightarrow$ Record outputs.
- **Run 2**: Modified Configuration (e.g., $L = 35\text{ m}$, Custom steel). Execute analysis $\rightarrow$ Record outputs.
- **Run 3**: Restore Baseline Configuration ($L = 25\text{ m}$). Execute analysis $\rightarrow$ Compare outputs directly with Run 1.

---

## 3. Test Cases Specification

### Test Case: TC_MR_001 – Consecutive Identical Solve Determinism
- **Test ID**: `TC_MR_001`
- **Test Objective**: Verify that running the identical design solve twice consecutively without altering inputs produces identical results and does not cause runtime errors.
- **Preconditions**: OsdagBridge open; Plate Girder initialized with default parameters.
- **Execution Steps**:
  1. Set Span = $25.0\text{ m}$, Width = $7.5\text{ m}$, Skew = $0.0^\circ$.
  2. Click **Run Design** $\rightarrow$ Wait for completion $\rightarrow$ Capture `output_dict_1`.
  3. Without changing any input or closing the app, click **Run Design** again $\rightarrow$ Capture `output_dict_2`.
  4. Compare `output_dict_1` and `output_dict_2` using `compare_dictionaries.py`.
- **Expected Result**:
  1. Both runs complete successfully without exceptions.
  2. `compare_dictionaries.py` reports zero key differences and zero numerical drift ($|v_1 - v_2| \le 10^{-6}$).
  3. Matplotlib plot and 3D CAD window update cleanly without blanking out.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_MR_001`
- **Remarks**: Deterministic execution check.

---

### Test Case: TC_MR_002 – 3-Run Alternating Parameter State Isolation
- **Test ID**: `TC_MR_002`
- **Test Objective**: Verify that modifying parameters in Run 2 does not contaminate Run 3 when reverting back to Run 1 parameters.
- **Preconditions**: Same as TC_MR_001.
- **Execution Steps**:
  1. **Run 1**: Span = $20.0\text{ m}$, Girders = 3, Material = E250. Solve and dump state `state_run1.json`.
  2. **Run 2**: Span = $36.0\text{ m}$, Girders = 5, Material = E410. Solve and dump state `state_run2.json`.
  3. **Run 3**: Span = $20.0\text{ m}$, Girders = 3, Material = E250. Solve and dump state `state_run3.json`.
  4. Compare `state_run3.json` against `state_run1.json`.
- **Expected Result**:
  1. `state_run3.json` matches `state_run1.json` exactly.
  2. No residue from Run 2 (e.g., 5-girder cross-sections, E410 yield strength, or longer span moments) persists in Run 3.
  3. Output dock displays only Run 3 calculations.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_MR_002`
- **Remarks**: Essential state isolation verification.

---

### Test Case: TC_MR_003 – Extended Multi-Run Memory & Graphics Stability
- **Test ID**: `TC_MR_003`
- **Test Objective**: Verify application stability and memory containment across 5 consecutive design runs with varying parameters.
- **Preconditions**: OsdagBridge open; system memory monitor attached.
- **Execution Steps**:
  1. Execute Run 1: Span 15m.
  2. Execute Run 2: Span 22m, Skew 15 deg.
  3. Execute Run 3: Span 30m, Skew 0 deg.
  4. Execute Run 4: Span 38m, Skew -30 deg.
  5. Execute Run 5: Span 25m, Skew 0 deg.
  6. Inspect memory consumption (RAM usage) and responsiveness after each run.
- **Expected Result**:
  1. All 5 runs complete without application crash or freezing.
  2. OpenCASCADE display removes previous AIS interactive shapes (`_clear_previous_ais` called cleanly).
  3. Memory consumption plateaus without monotonic escalation indicative of memory leaks.
- **Actual Result**: *(To be recorded upon execution)*
- **Status**: Pending Execution
- **Evidence Reference**: `LOG_MR_003`
- **Remarks**: Memory guard and stability stress test.
