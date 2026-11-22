#!/usr/bin/env python3
"""
Input Validation Script for OsdagBridge Project Files
====================================================

This script validates input files (.osi or .json) against OsdagBridge's
canonical validation rules using `BridgeInputValidator` and `validate_osi_inputs`.

If the OsdagBridge package is available in the environment, it uses the native
validator modules. Otherwise, it executes a standalone baseline validation suite.

Usage:
    python validate_inputs.py path/to/project.osi
    python validate_inputs.py --dir path/to/osi_files/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Try importing native OsdagBridge validators
try:
    from osdagbridge.core.utils.osi_validator import validate_osi_inputs, OsiValidationResult
    from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
    NATIVE_VALIDATOR_AVAILABLE = True
except ImportError:
    NATIVE_VALIDATOR_AVAILABLE = False


# Canonical fallback bounds when running in standalone mode
FALLBACK_BOUNDS = {
    "geometry.span": (12.0, 45.0, "Span length (m)"),
    "geometry.carriageway_width": (4.25, 24.0, "Carriageway width (m)"),
    "geometry.skew_angle": (-60.0, 60.0, "Skew angle (degrees)"),
    "material.girder.fy": (100.0, 1200.0, "Steel Yield Strength (MPa)"),
    "material.girder.fu": (100.0, 1500.0, "Steel Ultimate Strength (MPa)"),
    "material.girder.e": (100.0, 300.0, "Steel Modulus E (GPa)"),
    "material.deck.fck": (20.0, 100.0, "Concrete Deck fck (MPa)"),
}


def validate_standalone(data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """Standalone fallback validation if osdagbridge package is not installed."""
    errors = []
    warnings = []

    for key, (min_v, max_v, desc) in FALLBACK_BOUNDS.items():
        if key in data:
            val = data[key]
            try:
                fval = float(val)
                if fval < min_v or fval > max_v:
                    errors.append(
                        f"Field '{key}' ({desc}) with value {fval} is outside allowed range [{min_v}, {max_v}]."
                    )
            except (ValueError, TypeError):
                errors.append(f"Field '{key}' ({desc}) must be numeric, got: {val!r}")

    return len(errors) == 0, errors, warnings


def validate_file(filepath: Path) -> bool:
    """Validate a single project file."""
    print(f"\nValidating: {filepath.name}")
    print("-" * 50)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Could not parse file as JSON/OSI: {e}")
        return False

    if not isinstance(data, dict):
        print("  [ERROR] Root structure is not a dictionary.")
        return False

    if NATIVE_VALIDATOR_AVAILABLE:
        print("  [INFO] Running native OsdagBridge BridgeInputValidator...")
        result = validate_osi_inputs(data)
        if result.is_valid:
            print("  [PASS] File is valid according to OsdagBridge rules.")
            if result.warnings:
                for w in result.warnings:
                    print(f"  [WARNING] {w}")
            return True
        else:
            print("  [FAIL] Validation issues identified:")
            for err in result.errors:
                print(f"    - {err}")
            return False
    else:
        print("  [INFO] Running standalone boundary validator (native core not detected in PYTHONPATH)...")
        is_valid, errors, warnings = validate_standalone(data)
        if is_valid:
            print("  [PASS] File passed basic boundary checks.")
            return True
        else:
            print("  [FAIL] Boundary check failures:")
            for err in errors:
                print(f"    - {err}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate OsdagBridge project files (.osi / .json)"
    )
    parser.add_argument("path", nargs="?", default=None, type=Path, help="Path to single file or directory")
    parser.add_argument("--dir", "-d", type=Path, default=None, help="Directory containing .osi files to batch validate")

    args = parser.parse_args()

    target_dir = args.dir
    target_file = args.path

    if target_dir:
        files = list(target_dir.glob("*.osi")) + list(target_dir.glob("*.json"))
        if not files:
            print(f"No .osi or .json files found in {target_dir}")
            sys.exit(0)
        passes = 0
        for f in files:
            if validate_file(f):
                passes += 1
        print(f"\nBatch Summary: {passes}/{len(files)} files passed validation.")
    elif target_file:
        if target_file.is_dir():
            files = list(target_file.glob("*.osi")) + list(target_file.glob("*.json"))
            passes = sum(1 for f in files if validate_file(f))
            print(f"\nBatch Summary: {passes}/{len(files)} files passed validation.")
        else:
            validate_file(target_file)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
