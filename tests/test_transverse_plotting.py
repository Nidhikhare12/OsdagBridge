import os
import sys
import pytest
from PySide6.QtWidgets import QApplication, QComboBox
from PySide6.QtCore import Qt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_SKEW_ANGLE,
    KEY_ANALYSIS_MEMBER,
    KEY_ANALYSIS_MEMBER_TYPE,
    KEY_ANALYSIS_LOAD_COMBINATION,
)
from osdagbridge.desktop.ui.template_page import CustomWindow
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.defaults import solve_extend_basic_input_dict
from osdagbridge.core.bridge_types.plate_girder.plot_generator import (
    _find_transverse_lines,
    build_figure_transverse,
    build_figure_sfd,
    build_figure_bmd,
    build_figure_deflection,
)

@pytest.fixture(scope="session")
def analyzed_window():
    """Create and analyze a sample bridge once for all Task III tests."""
    app = QApplication.instance() or QApplication(sys.argv)
    win = CustomWindow("Test Task 3", PlateGirderBridge)
    win.input_dict[KEY_SPAN] = 25.0
    win.input_dict[KEY_CARRIAGEWAY_WIDTH] = 7.5
    win.input_dict[KEY_SKEW_ANGLE] = 0.0
    win.input_dict["project.location"] = {}
    solve_extend_basic_input_dict(win.input_dict)
    win._get_additional_inputs()
    win.input_dock._prime_material_inputs()
    win._sync_compute_results_to_input_dict()
    win.backend.set_input(win.input_dict)
    win.backend.design()

    ds_all = win.backend.get_results_dataset()
    loadcases = win.backend.get_available_loadcases()
    nodes, members = win.backend.get_nodes_members()
    edge_dist = win.backend.get_edge_dist()

    win.output_dock.refresh_loadcase_dropdowns()
    win.output_dock.refresh_member_dropdown()
    win.plots_widget.setup(ds_all, loadcases, nodes, members, edge_dist=edge_dist)
    win.plots_widget.link_output_dock(win.output_dock)
    return win

def test_transverse_lines_identification(analyzed_window):
    """Verify that _find_transverse_lines identifies ED1, ED2, and intermediate CB lines."""
    nodes, members = analyzed_window.backend.get_nodes_members()
    lines = _find_transverse_lines(nodes, members)
    assert len(lines) >= 3, "Model must have at least start edge, end edge, and intermediate lines"

    # Verify first line is at start of span (x ≈ 0)
    assert abs(lines[0]["x"] - 0.0) < 0.1, "First line must be at x ≈ 0 (End Diaphragm 1)"

    # Verify last line is at end of span (x ≈ 25)
    assert abs(lines[-1]["x"] - 25.0) < 0.1, "Last line must be at x ≈ 25 (End Diaphragm 2)"

    # Check that each line has ordered elements and continuous stations
    for line in lines:
        assert len(line["elements"]) > 0
        assert len(line["stations"]) == len(line["nodes"])
        assert line["stations"][0] == 0.0
        assert line["stations"][-1] > 0.0

def test_end_diaphragm_all_components(analyzed_window):
    """Verify plot generation for End Diaphragms across all 9 force, moment, and displacement components."""
    ds_all = analyzed_window.backend.get_results_dataset()
    nodes, members = analyzed_window.backend.get_nodes_members()
    lc = analyzed_window.backend.get_available_loadcases()[0]
    ds = ds_all.sel(Loadcase=lc)

    components = ["Fx", "Fy", "Fz", "Mx", "My", "Mz", "Dx", "Dy", "Dz"]
    for comp in components:
        fig, summary = build_figure_transverse(
            ds,
            member_type="End Diaphragms",
            selected_member="End Diaphragm 1 (Start)",
            force_key=comp,
            nodes=nodes,
            members=members,
            loadcase=lc,
        )
        assert isinstance(fig, Figure)
        assert len(fig.axes) == 1
        ax = fig.axes[0]
        # Must be 2D axis, not 3D
        assert not isinstance(ax, Axes3D)
        # Must have lines drawn
        assert len(ax.lines) >= 1
        # Check summary data contains max and min
        assert len(summary) >= 1
        for member_name, s_vals in summary.items():
            assert "max" in s_vals
            assert "min" in s_vals

