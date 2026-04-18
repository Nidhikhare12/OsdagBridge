"""
Output dock widget for Highway Bridge Design GUI.

Task-2 changes (FOSSEE screening task):
  - Load Combination dropdown now drives the PlotWidget loadcase.
  - Force checkboxes (Fx/Fy/Fz/Mx/My/Mz mapped as Fx/Vy/Vz/Tx/My/Mz)
    replace the Force dropdown in the plot toolbar.
  - Max / Min checkboxes in Display Options are linked to the plot.
  - All linkage is done via plot_signals (no direct import of PlotWidget).
  - Removed unused Steel Design / Deck Design "Here" buttons.
  - Fixed force checkbox grid to include all 6 forces (Fx, Vy, Vz, Tx, My, Mz).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy,
    QPushButton, QGroupBox, QCheckBox, QScrollArea, QFrame,
    QComboBox, QGridLayout,
)
from PySide6.QtCore import Qt, QSize, Slot
from PySide6.QtGui import QIcon

from osdagbridge.core.utils.common import (
    TYPE_TITLE, TYPE_BUTTON, TYPE_COMBOBOX,
    TYPE_CHECKBOX, TYPE_CHECKBOX_ROW, TYPE_CHECKBOX_GRID,
)
from osdagbridge.desktop.ui.utils.custom_buttons import DockCustomButton
from osdagbridge.desktop.ui.docks.dock_utils import apply_field_style
from osdagbridge.desktop.ui.utils.combobox_utils import RichCheckBox

# Import the shared signal hub from plot_UI
try:
    from osdagbridge.desktop.ui.plots_UI import plot_signals, FORCE_MAP
except ImportError:
    plot_signals = None
    FORCE_MAP = {
        "Fx": ("Vx_i", "Vx_j"),
        "Fy": ("Vy_i", "Vy_j"),
        "Fz": ("Vz_i", "Vz_j"),
        "Mx": ("Mx_i", "Mx_j"),
        "My": ("My_i", "My_j"),
        "Mz": ("Mz_i", "Mz_j"),
    }

  


# ── Styles ─────────────────────────────────────────────────────────────────────
GROUPBOX_STYLE = (
    "QGroupBox { border:1px solid #90AF13; border-radius:4px; background-color:white;"
    "  padding:8px; margin-top:12px; font-size:10px; font-weight:bold; color:#333; }"
    "QGroupBox::title { subcontrol-origin:margin; subcontrol-position:top left;"
    "  left:8px; padding:0 4px; margin-top:4px; background-color:white; color:#333; }"
)
SUBGROUP_STYLE = (
    "QGroupBox { border:1px solid #90AF13; border-radius:4px; background-color:white;"
    "  padding:6px; margin-top:10px; font-size:10px; font-weight:bold; color:#333; }"
    "QGroupBox::title { subcontrol-origin:margin; subcontrol-position:top left;"
    "  left:8px; padding:0 4px; margin-top:4px; background-color:white; color:#333; }"
)
ACTION_BTN_STYLE = (
    "QPushButton { background-color:#90AF13; color:white; font-weight:bold; border:none;"
    "  border-radius:4px; padding:8px 20px; font-size:11px; min-width:80px; }"
    "QPushButton:hover { background-color:#7a9a12; }"
    "QPushButton:disabled { background:#D0D0D0; color:#666; }"
)
LABEL_STYLE       = "QLabel { color:#000; font-size:12px; background:transparent; }"
SMALL_LABEL_STYLE = "QLabel { color:#333; font-size:10px; font-weight:normal; background:transparent; }"

# Force label → FORCE_MAP key mapping (Task-2 spec)
# UI label  →  internal FORCE_MAP key
FORCE_LABEL_TO_KEY = {
    "Fx": "Fx",
    "Vy": "Fy",   # Fy in model = Vy in UI
    "Vz": "Fz",   # Fz in model = Vz in UI
    "Tx": "Mx",   # Mx in model = Tx in UI
    "My": "My",
    "Mz": "Mz",
}


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()


# ── OutputDock ─────────────────────────────────────────────────────────────────
class OutputDock(QWidget):
    """
    Output dock widget.
    Task-2: Load Combination, Force checkboxes, Max/Min, and Hide Axis are now
    linked to the PlotWidget via plot_signals.
    """

    def __init__(self, backend=None, parent=None):
        super().__init__()
        self.parent  = parent
        self.backend = backend
        self.setStyleSheet("background: transparent;")

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setMinimumWidth(320)

        self._build_toggle_strip()

        content_container = QWidget()
        content_container.setStyleSheet("background-color: white;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)

        content_layout.addLayout(self._build_top_bar())
        content_layout.addWidget(self._build_scroll_area())
        content_layout.addLayout(self._build_bottom_buttons())

        self.main_layout.addWidget(content_container)

        # Wire up plot_signals
        if plot_signals is not None:
            plot_signals.loadcases_ready.connect(self._on_loadcases_ready)

    # ── Toggle strip ──────────────────────────────────────────────────────────
    def _build_toggle_strip(self):
        self.toggle_strip = QWidget()
        self.toggle_strip.setStyleSheet("background-color: #90AF13;")
        self.toggle_strip.setFixedWidth(6)
        sl = QVBoxLayout(self.toggle_strip)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        sl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.toggle_btn = QPushButton("❯")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(6, 60)
        self.toggle_btn.setToolTip("Hide panel")
        self.toggle_btn.clicked.connect(self.toggle_output_dock)
        self.toggle_btn.setStyleSheet("""
            QPushButton       { background-color:#6c8408; color:white; font-size:12px;
                                font-weight:bold; padding:0px; border:none; }
            QPushButton:hover { background-color:#5e7407; }
        """)
        sl.addStretch()
        sl.addWidget(self.toggle_btn)
        sl.addStretch()
        self.main_layout.addWidget(self.toggle_strip)

    # ── Top bar ───────────────────────────────────────────────────────────────
    def _build_top_bar(self) -> QHBoxLayout:
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        top_bar.setContentsMargins(0, 0, 0, 15)

        title_btn = QPushButton("Output Dock")
        title_btn.setStyleSheet("""
            QPushButton { background-color:#90AF13; color:white; font-weight:bold;
                          font-size:13px; border:none; border-radius:4px; padding:7px 20px; }
        """)
        title_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        top_bar.addWidget(title_btn)
        top_bar.addStretch()
        return top_bar

    # ── Scroll area ───────────────────────────────────────────────────────────
    def _build_scroll_area(self) -> QScrollArea:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background:transparent; padding:0px 5px;
                          border-top:1px solid #909090; border-bottom:1px solid #909090; }
            QScrollArea QScrollBar:vertical { border:none; background:#f0f0f0; width:8px; }
            QScrollArea QScrollBar::handle:vertical { background:#c0c0c0; border-radius:4px; min-height:20px; }
            QScrollArea QScrollBar::handle:vertical:hover { background:#a0a0a0; }
            QScrollArea QScrollBar::add-line:vertical,
            QScrollArea QScrollBar::sub-line:vertical { border:none; background:none; }
        """)

        self.output_widget = QWidget()
        root_layout = QVBoxLayout(self.output_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(12)

        # ── Task-2: Analysis Results section ──────────────────────────────
        self._build_analysis_results_section(root_layout)

        # ── Original schema-driven fields (design sections only) ──────────
        self._build_field_loop(root_layout)

        root_layout.addStretch()
        self.scroll_area.setWidget(self.output_widget)
        return self.scroll_area

    # ── Task-2: Analysis Results section ──────────────────────────────────────
    def _build_analysis_results_section(self, parent_layout: QVBoxLayout):
        """
        Builds the Analysis Results group with:
          - Member dropdown
          - Load Combination dropdown  → drives PlotWidget loadcase
          - Force checkboxes (Fx, Vy, Vz, Tx, My, Mz) → drives PlotWidget force
          - Display Options: Max / Min / Hide Axis checkboxes
        """
        group = QGroupBox("Analysis Results")
        group.setStyleSheet(GROUPBOX_STYLE)
        g_layout = QVBoxLayout()
        g_layout.setContentsMargins(8, 8, 8, 8)
        g_layout.setSpacing(8)

        # ── Member row ─────────────────────────────────────────────────────
        member_row = QHBoxLayout()
        member_lbl = QLabel("Member:")
        member_lbl.setStyleSheet(LABEL_STYLE)
        member_lbl.setMinimumWidth(110)
        member_row.addWidget(member_lbl)
        self.member_combo = NoScrollComboBox()
        self.member_combo.addItem("All")
        apply_field_style(self.member_combo)
        member_row.addWidget(self.member_combo, 1)
        g_layout.addLayout(member_row)

        # ── Load Combination row ───────────────────────────────────────────
        lc_row = QHBoxLayout()
        lc_lbl = QLabel("Load Combination:")
        lc_lbl.setStyleSheet(LABEL_STYLE)
        lc_lbl.setMinimumWidth(110)
        lc_row.addWidget(lc_lbl)
        self.load_combo = NoScrollComboBox()
        self.load_combo.setObjectName("load_combination")
        self.load_combo.addItem("Envelope")
        self.load_combo.setToolTip("Select load combination to display in plot")
        apply_field_style(self.load_combo)
        self.load_combo.currentTextChanged.connect(self._on_load_combination_changed)
        lc_row.addWidget(self.load_combo, 1)
        g_layout.addLayout(lc_row)

        # ── Force / Moment checkboxes ──────────────────────────────────────
        # Grid layout: 2 cols × 3 rows
        #   Col 0  |  Col 1
        #   Fx     |  Tx
        #   Vy     |  My
        #   Vz     |  Mz
        #
        # Each maps to a FORCE_MAP key via FORCE_LABEL_TO_KEY.
        # Behaves like a radio group (only one active at a time).
        force_group = QGroupBox("Force / Moment")
        force_group.setStyleSheet(SUBGROUP_STYLE)
        force_group.setToolTip("Select the force/moment component to display in the plot")
        fg_layout = QGridLayout()
        fg_layout.setContentsMargins(4, 4, 4, 4)
        fg_layout.setHorizontalSpacing(40)
        fg_layout.setVerticalSpacing(6)

        # (label, row, col)  — all 6 components present
        force_labels = [
            ("Fx", 0, 0), ("Tx", 0, 1),   # Tx → Mx
            ("Vy", 1, 0), ("My", 1, 1),
            ("Vz", 2, 0), ("Mz", 2, 1),
        ]
        self._force_checkboxes: dict[str, QCheckBox] = {}
        for label, row, col in force_labels:
            cb = QCheckBox(label)
            cb.setStyleSheet("QCheckBox { font-size:11px; }")
            cb.setToolTip(f"Show {label} ({FORCE_LABEL_TO_KEY.get(label, label)}) diagram")
            cb.clicked.connect(self._on_force_checkbox_clicked)
            fg_layout.addWidget(cb, row, col, Qt.AlignLeft)    
            self._force_checkboxes[label] = cb

        # Default: Vy checked (matches original Fy default)
        self._force_checkboxes["Vy"].setChecked(True)

        force_group.setLayout(fg_layout)
        g_layout.addWidget(force_group)

        # ── Display Options ────────────────────────────────────────────────
        disp_group = QGroupBox("Display Options")
        disp_group.setStyleSheet(SUBGROUP_STYLE)
        dg_layout = QVBoxLayout()
        dg_layout.setContentsMargins(4, 4, 4, 4)
        dg_layout.setSpacing(6)

        # Max / Min row
        maxmin_row = QHBoxLayout()
        self.max_cb = QCheckBox("Max")
        self.max_cb.setToolTip("Highlight maximum value points on the diagram")
        self.min_cb = QCheckBox("Min")
        self.min_cb.setToolTip("Highlight minimum value points on the diagram")
        self.max_cb.stateChanged.connect(self._on_max_changed)
        self.min_cb.stateChanged.connect(self._on_min_changed)
        maxmin_row.addWidget(self.max_cb)
        maxmin_row.addWidget(self.min_cb)
        maxmin_row.addStretch()
        dg_layout.addLayout(maxmin_row)


        # Controlling Utilization Ratio (existing)
        ctrl_ratio_cb = QCheckBox("Controlling Utilization Ratio")
        ctrl_ratio_cb.setStyleSheet("QCheckBox { font-size:11px; }")
        dg_layout.addWidget(ctrl_ratio_cb)

        disp_group.setLayout(dg_layout)
        g_layout.addWidget(disp_group)

        group.setLayout(g_layout)
        parent_layout.addWidget(group)

    # ── Task-2: signal handlers ───────────────────────────────────────────────
    def _on_load_combination_changed(self, text: str):
        """Load Combination changed → tell PlotWidget to update."""
        if plot_signals is not None:
            plot_signals.loadcase_changed.emit(text)

    def _on_force_checkbox_clicked(self):
        """
        Force checkbox clicked → enforce radio behaviour (only one active),
        then emit the corresponding FORCE_MAP key to PlotWidget.
        """
        sender = self.sender()
        if not isinstance(sender, QCheckBox):
            return

        if sender.isChecked():
            # Uncheck all others
            for label, cb in self._force_checkboxes.items():
                if cb is not sender:
                    cb.setChecked(False)
            # Emit the internal FORCE_MAP key
            force_key = FORCE_LABEL_TO_KEY.get(sender.text(), sender.text())
            if plot_signals is not None:
                plot_signals.force_changed.emit(force_key)
        else:
            # Prevent unchecking the last active checkbox (always keep one ticked)
            sender.setChecked(True)

    def _on_max_changed(self, state: int):
        if plot_signals is not None:
            plot_signals.max_toggled.emit(state == Qt.Checked)

    def _on_min_changed(self, state: int):
        if plot_signals is not None:
            plot_signals.min_toggled.emit(state == Qt.Checked)

    def _on_hide_axis_changed(self, state: int):
        """Hide Axis toggled → tell PlotWidget via shared signal."""
        if plot_signals is not None:
            # True = hide axes (show_axis = False)
            plot_signals.axis_toggled.emit(state != Qt.Checked)

    @Slot(list)
    def _on_loadcases_ready(self, loadcases: list):
        """PlotWidget finished setup → populate Load Combination dropdown."""
        self.load_combo.blockSignals(True)
        self.load_combo.clear()
        self.load_combo.addItems(loadcases)
        self.load_combo.blockSignals(False)

    # ── Bottom buttons ────────────────────────────────────────────────────────
    def _build_bottom_buttons(self) -> QHBoxLayout:
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)
        btn_layout.setSpacing(10)

        results_btn = DockCustomButton("Generate Results Table", ":/vectors/design_report.svg")
        results_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_layout.addWidget(results_btn)

        report_btn = DockCustomButton("Generate Report", ":/vectors/design_report.svg")
        report_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn_layout.addWidget(report_btn)

        return btn_layout

    # ── Schema-driven field loop (design sections only) ───────────────────────
    def _build_field_loop(self, root_layout: QVBoxLayout):
        """
        Builds schema-driven design sections from output_values().
        Analysis Results are built by _build_analysis_results_section().
        TYPE_BUTTON entries are skipped (Steel Design / Deck Design buttons
        are no longer needed here).
        Sections whose meta kind == 'analysis' are skipped entirely.
        """
        field_list = []
        if self.backend and hasattr(self.backend, "output_values"):
            try:
                field_list = self.backend.output_values() or []
            except Exception:
                pass

        track        = False
        group        = None
        glayout      = None
        subgroup     = None
        sub_layout   = None
        skip_section = False

        def close_group():
            nonlocal track, group, glayout, subgroup, sub_layout
            if track and group:
                group.setLayout(glayout)
                track = False
            subgroup   = None
            sub_layout = None

        for defn in field_list:
            if len(defn) < 7:
                continue
            key, label, ftype, values, is_visible, _, meta = defn
            meta = meta or {}

            if not is_visible:
                continue

            if ftype == TYPE_TITLE:
                close_group()
                kind = meta.get("kind", "design")
                # Skip analysis section — built manually above
                if kind == "analysis":
                    skip_section = True
                    continue
                skip_section = False
                group, glayout = self._open_group(label, kind)
                root_layout.addWidget(group)
                track = True
                continue

            if not track or skip_section:
                continue

            # ── Skip TYPE_BUTTON entries (Steel Design / Deck Design) ──────
            if ftype == TYPE_BUTTON:
                continue

            if meta.get("group_title"):
                subgroup   = QGroupBox(meta["group_title"])
                subgroup.setStyleSheet(SUBGROUP_STYLE)
                sub_layout = QVBoxLayout()
                sub_layout.setContentsMargins(8, 8, 8, 8)
                sub_layout.setSpacing(6)
                subgroup.setLayout(sub_layout)
                glayout.addWidget(subgroup)

            target = sub_layout if subgroup is not None else glayout

            if ftype == TYPE_COMBOBOX:
                target.addLayout(self._make_combobox_row(key, label, values, meta))
            elif ftype == TYPE_CHECKBOX_GRID:
                target.addLayout(self._make_checkbox_grid(key, label, values, meta))
            elif ftype == TYPE_CHECKBOX_ROW:
                target.addLayout(self._make_checkbox_row(key, label, values, meta))
            elif ftype == TYPE_CHECKBOX:
                cb = QCheckBox(label or "")
                cb.setObjectName(key)
                target.addWidget(cb)

            if meta.get("group_end"):
                subgroup   = None
                sub_layout = None

        close_group()

    # ── Group factories ───────────────────────────────────────────────────────
    def _open_group(self, title, kind):
        if kind == "analysis":
            return self._make_analysis_shell(title)
        return self._make_design_shell(title)

    def _make_analysis_shell(self, title):
        group = QGroupBox(title)
        group.setStyleSheet(GROUPBOX_STYLE)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        return group, layout

    def _make_design_shell(self, title):
        outer = QGroupBox()
        outer.setStyleSheet(
            "QGroupBox { border:1px solid #90AF13; border-radius:5px;"
            " margin-top:0px; padding-top:5px; background-color:white; }"
        )
        ol = QVBoxLayout()
        ol.setContentsMargins(10, 10, 10, 10)
        ol.setSpacing(10)

        header = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size:13px; font-weight:bold; color:#333;")
        header.addWidget(title_lbl)
        header.addStretch()

        toggle = QPushButton()
        toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle.setCheckable(True)
        toggle.setChecked(True)
        toggle.setIcon(QIcon(":/vectors/arrow_up_light.svg"))
        toggle.setIconSize(QSize(20, 20))
        toggle.setStyleSheet(
            "QPushButton { background:transparent; border:none; padding:2px; }"
            "QPushButton:hover, QPushButton:pressed { background:transparent; }"
        )
        header.addWidget(toggle)
        ol.addLayout(header)

        body = QFrame()
        body.setFrameShape(QFrame.NoFrame)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)
        ol.addWidget(body)

        toggle.toggled.connect(lambda checked: (
            body.setVisible(checked),
            toggle.setIcon(QIcon(
                ":/vectors/arrow_up_light.svg" if checked
                else ":/vectors/arrow_down_light.svg"
            )),
        ))

        outer.setLayout(ol)
        return outer, body_layout

    # ── Widget factories ──────────────────────────────────────────────────────
    def _make_combobox_row(self, key, label, values, meta):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        lbl = QLabel(label)
        lbl.setStyleSheet(LABEL_STYLE)
        lbl.setMinimumWidth(110)
        row.addWidget(lbl)
        combo = NoScrollComboBox()
        combo.setObjectName(key)
        items = list(values or [])
        combo.addItems(items)
        default = meta.get("default")
        if default and str(default) in items:
            combo.setCurrentText(str(default))
        apply_field_style(combo)
        row.addWidget(combo, 1)
        return row

    def _make_checkbox_grid(self, key, label, values, meta):
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)
        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet(LABEL_STYLE)
            outer.addWidget(lbl)
        columns  = values if isinstance(values, list) else []
        all_cbs  = []
        num_cols = len(columns)
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        for c in range(num_cols):
            grid.setColumnStretch(c, 1)
        num_rows = max((len(col) for col in columns), default=0)
        for row in range(num_rows):
            for col, col_items in enumerate(columns):
                if row < len(col_items):
                    cb = RichCheckBox(str(col_items[row]))
                    all_cbs.append(cb)
                    grid.addWidget(cb, row, col, alignment=Qt.AlignCenter)
        outer.addLayout(grid)
        if meta.get("exclusive", False):
            self._wire_exclusive(all_cbs)
        return outer

    def _make_checkbox_row(self, key, label, values, meta):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        if label:
            lbl = QLabel(label)
            lbl.setStyleSheet(LABEL_STYLE)
            lbl.setMinimumWidth(110)
            row.addWidget(lbl)
        options = list(values or [])
        cbs = []
        for text in options:
            cb = QCheckBox(str(text))
            cbs.append(cb)
            row.addWidget(cb)
        row.addStretch()
        if meta.get("exclusive", False):
            self._wire_exclusive(cbs)
        return row

    @staticmethod
    def _wire_exclusive(checkboxes):
        def _on_clicked(checked, clicked_cb):
            if checked:
                for cb in checkboxes:
                    if cb is not clicked_cb:
                        cb.setChecked(False)
        for box in checkboxes:
            box.clicked.connect(lambda checked, b=box: _on_clicked(checked, b))

    def _w(self, key):
        return self.output_widget.findChild(QWidget, key) if self.output_widget else None

    # ── Panel toggle ──────────────────────────────────────────────────────────
    def toggle_output_dock(self):
        if hasattr(self.parent, "toggle_animate"):
            collapsing = self.width() > 0
            self.parent.toggle_animate(show=not collapsing, dock="output")
            self.toggle_btn.setText("❮" if collapsing else "❯")
            self.toggle_btn.setToolTip("Show panel" if collapsing else "Hide panel")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent and hasattr(self.parent, "update_docking_icons"):
            self.parent.update_docking_icons(output_is_active=self.width() > 0)