from osdagbridge.core.bridge_types.plate_girder.defaults import BASIC_INPUT_DICT, solve_extend_basic_input_dict
from osdagbridge.core.utils import common as key


def test_default_expansion_preserves_explicit_values():
    inputs = {**BASIC_INPUT_DICT, key.KEY_SPAN: 24, key.KEY_SKEW_ANGLE: 0,
              key.KEY_CARRIAGEWAY_WIDTH: 7.5}
    edits = {
        key.KEY_LL_IRC_CLASS_A: False,
        key.KEY_LL_CUSTOM_VEHICLES: [{"name": "Project Vehicle"}],
        key.KEY_LL_FOOTPATH_PRESSURE_MODE: "User-defined",
        key.KEY_LL_FOOTPATH_PRESSURE_VALUE: 0,
        key.KEY_WL_GUST_FACTOR_VALUE: 0.9,
        key.KEY_SC_LEFT_SUPPORT: "Roller",
        key.KEY_DS_TOP_CLEAR_COVER: "75",
        key.KEY_DO_ULS_BENDING: False,
    }
    inputs.update(edits)
    solve_extend_basic_input_dict(inputs)
    assert {field: inputs[field] for field in edits} == edits
    assert inputs[key.KEY_LL_IRC_70R_WHEELED] is True


def test_desktop_osi_save_round_trip_and_cancel(monkeypatch, tmp_path):
    from types import SimpleNamespace
    import yaml
    from osdagbridge.desktop.ui import template_page

    original = {**BASIC_INPUT_DICT, key.KEY_SPAN: 24, key.KEY_SKEW_ANGLE: 0,
                key.KEY_CARRIAGEWAY_WIDTH: 7.5, key.KEY_LL_IRC_CLASS_A: False,
                key.KEY_LL_FOOTPATH_PRESSURE_VALUE: 0, key.KEY_SC_LEFT_SUPPORT: "Roller"}
    owner = SimpleNamespace(input_dict=original.copy())
    monkeypatch.setattr(template_page.QFileDialog, "getSaveFileName", lambda *args: ("", ""))
    template_page.CustomWindow.saveOSI_inputs(owner)
    assert owner.input_dict == original

    path = tmp_path / "bridge.osi"
    monkeypatch.setattr(template_page.QFileDialog, "getSaveFileName", lambda *args: (str(path), ""))
    monkeypatch.setattr(template_page, "CustomMessageBox", lambda **kwargs: SimpleNamespace(exec=lambda: None))
    template_page.CustomWindow.saveOSI_inputs(owner)
    saved = yaml.safe_load(path.read_text())
    solve_extend_basic_input_dict(saved)
    assert saved[key.KEY_LL_IRC_CLASS_A] is False
    assert saved[key.KEY_LL_FOOTPATH_PRESSURE_VALUE] == 0
    assert saved[key.KEY_SC_LEFT_SUPPORT] == "Roller"
    assert owner.input_dict == original
