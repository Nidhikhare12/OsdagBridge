"""Minimal compatibility shim for osdag.cli._get_output_dictionary.

This module is used only as a fallback when the installed `osdag` package
does not provide osdag.cli._get_output_dictionary. The implementation is
conservative: it prefers well-known attributes/methods on the module instance
(e.g. output_dict, results, get_output_dict) and otherwise returns a dict of
public, non-callable attributes as a last resort.

Keep the function signature and behaviour simple so it can be a drop-in
replacement for the original helper used by OsdagBridge.
"""
from typing import Any, Dict


def _get_output_dictionary(module_instance: Any) -> Dict[str, Any]:
    """Return a dictionary representation of a design module's outputs.

    The function tries several common attribute/method names used by osdag
    design modules. If none yield a dict-like value, it falls back to
    collecting public, non-callable attributes from the instance.
    """
    # Preferred attribute/method names to try (in order)
    candidates = [
        "output_dict",
        "output",
        "results",
        "design_output",
        "output_data",
        "get_output_dict",
        "get_results",
    ]

    for name in candidates:
        if hasattr(module_instance, name):
            attr = getattr(module_instance, name)
            # If callable, try calling it (safe-guarded)
            if callable(attr):
                try:
                    value = attr()
                except Exception:
                    value = None
            else:
                value = attr

            if isinstance(value, dict):
                return value
            # Try to coerce mapping-like objects to dict
            try:
                return dict(value)  # type: ignore[arg-type]
            except Exception:
                # Not dict-like; continue
                pass

    # Last resort: collect public, non-callable attributes
    output = {}
    try:
        for key, val in vars(module_instance).items():
            if key.startswith("_"):
                continue
            if callable(val):
                continue
            try:
                output[key] = val
            except Exception:
                # Skip attributes that raise on access
                continue
    except Exception:
        # If vars() fails, return empty dict
        return {}

    return output
