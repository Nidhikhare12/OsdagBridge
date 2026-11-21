"""
Cross-field checks for custom steel materials (fu > fy, G = E / (2(1 + nu))).

The first group tests BridgeInputValidator directly. The second group drives
the real MaterialPropertiesDialog off-screen and is skipped when PySide6 is
not installed.
"""

import os

import pytest

from osdagbridge.core.bridge_types.plate_girder.validator import BridgeInputValidator
from osdagbridge.core.utils.common import (
    KEY_GIRDER,
    KEY_MATERIAL_GIRDER_DENSITY, KEY_MATERIAL_GIRDER_FY, KEY_MATERIAL_GIRDER_FU,
    KEY_MATERIAL_GIRDER_E, KEY_MATERIAL_GIRDER_G, KEY_MATERIAL_GIRDER_POISSON,
    KEY_MATERIAL_GIRDER_THERMAL,
)

# A valid custom steel, as typed in the dialog (strings).
VALID_STEEL = {
    KEY_MATERIAL_GIRDER_DENSITY: "78.5",
    KEY_MATERIAL_GIRDER_FY: "410",
    KEY_MATERIAL_GIRDER_FU: "540",
    KEY_MATERIAL_GIRDER_E: "200",
    KEY_MATERIAL_GIRDER_G: "76.9",
    KEY_MATERIAL_GIRDER_POISSON: "0.3",
    KEY_MATERIAL_GIRDER_THERMAL: "12",
}


def _steel(**changes):
    values = dict(VALID_STEEL)
    values.update(changes)
    return values


# ── Validator ──────────────────────────────────────────────────────────────

@pytest.fixture
def validator():
    return BridgeInputValidator()


def test_valid_steel_has_no_errors(validator):
    assert validator.validate_material_consistency(VALID_STEEL) == []


def test_fu_below_fy_is_rejected(validator):
    errors = validator.validate_material_consistency(
        _steel(**{KEY_MATERIAL_GIRDER_FY: "450", KEY_MATERIAL_GIRDER_FU: "400"}))
    assert len(errors) == 1
    assert "Fu (400 MPa) must be greater than" in errors[0]


def test_fu_equal_to_fy_is_rejected(validator):
    errors = validator.validate_material_consistency(
        _steel(**{KEY_MATERIAL_GIRDER_FY: "410", KEY_MATERIAL_GIRDER_FU: "410"}))
    assert len(errors) == 1


def test_inconsistent_shear_modulus_is_rejected(validator):
    # E 200 GPa, nu 0.3 -> G = 76.9 GPa; 120 GPa is in the per-field range
    # (30-120) but physically impossible.
    errors = validator.validate_material_consistency(_steel(**{KEY_MATERIAL_GIRDER_G: "120"}))
    assert len(errors) == 1
    assert "76.9 GPa" in errors[0]


@pytest.mark.parametrize("e, nu, g", [
    ("200", "0.3", "77"),     # G rounded to a whole number
    ("210", "0.3", "80.8"),   # different E
    ("205", "0.28", "80.1"),  # different nu
])
def test_consistent_shear_modulus_is_accepted(validator, e, nu, g):
    values = _steel(**{KEY_MATERIAL_GIRDER_E: e, KEY_MATERIAL_GIRDER_POISSON: nu,
                       KEY_MATERIAL_GIRDER_G: g})
    assert validator.validate_material_consistency(values) == []


def test_both_errors_are_reported_together(validator):
    errors = validator.validate_material_consistency(_steel(**{
        KEY_MATERIAL_GIRDER_FY: "450", KEY_MATERIAL_GIRDER_FU: "400",
        KEY_MATERIAL_GIRDER_G: "120"}))
    assert len(errors) == 2


def test_missing_or_non_numeric_values_are_left_to_the_per_field_check(validator):
    assert validator.validate_material_consistency({}) == []
    assert validator.validate_material_consistency(
        _steel(**{KEY_MATERIAL_GIRDER_FU: "abc", KEY_MATERIAL_GIRDER_E: ""})) == []


# ── Dialog (off-screen) ────────────────────────────────────────────────────

@pytest.fixture
def qt_app():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


@pytest.fixture
def dialog_messages(qt_app, monkeypatch):
    """Record message boxes instead of showing them."""
    from osdagbridge.desktop.ui.dialogs import material_properties as mp

    shown = []

    def fake_exec(box):
        shown.append(box)
        return 0

    monkeypatch.setattr(mp.CustomMessageBox, "exec", fake_exec)
    return shown


def _save_custom_steel(values):
    from PySide6.QtWidgets import QDialog
    from osdagbridge.desktop.ui.dialogs.material_properties import MaterialPropertiesDialog

    dialog = MaterialPropertiesDialog(read_only=False, selected_material="", member=KEY_GIRDER)
    for key, text in values.items():
        dialog.field_inputs[key].setText(text)
    dialog._validate_and_save()
    return dialog.result() == QDialog.Accepted


def test_dialog_saves_a_valid_custom_steel(dialog_messages):
    assert _save_custom_steel(VALID_STEEL)
    assert dialog_messages == []


@pytest.mark.parametrize("changes", [
    {KEY_MATERIAL_GIRDER_FY: "450", KEY_MATERIAL_GIRDER_FU: "400"},
    {KEY_MATERIAL_GIRDER_G: "120"},
], ids=["fu_below_fy", "G_inconsistent"])
def test_dialog_rejects_inconsistent_custom_steel(dialog_messages, changes):
    assert not _save_custom_steel(_steel(**changes))
    assert len(dialog_messages) == 1


def test_every_database_steel_grade_passes(qt_app):
    from osdagbridge.desktop.ui.dialogs.material_properties import STEEL_MATERIAL_BASE_VALUES

    assert STEEL_MATERIAL_BASE_VALUES, "steel grade table did not load"
    validator = BridgeInputValidator()
    for grade, v in STEEL_MATERIAL_BASE_VALUES.items():
        values = {
            KEY_MATERIAL_GIRDER_FY: v["Fy"], KEY_MATERIAL_GIRDER_FU: v["Fu"],
            KEY_MATERIAL_GIRDER_E: v["E"], KEY_MATERIAL_GIRDER_G: v["G"],
            KEY_MATERIAL_GIRDER_POISSON: v["Poisson"],
        }
        assert validator.validate_material_consistency(values) == [], grade
