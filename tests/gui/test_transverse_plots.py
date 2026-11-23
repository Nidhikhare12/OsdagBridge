"""Task III - Transverse Members in the analysis plot dropdown (runs a full Design)."""

import time

import pytest
from PySide6.QtWidgets import QComboBox

from osdagbridge.core.utils.common import (
    KEY_ANALYSIS_MEMBER, KEY_ANALYSIS_LOAD_COMBINATION, VALUE_ANALYSIS_MEMBER_TRANSVERSE,
)
from osdagbridge.desktop.ui.utils.custom_widgets import CustomRadioButton

COMPONENTS = ["F<sub>x</sub>", "V<sub>y</sub>", "V<sub>z</sub>", "T<sub>x</sub>",
              "M<sub>y</sub>", "M<sub>z</sub>", "D<sub>x</sub>", "D<sub>y</sub>", "D<sub>z</sub>"]


@pytest.fixture
def designed(window, basic_inputs, messages, pump):
    messages.reply = "OK"
    window.common_design_func("Design")
    start = time.time()
    while getattr(window, "_design_running", False) and time.time() - start < 900:
        pump(300)
    pump(1000)
    assert not getattr(window, "_design_running", False), "design did not finish"
    if not window.plots_view_active:
        window.plots_view_toggle()
    pump(800)
    out = window.output_dock.output_widget
    return (window, out.findChild(QComboBox, KEY_ANALYSIS_MEMBER),
            out.findChild(QComboBox, KEY_ANALYSIS_LOAD_COMBINATION),
            {rb.text(): rb for rb in out.findChildren(CustomRadioButton)})


def test_transverse_members_plot_every_component(designed, pump):
    window, member, loadcase, radios = designed
    items = [member.itemText(i) for i in range(member.count())]
    assert items[-1] == VALUE_ANALYSIS_MEMBER_TRANSVERSE
    loadcase.setCurrentText("1.0 DL")
    member.setCurrentText(VALUE_ANALYSIS_MEMBER_TRANSVERSE)
    pump(800)
    plots = window.plots_widget
    for label in COMPONENTS:
        radios[label].setChecked(True)
        pump(400)
        assert getattr(plots._fig, "_view_kind", None) == "transverse", label
        names = list(plots._summary_data)
        assert names[0] == "ED1" and names[-1] == "ED2" and any(n.startswith("CB") for n in names)

    # Dead load bends the cross-bracings (local Mz) but does not twist them (Tx).
    radios["M<sub>z</sub>"].setChecked(True)
    pump(400)
    bending = max(max(abs(v["max"]), abs(v["min"])) for v in plots._summary_data.values())
    radios["T<sub>x</sub>"].setChecked(True)
    pump(400)
    torsion = max(max(abs(v["max"]), abs(v["min"])) for v in plots._summary_data.values())
    assert bending > 1.0 and torsion < 0.01 * bending


def test_follows_the_load_case_and_returns_to_girders(designed, pump):
    window, member, loadcase, radios = designed
    member.setCurrentText(VALUE_ANALYSIS_MEMBER_TRANSVERSE)
    radios["V<sub>y</sub>"].setChecked(True)
    loadcase.setCurrentText("1.0 DL")
    pump(500)
    dead = dict(window.plots_widget._summary_data)
    loadcase.setCurrentText("Case1 2xClassA")
    pump(500)
    assert window.plots_widget._summary_data != dead
    member.setCurrentText("G2")
    pump(500)
    assert getattr(window.plots_widget._fig, "_view_kind", "longitudinal") != "transverse"


TOGGLES = ["summary", "max", "min", "all_vals", "nodes", "axis", "supports", "grid",
           "girder_labels", "node_numbers", "element_numbers", "grillage"]


def test_every_plot_toggle_works_on_the_transverse_plot(designed, pump):
    window, member, loadcase, radios = designed
    plots = window.plots_widget
    loadcase.setCurrentText("1.0 DL")
    member.setCurrentText(VALUE_ANALYSIS_MEMBER_TRANSVERSE)
    radios["M<sub>z</sub>"].setChecked(True)
    pump(500)
    for name in TOGGLES:
        handler = getattr(plots, f"_on_{name}_toggled")
        handler(True)                                 # exceptions propagate to pytest here
        pump(150)
        handler(False)
        pump(150)
    assert getattr(plots._fig, "_view_kind", None) == "transverse"

    def visible(gid):
        return [a.get_visible() for a in plots._fig.axes[0].get_children() if a.get_gid() == gid]

    for gid, handler in (("max_line", plots._on_max_toggled),
                         ("min_line", plots._on_min_toggled),
                         ("all_vals", plots._on_all_vals_toggled)):
        handler(True)
        assert visible(gid) and all(visible(gid)), gid
        handler(False)
        assert not any(visible(gid)), gid