def test_cross_bracing_all_components(analyzed_window):
    """Verify plot generation for Cross Bracings across forces, moments, and displacements."""
    ds_all = analyzed_window.backend.get_results_dataset()
    nodes, members = analyzed_window.backend.get_nodes_members()
    lc = analyzed_window.backend.get_available_loadcases()[0]
    ds = ds_all.sel(Loadcase=lc)

    # Test single cross bracing and "All"
    for sel in ["Cross Bracing 1", "All"]:
        fig, summary = build_figure_transverse(
            ds,
            member_type="Cross Bracings",
            selected_member=sel,
            force_key="Fy",
            nodes=nodes,
            members=members,
            loadcase=lc,
        )
        assert isinstance(fig, Figure)
        assert len(fig.axes) == 1
        ax = fig.axes[0]
        assert not isinstance(ax, Axes3D)
        assert len(ax.lines) >= 1

def test_output_dock_member_type_dropdown(analyzed_window):
    """Verify that OutputDock member type dropdown populates and filters member dropdown."""
    dock = analyzed_window.output_dock
    combo_type = dock._w(KEY_ANALYSIS_MEMBER_TYPE)
    combo_member = dock._w(KEY_ANALYSIS_MEMBER)

    assert combo_type is not None
    assert combo_member is not None

    # 1. Select Longitudinal Members
    combo_type.setCurrentText("Longitudinal Members")
    items_long = [combo_member.itemText(i) for i in range(combo_member.count())]
    assert "All" in items_long
    assert "G1" in items_long

    # 2. Select End Diaphragms
    combo_type.setCurrentText("End Diaphragms")
    items_ed = [combo_member.itemText(i) for i in range(combo_member.count())]
    assert "All" in items_ed
    assert "End Diaphragm 1 (Start)" in items_ed
    assert "End Diaphragm 2 (End)" in items_ed

    # 3. Select Cross Bracings
    combo_type.setCurrentText("Cross Bracings")
    items_cb = [combo_member.itemText(i) for i in range(combo_member.count())]
    assert "All" in items_cb
    assert any("Cross Bracing" in item for item in items_cb)

def test_plot_widget_transverse_plot_rendering(analyzed_window):
    """Verify that MplPlotWidget renders 2D transverse plot when End Diaphragms or Cross Bracings is selected."""
    dock = analyzed_window.output_dock
    plots = analyzed_window.plots_widget
    combo_type = dock._w(KEY_ANALYSIS_MEMBER_TYPE)
    combo_member = dock._w(KEY_ANALYSIS_MEMBER)

    # Switch to End Diaphragms
    combo_type.setCurrentText("End Diaphragms")
    combo_member.setCurrentText("End Diaphragm 1 (Start)")
    plots.update_plot()

    assert plots._fig is not None
    ax = plots._fig.axes[0]
    assert not isinstance(ax, Axes3D), "End Diaphragm plot must render in 2D"
    assert not plots._navcube.isVisible(), "NavCube must be hidden for 2D plots"

    # Switch to Cross Bracings
    combo_type.setCurrentText("Cross Bracings")
    plots.update_plot()
    assert plots._fig is not None
    ax = plots._fig.axes[0]
    assert not isinstance(ax, Axes3D), "Cross Bracing plot must render in 2D"

def test_longitudinal_plots_regression_free(analyzed_window):
    """Verify that Longitudinal member 3D plots continue to render correctly without regression."""
    dock = analyzed_window.output_dock
    plots = analyzed_window.plots_widget
    combo_type = dock._w(KEY_ANALYSIS_MEMBER_TYPE)
    combo_member = dock._w(KEY_ANALYSIS_MEMBER)

    # Switch back to Longitudinal Members
    combo_type.setCurrentText("Longitudinal Members")
    combo_member.setCurrentText("All")
    plots.update_plot()

    assert plots._fig is not None
    ax = plots._fig.axes[0]
    assert isinstance(ax, Axes3D), "Longitudinal girder plot must render in 3D"
