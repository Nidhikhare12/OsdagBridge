from __future__ import annotations

import re
import sqlite3

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QFrame,
    QSizePolicy, QSizeGrip,
    QGridLayout, QCheckBox, QTextEdit,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.docks.output_dock import NoScrollComboBox
from osdagbridge.desktop.ui.widgets.placeholder_section_preview import PlaceholderSectionPreviewWidget
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import (
    TRANSVERSE_MEMBER_DESIGN_SCHEMA,
)
from osdagbridge.core.utils.common import (
    KEY_TD_MEMBER_ID,
    KEY_TD_SELECT_GIRDER,
    KEY_TD_LOAD_COMBINATION,
    KEY_TD_CB_SECTION_INPUTS_BRACING_TYPE,
    KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_ENABLED,
    KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_ENABLED,
    KEY_TD_CB_SECTION_INPUTS_SPACING,
    KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_DESIGNATION,
    KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION,
    KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION,
    KEY_TD_CB_SECTION_INPUTS_DESIGN,
    KEY_TD_CB_SECTION_INPUTS_NO_OF_CB,
    KEY_TD_CB_SECTION_INPUTS_CONNECTION_TYPE,
    KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_TYPE,
    KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE,
    KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE,
    KEY_TD_ED_SECTION_INPUTS_TYPE,
    KEY_TD_ED_SECTION_INPUTS_DESIGN,
    KEY_TD_ED_SECTION_INPUTS_NO_OF_CB,
    KEY_TD_ED_SECTION_INPUTS_BRACING_TYPE,
    KEY_TD_ED_SECTION_INPUTS_CONNECTION_TYPE,
    KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_TYPE,
    KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_DESIGNATION,
    KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_ENABLED,
    KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE,
    KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION,
    KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_ENABLED,
    KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE,
    KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION,
    KEY_TD_ED_SECTION_INPUTS_IS_SECTION,
    KEY_TD_ED_SECTION_INPUTS_SYMMETRY,
    KEY_TD_ED_SECTION_INPUTS_TOTAL_DEPTH,
    KEY_TD_ED_SECTION_INPUTS_WEB_THICKNESS,
    KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_WIDTH,
    KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_WIDTH,
    KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_THICKNESS,
    KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_THICKNESS,
    KEY_TD_ED_SECTION_PROPS_BRACING,
    KEY_TD_ED_SECTION_PROPS_TOP_CHORD,
    KEY_TD_ED_SECTION_PROPS_BOTTOM_CHORD,
    KEY_TD_ED_DESIGN_CHECK_RESULTS,
    KEY_TD_ED_BRACING_DIAGRAM,
    KEY_MP_CB_BRACING_CONNECTION,
    KEY_MP_CB_TYPE,
    KEY_MP_CB_BRACING_SECTION_TYPE,
    KEY_MP_CB_BRACING_SECTION_DESIGNATION,
    KEY_MP_CB_TOP_CHORD_SECTION_TYPE,
    KEY_MP_CB_TOP_CHORD_SECTION_DESIG,
    KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_ED_BRACING_CONNECTION,
    KEY_MP_ED_BRACING_SECTION,
    KEY_MP_ED_TOP_CHORD_SECTION_TYPE,
    KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE,
    KEY_MP_ED_IS_SECTION,
    KEY_MP_ED_TYPE,
    KEY_MP_ED_SYMMETRY,
    KEY_MP_ED_TOTAL_DEPTH,
    KEY_MP_ED_WEB_THICKNESS,
    KEY_MP_ED_TOP_FLANGE_WIDTH,
    KEY_MP_ED_TOP_FLANGE_THICKNESS,
    KEY_MP_ED_BOTTOM_FLANGE_WIDTH,
    KEY_MP_ED_BOTTOM_FLANGE_THICKNESS,
    KEY_TD_ED_PROP_L,
    KEY_TS_GIRDER_SPACING,
)

# ── Style constants ───────────────────────────────────────────────────────────

_TAB_STYLE = """
    QTabWidget::pane {
        border: 1px solid #d1d1d1;
        background-color: #ffffff;
        border-radius: 6px;
    }
    QTabBar::tab {
        font-weight: bold;
        font-size: 12px;
        background: #ffffff;
        color: #3a3a3a;
        border: 1px solid #d1d1d1;
        padding: 10px 22px;
    }
    QTabBar::tab:selected {
        background: #90AF13;
        color: #ffffff;
        border: 1px solid #90AF13;
    }
    QTabBar::tab:hover {
        background: #90AF13;
        color: #ffffff;
    }
"""

_CARD_STYLE = (
    "QFrame#controlCard {"
    "  background-color: white;"
    "  border: 1px solid #b0b0b0;"
    "  border-radius: 6px;"
    "}"
    "QFrame#controlCard > QLabel { border: none; background: transparent; }"
)

_COMBO_STYLE = """
    QComboBox {
        padding: 1px 7px;
        border: 1px solid #888;
        border-radius: 5px;
        background-color: white;
        color: black;
        font-size: 11px;
        min-height: 28px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        border-left: 0px;
    }
    QComboBox::down-arrow {
        image: url(:/vectors/arrow_down_light.svg);
        width: 20px;
        height: 20px;
        margin-right: 8px;
    }
    QComboBox QAbstractItemView {
        background-color: white;
        border: 1px solid #888;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 4px 8px;
        min-height: 24px;
        color: black;
        background-color: white;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #90AF13;
        color: white;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: #90AF13;
        color: white;
    }
    QComboBox:disabled {
        color: #333;
        background-color: #f5f5f5;
    }
"""

_INNER_BOX_STYLE = (
    "QFrame { border: 1px solid #cfcfcf; border-radius: 8px; background-color: #ffffff; }"
    "QFrame QLabel { border: none; }"
)


_TITLE_STYLE    = "font-size: 13px; color: #2B2B2B; font-weight: bold; background: transparent; border: none;"
_HEADING_STYLE  = "font-size: 12px; font-weight: 700; color: #4b4b4b; border: none;"
_LABEL_STYLE    = "font-size: 11px; font-weight: 400; color: #4b4b4b; border: none;"
_SUBHEAD_STYLE  = "font-size: 11px; font-weight: 600; color: #4b4b4b; border: none;"
_PROP_LBL_STYLE = "font-size: 10px; color: #555; border: none; background: transparent;"

_SECTION_TYPE_MAP = {
    "Double Angles":  "double_angle_long",
    "Double Angle (Long Leg)": "double_angle_long",
    "Double Angle (Short Leg)": "double_angle_short",
    "Angle":          "angle",
    "Channel":        "channel",
    "Double Channel": "double_channel",
    "":               "double_angle_long",
}

# ── Schema reference ──────────────────────────────────────────────────────────
_SCHEMA = TRANSVERSE_MEMBER_DESIGN_SCHEMA


class TransverseMemberDesign(QDialog):
    """Schema-driven Transverse Member Design dialog."""

    # Load Combination dropdown shows only these categories — accidental/quasi-
    # permanent and other intermediate combos are hidden to keep the list short.
    _LC_PREFIXES = ("BASIC", "SEISMIC", "SLS_RARE", "SLS_FREQUENT")
    _LC_EXACT    = ("ENVELOPE ULS", "ENVELOPE SLS")

    @classmethod
    def _is_displayable_lc(cls, lc: str) -> bool:
        head = lc.split(":", 1)[0].strip().upper()
        return head in cls._LC_EXACT or head.startswith(cls._LC_PREFIXES)

    def __init__(self, parent=None):
        super().__init__(None)
        self._main_window = parent
        self.setObjectName("TransverseMemberDesign")

        win = _SCHEMA.get("window", {})
        self.resize(win.get("width", 1100), win.get("height", 720))
        self.setMinimumSize(win.get("min_width", 950), win.get("min_height", 550))

        self._forces_dict:      dict          = {}
        self._designs_dict:     dict          = {}
        self._cb_designs_dict:  dict          = {}
        self._ed_designs_dict:  dict          = {}
        self._pair_keys:        list[str]     = []
        self._members_per_pair: dict[str, int] = {}
        self._ed_group_widgets: dict[str, list[QWidget]] = {"crossbracing": [], "welded_beam": [], "rolled_beam": []}
        self._backend: object = None
        self._cb_forces_df = None   # full compute_panel_forces() DataFrame for per-LC queries


        # All schema-driven widgets keyed by their schema "id"
        self._widgets: dict[str, QWidget] = {}
        # Per-tab bracing layout and result widgets (avoids collision between CB and ED tabs)
        self._tab_bracing_widgets: dict = {"cb": None, "ed": None}
        self._tab_result_texts: dict = {"cb": None, "ed": None}
        self._ed_type_combo = None

        # Section property fields and previews keyed by card title
        self._prop_fields:      dict[str, dict[str, QLineEdit]]            = {}
        self._section_previews: dict[str, PlaceholderSectionPreviewWidget] = {}

        self.init_ui()
        self.setStyleSheet(
            "QDialog { background-color: #ffffff; border: 1px solid #90AF13; }"
        )
        self._try_load_data()

    # Convenience accessors for schema-driven widgets

    def _w(self, schema_id: str) -> QWidget | None:
        """Return the widget registered under *schema_id*, or None."""
        return self._widgets.get(schema_id)

    # Window chrome

    def setupWrapper(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window)

        root = QVBoxLayout(self)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle(_SCHEMA.get("title", "Transverse Member Design"))
        root.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        root.addWidget(self.content_widget, 1)

        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(grip, 0, Qt.AlignBottom | Qt.AlignRight)
        root.addLayout(overlay)

    def init_ui(self):
        self.setupWrapper()

        main = QVBoxLayout(self.content_widget)
        main.setContentsMargins(5, 5, 5, 5)
        main.setSpacing(6)
        main.addWidget(self._build_global_bar())

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(_TAB_STYLE)

        details_schema = _SCHEMA.get("crossbracing_tab", {})
        self.tabs.addTab(
            self._build_crossbracing_tab(details_schema),
            "Crossbracing",
        )
        ed_schema = _SCHEMA.get("end_diaphragm_tab", {})
        self.tabs.addTab(
            self._build_end_diaphragm_tab(ed_schema),
            "End Diaphragm",
        )

        self.tabs.currentChanged.connect(self._on_tab_changed)
        main.addWidget(self.tabs)

    def _build_global_bar(self) -> QWidget:
        """Build the top control bar from ``schema["global_bar"]``."""
        bar_schema = _SCHEMA.get("global_bar", [])

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 6)
        row.setSpacing(16)

        for field_def in bar_schema:
            fid   = field_def["id"]
            title = field_def.get("label", "")

            card = QFrame()
            card.setObjectName("controlCard")
            card.setStyleSheet(_CARD_STYLE)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(23, 10, 14, 12)
            cl.setSpacing(4)

            lbl = QLabel(title)
            lbl.setStyleSheet(_TITLE_STYLE)
            cl.addWidget(lbl)

            combo = NoScrollComboBox()
            combo.setObjectName(fid)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.setFixedHeight(28)
            combo.setStyleSheet(_COMBO_STYLE)

            # Seed default items
            default = field_def.get("default")
            if default:
                combo.addItem(str(default))

            cl.addWidget(combo)
            self._widgets[fid] = combo
            row.addWidget(card, 1)

        # Wire Select Girder change signal
        girder_combo = self._widgets.get(KEY_TD_SELECT_GIRDER)
        if girder_combo is not None:
            girder_combo.currentTextChanged.connect(self._on_girder_pair_changed)

        # Wire Load Combination change signal
        lc_combo = self._widgets.get(KEY_TD_LOAD_COMBINATION)
        if lc_combo is not None:
            lc_combo.currentTextChanged.connect(self._on_load_combination_changed)

        return container

    # Crossbracing tab
    def _build_crossbracing_tab(self, schema: dict) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = StyledScrollArea()
        content = QWidget()
        content.setStyleSheet("background-color: white;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(12)

        # 2D Bracing Diagram - full width at top with left/right margins
        diag_schema = schema.get("right_panel", {}).get("bracing_diagram", {})
        diagram_box = self._build_bracing_diagram_box(diag_schema)
        self._tab_bracing_widgets["cb"] = self.bracing_layout_widget  # store here
        diagram_box.setContentsMargins(20, 10, 20, 10)  # Left/right margins for diagram
        cl.addWidget(diagram_box)

        # Middle section: Section inputs (left) + Section cards (right)
        middle_part = QWidget()
        middle_layout = QHBoxLayout(middle_part)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(12)
        middle_layout.addWidget(self._build_left_panel(schema.get("left_panel", {})), 0)
        # Build right panel without diagram (only section cards)
        middle_layout.addWidget(self._build_section_cards_panel(schema.get("right_panel", {})), 1)
        cl.addWidget(middle_part)

        # Results table at bottom
        dc_schema = _SCHEMA.get("crossbracing_tab", {})
        rt_schema = dc_schema.get("results_table", {})
        result_card, cb_text = self._build_result_text_card(rt_schema)
        self.design_check_text = cb_text          # keep for backward compat
        self._tab_result_texts["cb"] = cb_text
        cl.addWidget(result_card)
        cl.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return tab

    # End Diaphragm tab 
    def _build_end_diaphragm_tab(self, schema: dict) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet("background-color: white;")
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        scroll = StyledScrollArea()
        content = QWidget()
        content.setStyleSheet("background-color: white;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(10, 10, 10, 10)
        cl.setSpacing(12)

        # ── Diagram (same as CB) ──────────────────────────────────────────────
        diag_schema = schema.get("right_panel", {}).get("bracing_diagram", {})
        diagram_box = self._build_bracing_diagram_box(diag_schema)
        self._tab_bracing_widgets["ed"] = self.bracing_layout_widget
        diagram_box.setContentsMargins(20, 10, 20, 10)
        cl.addWidget(diagram_box)

        # ── Middle: left inputs + stacked right panel ─────────────────────────
        middle_part = QWidget()
        middle_layout = QHBoxLayout(middle_part)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(12)

        middle_layout.addWidget(
            self._build_section_inputs_box(
                schema.get("left_panel", {}).get("section_inputs", {})
            ), 0
        )

        # Right: two variants stacked, show/hide via _on_ed_type_changed
        self._ed_right_stack = QWidget()
        self._ed_right_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        stack_layout = QVBoxLayout(self._ed_right_stack)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(0)

        self._ed_cards_cb = self._build_section_cards_panel(schema.get("right_panel", {}), key_prefix="ed_")
        stack_layout.addWidget(self._ed_cards_cb)

        self._ed_cards_wb = self._build_welded_beam_card()
        stack_layout.addWidget(self._ed_cards_wb)

        middle_layout.addWidget(self._ed_right_stack, 1)
        cl.addWidget(middle_part)

        # ── Results ───────────────────────────────────────────────────────────
        rt_schema = schema.get("results_table", {})
        result_card, ed_text = self._build_result_text_card(rt_schema)
        self._tab_result_texts["ed"] = ed_text
        cl.addWidget(result_card)
        cl.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        # Set initial state — crossbracing visible, welded beam hidden
        self._on_ed_type_changed("Cross Bracing")
        return tab

    # Left panel

    def _build_left_panel(self, schema: dict) -> QWidget:
        panel = QWidget()
        panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        si = schema.get("section_inputs", {})
        layout.addWidget(self._build_section_inputs_box(si))
        return panel

    def _build_section_inputs_box(self, schema: dict) -> QFrame:
        """Build section inputs from ``schema["fields"]`` list."""
        box = self._inner_box()
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vl = QVBoxLayout(box)
        vl.setContentsMargins(10, 10, 10, 10)
        vl.setSpacing(6)

        heading_text = schema.get("label", "Section Inputs:")
        vl.addWidget(self._heading(heading_text))

        label_width = schema.get("label_width")
        fields = schema.get("fields", [])

        box.setMaximumWidth(350)

        grid = QGridLayout()
        grid.setContentsMargins(0, 2, 0, 2)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        grid.setColumnMinimumWidth(0, label_width)
        grid.setColumnStretch(1, 1)
        row = 0

        for field_def in fields:
            fid    = field_def["id"]
            ftype  = field_def.get("type", "line")
            flabel = field_def.get("label", "")

            if ftype == "checkbox":
                hdr_widget = QWidget()
                hdr_widget.setStyleSheet("background: transparent;")
                hdr = QHBoxLayout(hdr_widget)
                hdr.setContentsMargins(0, 4, 0, 0)
                hdr.setSpacing(6)
                hdr.addWidget(self._subhead(flabel))
                cb = QCheckBox()
                cb.setObjectName(fid)
                cb.setEnabled(field_def.get("enabled", True))
                cb.setChecked(field_def.get("default", False))
                hdr.addWidget(cb)
                hdr.addStretch()
                grid.addWidget(hdr_widget, row, 0, 1, 2)   # ← addWidget not addLayout
                self._widgets[fid] = cb
                group = field_def.get("group")
                if group is not None:
                    self._ed_group_widgets.setdefault(group, []).append(hdr_widget)
                row += 1

            elif ftype == "combo":
                widget = self._ro_combo(field_def.get("choices", []))
                widget.setObjectName(fid)
                callback_name = field_def.get("on_change")
                if callback_name:
                    cb_func = getattr(self, callback_name, None)
                    if callable(cb_func):
                        widget.currentTextChanged.connect(cb_func)
                row, lbl_widget = self._grid_row(grid, row, flabel, widget)
                group = field_def.get("group")
                if group is not None:
                    self._ed_group_widgets.setdefault(group, []).extend([lbl_widget, widget])
                self._widgets[fid] = widget

            else:  # "line"
                widget = self._ro_line()
                widget.setObjectName(fid)
                callback_name = field_def.get("on_change")
                if callback_name:
                    cb_func = getattr(self, callback_name, None)
                    if callable(cb_func):
                        widget.textChanged.connect(cb_func)   # textChanged for QLineEdit
                row, lbl_widget = self._grid_row(grid, row, flabel, widget)
                group = field_def.get("group")
                if group is not None:
                    self._ed_group_widgets.setdefault(group, []).extend([lbl_widget, widget])
                self._widgets[fid] = widget

        vl.addLayout(grid)
        vl.addStretch()
        return box

    # ── Right panel (schema-driven diagram + property cards) ──────────────

    def _build_section_cards_panel(self, schema: dict,key_prefix: str = "") -> QWidget:
        panel = QWidget()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        # Section property cards from schema (no diagram)
        for card_def in schema.get("section_cards", []):
            card_title = card_def["title"]
            store_key  = key_prefix + card_title          # ← namespaced key
            col_lists  = [card_def.get("col1", []), card_def.get("col2", []), card_def.get("col3", [])]
            card, fields = self._build_section_property_card(card_title, col_lists, store_key=store_key)
            self._prop_fields[store_key] = fields          # ← use store_key, not card_title
            self._widgets[card_def["id"]] = card
            layout.addWidget(card)
        layout.addStretch()
        return panel

    def _build_bracing_diagram_box(self, schema: dict) -> QFrame:
        box = self._inner_box()
        box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bl = QVBoxLayout(box)
        bl.setContentsMargins(150, 10, 150, 10)
        bl.setSpacing(4)

        diagram_height = schema.get("height")

        try:
            from osdagbridge.desktop.ui.dialogs.additional_input.drawings.bracing_layout_cad import (
                BracingLayoutCadWidget,
            )
            self.bracing_layout_widget = BracingLayoutCadWidget(diagram_height)
            self.bracing_layout_widget.setFixedHeight(diagram_height)
            bl.addWidget(self.bracing_layout_widget)
        except Exception:
            self.bracing_layout_widget = None
            placeholder = QLabel("Bracing Layout Diagram")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setFixedHeight(diagram_height)
            placeholder.setStyleSheet(
                "QLabel { border: 1px dashed #aaa; border-radius: 6px; "
                "color: #888; font-size: 11px; background: #f7f7f7; }"
            )
            bl.addWidget(placeholder)

        fid = schema.get("id")
        if fid:
            self._widgets[fid] = box
        return box
    
    def _build_welded_beam_card(self) -> QFrame:
        """Single full-width card shown when ED type is Welded Beam."""
        card = self._inner_box()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        outer = QHBoxLayout(card)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(16)

        # Left: section preview (I-beam shape)
        lbl = QLabel("End Diaphragm")
        lbl.setStyleSheet(_HEADING_STYLE)
        preview = PlaceholderSectionPreviewWidget(placeholder_text="Welded Beam", min_height=150)
        preview.setFixedWidth(160)
        self._section_previews["ED Welded Beam"] = preview
        left_v = QVBoxLayout()
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(4)
        left_v.addWidget(lbl)
        left_v.addWidget(preview)
        left_v.addStretch()
        outer.addLayout(left_v)

        # Right: property columns
        col1 = ["D (mm)", "B_top (mm)", "tf_top (mm)"]
        col2 = ["tw (mm)", "B_bot (mm)", "tf_bot (mm)"]
        col3 = ["A (cm²)", "Iz (cm⁴)", "M (Kg/m)"]

        props_layout = QHBoxLayout()
        props_layout.setContentsMargins(0, 0, 0, 0)
        props_layout.setSpacing(10)
        fields: dict[str, QLineEdit] = {}

        for col_props in [col1, col2, col3]:
            col = QGridLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setHorizontalSpacing(4)
            col.setVerticalSpacing(3)
            for r, prop in enumerate(col_props):
                lbl_p = QLabel(prop)
                lbl_p.setStyleSheet(_PROP_LBL_STYLE)
                field = QLineEdit()
                field.setReadOnly(True)
                field.setFixedWidth(68)
                field.setFixedHeight(21)
                field.setStyleSheet(
                    "QLineEdit { border:1px solid #d0d0d0; border-radius:3px;"
                    " background:#fafafa; font-size:10px; color:#333; padding:1px 4px; }"
                )
                col.addWidget(lbl_p, r, 0, Qt.AlignLeft | Qt.AlignVCenter)
                col.addWidget(field, r, 1, Qt.AlignLeft | Qt.AlignVCenter)
                fields[prop] = field
            props_layout.addLayout(col)

        self._prop_fields["ED Welded Beam"] = fields
        outer.addLayout(props_layout)
        outer.addStretch()
        return card

    def _build_section_property_card(
        self, title: str, col_lists: list[list[str]],store_key: str | None = None
    ) -> tuple[QFrame, dict[str, QLineEdit]]:
        card = self._inner_box()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(12)

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(_HEADING_STYLE)
        left.addWidget(title_lbl)

        preview = PlaceholderSectionPreviewWidget(placeholder_text=title, min_height=150)
        preview.setFixedWidth(150)
        self._section_previews[store_key if store_key is not None else title] = preview  # ← only change
        left.addWidget(preview)
        left.addStretch()
        card_layout.addLayout(left)

        props_layout = QHBoxLayout()
        props_layout.setContentsMargins(0, 0, 0, 0)
        props_layout.setSpacing(10)

        fields: dict[str, QLineEdit] = {}
        for col_props in col_lists:
            col = QGridLayout()
            col.setContentsMargins(0, 0, 0, 0)
            col.setHorizontalSpacing(4)
            col.setVerticalSpacing(3)
            for r, prop in enumerate(col_props):
                lbl = QLabel(prop)
                lbl.setStyleSheet(_PROP_LBL_STYLE)
                field = QLineEdit()
                field.setReadOnly(True)
                field.setFixedWidth(58)
                field.setFixedHeight(21)
                field.setStyleSheet(
                    "QLineEdit { border: 1px solid #d0d0d0; border-radius: 3px;"
                    " background: #fafafa; font-size: 10px; color: #333;"
                    " padding: 1px 4px; }"
                )
                col.addWidget(lbl,   r, 0, Qt.AlignLeft | Qt.AlignVCenter)
                col.addWidget(field, r, 1, Qt.AlignLeft | Qt.AlignVCenter)
                fields[prop] = field
            props_layout.addLayout(col)

        card_layout.addLayout(props_layout)
        return card, fields


    def _build_result_text_card(self, schema: dict) -> tuple[QFrame, QTextEdit]:
        card = self._inner_box()
        vl = QVBoxLayout(card)
        vl.setContentsMargins(14, 10, 14, 14)
        vl.setSpacing(8)
        vl.addWidget(self._heading(schema.get("title", "Design Check Results:")))

        text_widget = QTextEdit()                    # ← ONE widget only
        text_widget.setReadOnly(True)
        text_widget.setMinimumHeight(schema.get("min_height", 200))
        text_widget.setStyleSheet(
            "QTextEdit { background-color: white; border: none;"
            " font-size: 11px; color: #333333; padding: 0px; }"
        )
        text_widget.setContentsMargins(0, 0, 0, 0)
        text_widget.setViewportMargins(0, 0, 0, 0)
        text_widget.document().setDocumentMargin(0)
        text_widget.setHtml(self._empty_design_check_html())
        vl.addWidget(text_widget)                    # ← add it

        fid = schema.get("id")
        if fid:
            self._widgets[fid] = text_widget         # ← register it

        return card, text_widget

    # ── Shared widget helpers ─────────────────────────────────────────────

    def _inner_box(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(_INNER_BOX_STYLE)
        return frame

    def _sync_design_check_width(self) -> None:
        for text_w in self._tab_result_texts.values():
            if text_w is not None:
                text_w.document().setTextWidth(text_w.viewport().width())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_design_check_width()

    def _lbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(_LABEL_STYLE)
        return lbl

    def _heading(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(_HEADING_STYLE)
        return lbl

    def _subhead(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(_SUBHEAD_STYLE)
        return lbl

    def _ro_line(self) -> QLineEdit:
        field = QLineEdit()
        field.setReadOnly(True)
        field.setFixedHeight(28)
        field.setFixedWidth(150)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _ro_combo(self, items: list[str]) -> NoScrollComboBox:
        combo = NoScrollComboBox()
        combo.addItems(items)
        combo.setEnabled(False)
        combo.setFixedHeight(28)
        combo.setFixedWidth(150)
        combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo.setStyleSheet(_COMBO_STYLE)
        return combo

    def _grid_row(self, grid: QGridLayout, row: int, label: str, widget: QWidget) -> tuple[int, QLabel]:
        lbl = self._subhead(label) if label == "Spacing:" else self._lbl(label)
        grid.addWidget(lbl,    row, 0, Qt.AlignLeft | Qt.AlignVCenter)
        grid.addWidget(widget, row, 1)
        return row + 1, lbl

    # ── Signal handlers ───────────────────────────────────────────────────

    def _on_girder_pair_changed(self, text: str):
        """When girder pair changes, refresh details for the corresponding pair."""
        if text in self._pair_keys:
            pair_idx = self._pair_keys.index(text)
            self._on_pair_selected(pair_idx)

    def _on_pair_selected(self, idx: int):
        """Refresh details and bracing layout for the given pair index."""
        pair_key = self._pair_keys[idx] if 0 <= idx < len(self._pair_keys) else None
        self._refresh_bracing_layout()
        if pair_key:
            self._populate_cb_pair_details(pair_key)
            self._populate_ed_pair_details(pair_key)
            if self._forces_dict:   # forces are enough; designs just add capacity column
                lc_combo = self._widgets.get(KEY_TD_LOAD_COMBINATION)
                current_lc = lc_combo.currentText() if lc_combo else "Envelope"
                forces_for_display = (
                    self._forces_dict if current_lc == "Envelope"
                    else self._get_forces_for_lc(current_lc)
                )
                cb_html = self._build_cb_design_check_html(pair_key, forces_for_display, self._cb_designs_dict)
                if self._tab_result_texts.get("cb"):
                    self._tab_result_texts["cb"].setHtml(cb_html)
                ed_html = self._build_ed_design_check_html(pair_key, forces_for_display, self._ed_designs_dict)
                if self._tab_result_texts.get("ed"):
                    self._tab_result_texts["ed"].setHtml(ed_html)

    def _on_load_combination_changed(self, text: str):
        """Recompute displayed forces when the selected load combination changes."""
        if not self._forces_dict or not self._pair_keys:
            return
        pair_combo = self._widgets.get(KEY_TD_SELECT_GIRDER)
        pair_key = pair_combo.currentText() if pair_combo else ""
        if not pair_key:
            return
        forces_for_display = (
            self._forces_dict if text == "Envelope"
            else self._get_forces_for_lc(text)
        )
        cb_html = self._build_cb_design_check_html(pair_key, forces_for_display, self._cb_designs_dict)
        if self._tab_result_texts.get("cb"):
            self._tab_result_texts["cb"].setHtml(cb_html)
        ed_html = self._build_ed_design_check_html(pair_key, forces_for_display, self._ed_designs_dict)
        if self._tab_result_texts.get("ed"):
            self._tab_result_texts["ed"].setHtml(ed_html)

    def _get_forces_for_lc(self, lc: str) -> dict:
        """Build a forces_dict slice for a single load case from the stored DataFrame."""
        if self._cb_forces_df is None or self._cb_forces_df.empty:
            return self._forces_dict

        df = self._cb_forces_df
        base: dict = {
            "brace_type":   self._forces_dict.get("brace_type"),
            "top_chord":    self._forces_dict.get("top_chord"),
            "bottom_chord": self._forces_dict.get("bottom_chord"),
            "geometry":     self._forces_dict.get("geometry", {}),
            "pairs":        {},
        }
        for pair_key in self._pair_keys:
            mask = (df["LoadCase"] == lc) & (df["Girder Pair"] == pair_key)
            rows = df[mask]
            if rows.empty:
                base["pairs"][pair_key] = {
                    "diag_tension_kN": None, "diag_compression_kN": None,
                    "chord_tension_kN": None, "chord_compression_kN": None,
                }
                continue
            # Worst case over multiple chain stations for this LC
            f_diag_max  = float(rows["F_diag (kN)"].max())
            f_diag_min  = float(rows["F_diag (kN)"].min())
            f_chord_max = float(rows["F_chord (kN)"].max())
            f_chord_min = float(rows["F_chord (kN)"].min())
            _tol = 5e-3
            base["pairs"][pair_key] = {
                "diag_tension_kN":          round(f_diag_max,       3) if f_diag_max  >  _tol else None,
                "diag_compression_kN":      round(abs(f_diag_min),  3) if f_diag_min  < -_tol else None,
                "chord_tension_kN":         round(f_chord_max,      3) if f_chord_max >  _tol else None,
                "chord_compression_kN":     round(abs(f_chord_min), 3) if f_chord_min < -_tol else None,
                "diag_tension_gov_lc":      lc,
                "diag_compression_gov_lc":  lc,
                "chord_tension_gov_lc":     lc,
                "chord_compression_gov_lc": lc,
            }
        return base

    def _on_bracing_type_changed(self, _text: str):
        self._refresh_bracing_layout()

    def _on_ed_type_changed(self, ed_type: str):
        """Toggle End Diaphragm property cards between Cross Bracing and Beam cards."""
        is_beam = ed_type in ("Welded Beam", "Rolled Beam")
        if hasattr(self, "_ed_cards_cb") and self._ed_cards_cb:
            self._ed_cards_cb.setVisible(not is_beam)
        if hasattr(self, "_ed_cards_wb") and self._ed_cards_wb:
            self._ed_cards_wb.setVisible(is_beam)

    def _refresh_bracing_layout(self):
        # NEW
        is_ed_tab = (self.tabs.currentIndex() == 1)

        bracing_w = self._widgets.get(
            KEY_TD_ED_SECTION_INPUTS_BRACING_TYPE if is_ed_tab else KEY_TD_CB_SECTION_INPUTS_BRACING_TYPE
        )
        tc_w = self._widgets.get(
            KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_ENABLED if is_ed_tab else KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_ENABLED
        )
        bc_w = self._widgets.get(
            KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_ENABLED if is_ed_tab else KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_ENABLED
        )

        bracing = bracing_w.text() if (bracing_w and bracing_w.text()) else None
        top     = tc_w.isChecked() if tc_w else True
        bottom  = bc_w.isChecked() if bc_w else True

        active_widget = self._tab_bracing_widgets["ed" if is_ed_tab else "cb"]
        if active_widget is not None:
            active_widget.set_layout(bracing, top, bottom, "", "")

    # ── Data loading ──────────────────────────────────────────────────────

    def _try_load_data(self):
        backend = getattr(self._main_window, "backend", None)
        if backend is None or not getattr(backend, "result_data", None):
            return

        try:
            from osdagbridge.core.bridge_types.plate_girder.crossbracingforces import CrossBracingForces
            cb = CrossBracingForces(bridge=backend)
            self._cb_forces_df = cb.compute_panel_forces()
            forces_dict = cb.get_design_forces_dict()
            if not forces_dict or not forces_dict.get("pairs"):
                return

            all_lcs = [
                str(lc) for lc in backend.result_data.get("loadcases", [])
                if self._is_displayable_lc(str(lc))
            ]

            cb_designs = getattr(backend, "crossbracing_design_results", {}) or {}
            ed_designs = getattr(backend, "end_diaphragm_design_results", {}) or {}
            od         = getattr(backend, "output_dict", {}) or {}

            self._cb_designs_dict = cb_designs or {}
            self._ed_designs_dict = ed_designs or {}

            # Merge ED results into designs_dict and tag ed_type / ed_bracing_type
            designs_dict: dict = dict(cb_designs)
            for pair, ed_pair_data in ed_designs.items():
                pair_id   = pair.replace("-", "")
                ed_type  = ed_pair_data.get("ed_type") or od.get(f"member_properties.end_diaphragm_details.{pair_id}.type") or ""
                ed_btype = od.get(f"member_properties.end_diaphragm_details.{pair_id}.bracing_type") or ""

                if ed_type in ("Rolled Beam", "Welded Beam"):
                    # For Beam types, replace pair dict so it ONLY contains beam-relevant keys and ed_type
                    entry = dict(ed_pair_data)
                    if ed_type:
                        entry["ed_type"] = ed_type
                    designs_dict[pair] = entry
                else:
                    entry = designs_dict.setdefault(pair, {})
                    entry.update(ed_pair_data)
                    if ed_type:
                        entry["ed_type"] = ed_type
                    if ed_btype:
                        entry["ed_bracing_type"] = ed_btype

            self._backend = backend
            members_per_pair = self._compute_members_per_pair(backend, forces_dict)
            self.load_data(forces_dict, designs_dict, members_per_pair, all_lcs=all_lcs)
        except Exception as e:
            import traceback
            print(f"[TransverseMemberDesign] _try_load_data error: {e}")
            traceback.print_exc()

    def _compute_members_per_pair(self, backend, forces_dict: dict) -> dict[str, int]:
        pairs = list(forces_dict.get("pairs", {}).keys())
        if not pairs:
            return {}

        geom       = forces_dict.get("geometry", {})
        cb_spacing = float(geom.get("cb_spacing_m") or 4.0)

        span   = None
        sizing = getattr(backend, "sizing_result", None)
        if sizing is not None:
            span = getattr(sizing, "span", None)
        if span is None:
            span = float(getattr(backend, "basic_inputs", {}).get("span", 30) or 30)

        n = max(1, round(float(span) / cb_spacing) - 1)
        return {p: n for p in pairs}

    def load_data(
        self,
        forces_dict:      dict,
        designs_dict:     dict | None = None,
        members_per_pair: dict | None = None,
        all_lcs:          list[str] | None = None,
    ) -> None:
        if not forces_dict:
            return

        self._forces_dict  = forces_dict
        self._designs_dict = designs_dict or {}

        # --- DEBUG PRINT ---
        print(f"[TransverseMemberDesign] DEBUG: forces_dict: brace_type={self._forces_dict.get('brace_type')}, top_chord={self._forces_dict.get('top_chord')}, bottom_chord={self._forces_dict.get('bottom_chord')}")
        print(f"[TransverseMemberDesign] DEBUG: designs_dict keys: {list(self._designs_dict.keys())}")
        for pair_key, pair_designs in self._designs_dict.items():
            print(f"[TransverseMemberDesign] DEBUG: Pair {pair_key} designs: ed_type={pair_designs.get('ed_type')}, ed_bracing_type={pair_designs.get('ed_bracing_type')}")
            # Print ALL values for debugging to see what's available
            print(f"[TransverseMemberDesign] DEBUG: Pair {pair_key} ALL design values:")
            for key, value in pair_designs.items():
                print(f"[TransverseMemberDesign] DEBUG:   {key} = {value}")
        # --- END DEBUG ---

        geom  = forces_dict.get("geometry", {})
        pairs = forces_dict.get("pairs", {})

        self._pair_keys = list(pairs.keys())

        # Set bracing type
        brace_raw = forces_dict.get("brace_type")
        if brace_raw:
            brace_label = "K-Bracing" if "K" in str(brace_raw).upper() else "X-Bracing"
        else:
            brace_label = ""

        bracing_w = self._widgets.get(KEY_TD_CB_SECTION_INPUTS_BRACING_TYPE)
        if bracing_w:
            bracing_w.setText(brace_label)

        # Set chord checkboxes
        tc_w = self._widgets.get(KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_ENABLED)
        if tc_w:
            tc_w.setChecked(bool(forces_dict.get("top_chord", True)))
        bc_w = self._widgets.get(KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_ENABLED)
        if bc_w:
            bc_w.setChecked(bool(forces_dict.get("bottom_chord", True)))

        # Set spacing
        spacing = geom.get("cb_spacing_m")
        spacing_w = self._widgets.get(KEY_TD_CB_SECTION_INPUTS_SPACING)
        if spacing is not None and spacing_w:
            spacing_w.setText(f"{spacing:.3f} m")

        # members_per_pair tracks how many cross-bracings exist between each girder pair
        self._members_per_pair = members_per_pair or {p: 1 for p in self._pair_keys}

        # Populate Load Combination combo — all LCs from backend, or fall back to governing LCs
        load_combo = self._widgets.get(KEY_TD_LOAD_COMBINATION)
        if load_combo:
            load_combo.blockSignals(True)
            load_combo.clear()
            load_combo.addItem("Envelope")
            if all_lcs:
                for lc in all_lcs:
                    load_combo.addItem(str(lc))
            else:
                lcs: set[str] = set()
                for pdata in pairs.values():
                    for key in (
                        "diag_tension_gov_lc", "diag_compression_gov_lc",
                        "chord_tension_gov_lc", "chord_compression_gov_lc",
                    ):
                        lc_val = pdata.get(key)
                        if lc_val:
                            lcs.add(str(lc_val))
                for lc in sorted(lcs):
                    load_combo.addItem(lc)
            load_combo.blockSignals(False)

        girder_combo = self._widgets.get(KEY_TD_SELECT_GIRDER)
        if girder_combo:
            girder_combo.clear()
            girder_combo.addItems(self._pair_keys)
            girder_combo.setEnabled(bool(self._pair_keys))

        self._refresh_bracing_layout()

        if self._pair_keys:
            self._populate_cb_pair_details(self._pair_keys[0])
            self._populate_ed_pair_details(self._pair_keys[0])

        if self._pair_keys:
            cb_html = self._build_cb_design_check_html(self._pair_keys[0], forces_dict, self._cb_designs_dict)
            if self._tab_result_texts.get("cb"):
                self._tab_result_texts["cb"].setHtml(cb_html)
            ed_html = self._build_ed_design_check_html(self._pair_keys[0], forces_dict, self._ed_designs_dict)
            if self._tab_result_texts.get("ed"):
                self._tab_result_texts["ed"].setHtml(ed_html)

    def _populate_cb_pair_details(self, pair_key: str) -> None:
        # ── Always-visible fields (no design data needed) ────────────────────
        design_w = self._widgets.get(KEY_TD_CB_SECTION_INPUTS_DESIGN)
        if design_w:
            design_w.setText("Cross Bracing")

        no_cb_w = self._widgets.get(KEY_TD_CB_SECTION_INPUTS_NO_OF_CB)
        if no_cb_w:
            no_cb_w.setText(str(self._members_per_pair.get(pair_key, 0)))

        conn_w = self._widgets.get(KEY_TD_CB_SECTION_INPUTS_CONNECTION_TYPE)
        if conn_w:
            idict    = getattr(self._backend, "input_dict", {}) or {}
            pair_id  = pair_key.replace("-", "")
            _pm      = re.match(r"G(\d+)G", pair_id)
            mi_sfx   = f".{pair_id}.B{_pm.group(1)}M1" if _pm else ""
            conn_val = (
                idict.get(f"{KEY_MP_CB_BRACING_CONNECTION}.{pair_id}")
                or idict.get(f"{KEY_MP_CB_BRACING_CONNECTION}{mi_sfx}")
                or idict.get(KEY_MP_CB_BRACING_CONNECTION)
                or "Bolted"
            )
            conn_w.setText(str(conn_val))

        # ── Design-data-dependent fields & fallbacks ────────────────────────
        od           = getattr(self._backend, "output_dict", {}) or {}
        idict        = getattr(self._backend, "input_dict", {}) or {}
        pair_id      = pair_key.replace("-", "")
        _pm          = re.match(r"G(\d+)G", pair_id)
        mi_sfx       = f".{pair_id}.B{_pm.group(1)}M1" if _pm else ""
        pair_designs = self._designs_dict.get(pair_key, {}) if self._designs_dict else {}

        diag_des  = self._get_governing_section(pair_designs, "diagonal") if pair_designs else ""
        chord_des = self._get_governing_section(pair_designs, "chord") if pair_designs else ""

        if not diag_des:
            diag_des = (
                od.get(f"member_properties.cross_bracing_details.{pair_id}.diagonal.section_designation")
                or idict.get(f"{KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_DESIGNATION}.{pair_id}")
                or idict.get(f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}.{pair_id}")
                or idict.get(f"{KEY_MP_CB_BRACING_SECTION_DESIGNATION}{mi_sfx}")
                or idict.get(f"member_properties.cross_bracing_details.{pair_id}.bracing_section_designation")
                or idict.get(KEY_MP_CB_BRACING_SECTION_DESIGNATION)
                or ""
            )
        if not chord_des:
            chord_des = (
                od.get(f"member_properties.cross_bracing_details.{pair_id}.top_chord.section_designation")
                or idict.get(f"{KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION}.{pair_id}")
                or idict.get(f"{KEY_MP_CB_TOP_CHORD_SECTION_DESIG}.{pair_id}")
                or idict.get(f"{KEY_MP_CB_TOP_CHORD_SECTION_DESIG}{mi_sfx}")
                or idict.get(f"member_properties.cross_bracing_details.{pair_id}.top_chord_section_desig")
                or idict.get(KEY_MP_CB_TOP_CHORD_SECTION_DESIG)
                or ""
            )

        btype_raw = pair_designs.get("cb_type") if pair_designs else None
        if not btype_raw:
            btype_raw = idict.get(f"{KEY_MP_CB_TYPE}.{pair_id}") or idict.get(f"{KEY_MP_CB_TYPE}{mi_sfx}") or idict.get(KEY_MP_CB_TYPE)
        brace_lbl = "X-Bracing" if not btype_raw or "X" in str(btype_raw).upper() else "K-Bracing"

        diag_type_raw = (
            od.get(f"member_properties.cross_bracing_details.{pair_id}.diagonal.section_type")
            or idict.get(f"{KEY_MP_CB_BRACING_SECTION_TYPE}.{pair_id}")
            or idict.get(f"{KEY_MP_CB_BRACING_SECTION_TYPE}{mi_sfx}")
            or idict.get(KEY_MP_CB_BRACING_SECTION_TYPE)
            or "Double Angles"
        )
        diag_type_lbl = self._section_type_label(diag_type_raw)

        tc_type_raw = (
            od.get(f"member_properties.cross_bracing_details.{pair_id}.top_chord.section_type")
            or idict.get(f"{KEY_MP_CB_TOP_CHORD_SECTION_TYPE}.{pair_id}")
            or idict.get(f"{KEY_MP_CB_TOP_CHORD_SECTION_TYPE}{mi_sfx}")
            or idict.get(KEY_MP_CB_TOP_CHORD_SECTION_TYPE)
            or "Double Angles"
        )
        tc_type_lbl = self._section_type_label(tc_type_raw)

        bc_type_raw = (
            od.get(f"member_properties.cross_bracing_details.{pair_id}.bottom_chord.section_type")
            or idict.get(f"{KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE}.{pair_id}")
            or idict.get(f"{KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE}{mi_sfx}")
            or idict.get(KEY_MP_CB_BOTTOM_CHORD_SECTION_TYPE)
            or "Double Angles"
        )
        bc_type_lbl = self._section_type_label(bc_type_raw)

        for fid, val in (
            (KEY_TD_CB_SECTION_INPUTS_BRACING_TYPE,                      brace_lbl),
            (KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_TYPE,             diag_type_lbl),
            (KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE,           tc_type_lbl),
            (KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE,        bc_type_lbl),
            (KEY_TD_CB_SECTION_INPUTS_BRACING_SECTION_DESIGNATION,      diag_des  or ""),
            (KEY_TD_CB_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION,    chord_des or ""),
            (KEY_TD_CB_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION, chord_des or ""),
        ):
            w = self._widgets.get(fid)
            if w:
                w.setText(val)

        for card_name, designation, type_lbl in (
            ("Bracing",      diag_des,  diag_type_lbl),
            ("Top Chord",    chord_des, tc_type_lbl),
            ("Bottom Chord", chord_des, bc_type_lbl),
        ):
            self._fill_section_card(card_name, designation, type_lbl)

    def _populate_ed_pair_details(self, pair_key: str) -> None:
        # ── Always-visible fields ────────────────────────────────────────────
        design_w = self._widgets.get(KEY_TD_ED_SECTION_INPUTS_DESIGN)
        if design_w:
            design_w.setText("End Diaphragm")

        no_cb_w = self._widgets.get(KEY_TD_ED_SECTION_INPUTS_NO_OF_CB)
        if no_cb_w:
            no_cb_w.setText("2")

        conn_w = self._widgets.get(KEY_TD_ED_SECTION_INPUTS_CONNECTION_TYPE)
        if conn_w:
            idict   = getattr(self._backend, "input_dict", {}) or {}
            pair_id = pair_key.replace("-", "")
            _pm     = re.match(r"G(\d+)G", pair_id)
            mi_sfx  = f".{pair_id}.E{_pm.group(1)}M1" if _pm else ""
            conn_val = (
                idict.get(f"{KEY_MP_ED_BRACING_CONNECTION}.{pair_id}")
                or idict.get(f"{KEY_MP_ED_BRACING_CONNECTION}{mi_sfx}")
                or idict.get(KEY_MP_ED_BRACING_CONNECTION)
                or "Bolted"
            )
            conn_w.setText(str(conn_val))

        pair_designs = self._ed_designs_dict.get(pair_key, {}) if getattr(self, "_ed_designs_dict", None) else {}
        od           = getattr(self._backend, "output_dict", {}) or {}
        idict        = getattr(self._backend, "input_dict", {}) or {}
        pair_id      = pair_key.replace("-", "")
        _pm          = re.match(r"G(\d+)G", pair_id)
        mi_sfx       = f".{pair_id}.E{_pm.group(1)}M1" if _pm else ""
        ed_type = (
            pair_designs.get("ed_type")
            or od.get(f"member_properties.end_diaphragm_details.{pair_id}.type")
            or idict.get(f"{KEY_MP_ED_TYPE}{mi_sfx}")
            or idict.get(f"{KEY_MP_ED_TYPE}.{pair_id}")
            or idict.get(KEY_MP_ED_TYPE)
            or ""
        )
        print(f"[DEBUG _populate_ed_pair_details] pair_key={pair_key}, ed_type='{ed_type}', pair_designs={pair_designs}")
        type_w = self._widgets.get(KEY_TD_ED_SECTION_INPUTS_TYPE)
        if type_w:
            type_w.setText(ed_type)

        # Trigger ED type changed handler so UI layout (groups & cards) updates for ed_type
        self._on_ed_type_changed(ed_type if ed_type else "Cross Bracing")

        if ed_type == "Welded Beam":
            wb = pair_designs.get("beam", {}) if isinstance(pair_designs, dict) else {}
            depth_val = wb.get("depth_mm") or wb.get("total_depth") or idict.get(f"{KEY_MP_ED_TOTAL_DEPTH}{mi_sfx}") or idict.get(KEY_MP_ED_TOTAL_DEPTH) or 300.0
            web_t_val = wb.get("web_thk_mm") or wb.get("Web.Thickness") or idict.get(f"{KEY_MP_ED_WEB_THICKNESS}{mi_sfx}") or idict.get(KEY_MP_ED_WEB_THICKNESS) or 8.0
            top_w_val = wb.get("top_width_mm") or idict.get(f"{KEY_MP_ED_TOP_FLANGE_WIDTH}{mi_sfx}") or idict.get(KEY_MP_ED_TOP_FLANGE_WIDTH) or 150.0
            top_t_val = wb.get("top_thk_mm") or wb.get("TopFlange.Thickness") or idict.get(f"{KEY_MP_ED_TOP_FLANGE_THICKNESS}{mi_sfx}") or idict.get(KEY_MP_ED_TOP_FLANGE_THICKNESS) or 10.0
            bot_w_val = wb.get("bot_width_mm") or idict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_WIDTH}{mi_sfx}") or idict.get(KEY_MP_ED_BOTTOM_FLANGE_WIDTH) or 150.0
            bot_t_val = wb.get("bot_thk_mm") or wb.get("BottomFlange.Thickness") or idict.get(f"{KEY_MP_ED_BOTTOM_FLANGE_THICKNESS}{mi_sfx}") or idict.get(KEY_MP_ED_BOTTOM_FLANGE_THICKNESS) or 10.0
            symm_val  = wb.get("symmetry") or idict.get(f"{KEY_MP_ED_SYMMETRY}{mi_sfx}") or idict.get(KEY_MP_ED_SYMMETRY) or "Symmetrical"

            # Populate left panel line edits for Welded Beam
            wb_input_map = {
                KEY_TD_ED_SECTION_INPUTS_SYMMETRY:               symm_val,
                KEY_TD_ED_SECTION_INPUTS_TOTAL_DEPTH:             depth_val,
                KEY_TD_ED_SECTION_INPUTS_WEB_THICKNESS:           web_t_val,
                KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_WIDTH:        top_w_val,
                KEY_TD_ED_SECTION_INPUTS_TOP_FLANGE_THICKNESS:    top_t_val,
                KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_WIDTH:     bot_w_val,
                KEY_TD_ED_SECTION_INPUTS_BOTTOM_FLANGE_THICKNESS: bot_t_val,
            }
            for fid, val in wb_input_map.items():
                w = self._widgets.get(fid)
                if w:
                    w.setText(str(val) if val is not None else "")

            # Calculate physical section properties for property card display
            try:
                d_num, wt_num, tw_num, tt_num, bw_num, bt_num = float(depth_val), float(web_t_val), float(top_w_val), float(top_t_val), float(bot_w_val), float(bot_t_val)
                hw = d_num - tt_num - bt_num
                area_cm2 = round((tw_num * tt_num + bw_num * bt_num + hw * wt_num) / 100.0, 2)
                iz_cm4 = round((wt_num * hw**3 / 12.0 + tw_num * tt_num * (hw/2 + tt_num/2)**2 * 2) / 10000.0, 2)
                mass_kgm = round(area_cm2 * 100.0 * 7850e-9 * 1000.0, 2)
            except Exception:
                area_cm2, iz_cm4, mass_kgm = "", "", ""

            wb_card_dict = {
                "D (mm)":      depth_val,
                "tw (mm)":     web_t_val,
                "B_top (mm)":  top_w_val,
                "tf_top (mm)": top_t_val,
                "B_bot (mm)":  bot_w_val,
                "tf_bot (mm)": bot_t_val,
                "A (cm²)":     area_cm2,
                "Iz (cm⁴)":    iz_cm4,
                "M (Kg/m)":    mass_kgm,
            }
            wb_fields = self._prop_fields.get("ED Welded Beam", {})
            for k, v in wb_card_dict.items():
                field = wb_fields.get(k)
                if field:
                    field.setText(str(v) if v != "" else "")

        elif ed_type == "Rolled Beam":
            # Rolled Beam — find IS section designation from output_dict or input_dict
            od      = getattr(self._backend, "output_dict", {}) or {}
            idict   = getattr(self._backend, "input_dict", {}) or {}
            pair_id = pair_key.replace("-", "")
            _pm     = re.match(r"G(\d+)G", pair_id)
            mi_sfx  = f".{pair_id}.E{_pm.group(1)}M1" if _pm else ""
            beam_dict = pair_designs.get("beam", {}) if isinstance(pair_designs, dict) else {}
            is_des = (
                beam_dict.get("designation")
                or beam_dict.get("Optimum.Designation")
                or od.get(f"member_properties.end_diaphragm_details.{pair_id}.is_section")
                or od.get(f"{KEY_MP_ED_IS_SECTION}.{pair_id}")
                or idict.get(f"{KEY_MP_ED_IS_SECTION}{mi_sfx}")
                or idict.get(f"{KEY_MP_ED_IS_SECTION}.{pair_id}")
                or idict.get(KEY_MP_ED_IS_SECTION)
                or ""
            )

            # Show IS section designation in the IS Section field
            is_w = self._widgets.get(KEY_TD_ED_SECTION_INPUTS_IS_SECTION)
            if is_w:
                is_w.setText(str(is_des) if is_des else "")

            # Populate section card from database
            self._fill_section_card("ed_End Diaphragm", is_des, "Rolled Beam")
            s_val = (
                od.get(f"{KEY_TD_ED_PROP_L}.{pair_id}")
                or od.get(KEY_TD_ED_PROP_L)
                or idict.get(KEY_TS_GIRDER_SPACING)
            )
            if s_val is not None:
                ed_fields = self._prop_fields.get("ed_End Diaphragm", {})
                l_field = ed_fields.get("L (m)")
                if l_field:
                    l_field.setText(f"{float(s_val):.4g}")

            # Top and Bottom Chord cards are not applicable for Rolled Beam
            self._fill_section_card("ed_Top Chord",    "", "")
            self._fill_section_card("ed_Bottom Chord", "", "")

        else:  # Cross Bracing
            pair_id = pair_key.replace("-", "")

            diag_des  = self._get_governing_section(pair_designs, "diagonal") if pair_designs else ""
            chord_des = self._get_governing_section(pair_designs, "chord") if pair_designs else ""

            btype_raw = pair_designs.get("ed_bracing_type") if pair_designs else None
            brace_lbl = ("K-Bracing" if "K" in str(btype_raw).upper() else "X-Bracing") if btype_raw else ""

            idict = getattr(self._backend, "input_dict", {}) or {}
            m = re.match(r"G(\d+)G", pair_id)
            girder_idx = m.group(1) if m else "1"
            e_suffix = f".{pair_id}.E{girder_idx}M1"

            diag_type_lbl = self._section_type_label(
                idict.get(f"{KEY_MP_ED_BRACING_SECTION}.{pair_id}")
                or idict.get(f"{KEY_MP_ED_BRACING_SECTION}{e_suffix}")
                or idict.get(KEY_MP_ED_BRACING_SECTION)
                or ""
            )
            tc_type_lbl = self._section_type_label(
                idict.get(f"{KEY_MP_ED_TOP_CHORD_SECTION_TYPE}{e_suffix}", "")
            )
            bc_type_lbl = self._section_type_label(
                idict.get(f"{KEY_MP_ED_BOTTOM_CHORD_SECTION_TYPE}{e_suffix}", "")
            )

            for fid, val in (
                (KEY_TD_ED_SECTION_INPUTS_BRACING_TYPE,                  brace_lbl),
                (KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_TYPE,          diag_type_lbl),
                (KEY_TD_ED_SECTION_INPUTS_BRACING_SECTION_DESIGNATION,   diag_des  or ""),
                (KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_TYPE,        tc_type_lbl),
                (KEY_TD_ED_SECTION_INPUTS_TOP_CHORD_SECTION_DESIGNATION, chord_des or ""),
                (KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_TYPE,     bc_type_lbl),
                (KEY_TD_ED_SECTION_INPUTS_BOTTOM_CHORD_SECTION_DESIGNATION, chord_des or ""),
            ):
                w = self._widgets.get(fid)
                if w:
                    w.setText(val)

            for card_name, designation, type_lbl in (
                ("ed_End Diaphragm", diag_des,  diag_type_lbl),
                ("ed_Top Chord",     chord_des, tc_type_lbl),
                ("ed_Bottom Chord",  chord_des, bc_type_lbl),
            ):
                self._fill_section_card(card_name, designation, type_lbl)

    def _get_governing_section(self, member_designs: dict, member_type: str) -> str:
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary
        type_data = member_designs.get(member_type, {})
        for force_type in ("tension", "compression"):
            res = _extract_osdag_summary(type_data.get(force_type) or {})
            sec = res.get("section")
            if sec:
                return str(sec)
        return ""

    def _fill_section_card(
        self,
        card_name:          str,
        designation:        str,
        section_type_label: str,
    ) -> None:
        props   = self._query_section_db(designation) if designation else {}
        preview = self._section_previews.get(card_name)

        if preview is not None:
            if designation and props:
                db_des = props.get("_db_designation", designation)
                family = props.get("_section_family", "angle")
                if family == "beam":
                    stype = "beam"
                elif family == "channel":
                    stype = _SECTION_TYPE_MAP.get(section_type_label, "channel")
                    if stype not in ("channel", "double_channel"):
                        stype = "channel"
                else:
                    stype = _SECTION_TYPE_MAP.get(section_type_label) or "double_angle_long"
                preview.set_section(stype, db_des)
            else:
                preview.clear()

        fields = self._prop_fields.get(card_name, {})
        for prop_label, field in fields.items():
            val = props.get(prop_label)
            field.setText(f"{val:.4g}") if val is not None else field.clear()

    def _query_section_db(self, designation: str) -> dict:
        if not designation:
            return {}

        try:
            from osdagbridge.desktop.ui.widgets.section_viewer import DB_PATH
        except ImportError:
            return {}

        designation_stripped = str(designation).strip()
        nums = re.findall(r"\d+(?:\.\d+)?", designation_stripped)
        if not nums:
            return {}
        like_pattern = "%" + "%".join(nums) + "%"

        try:
            con = sqlite3.connect(str(DB_PATH))
            cur = con.cursor()

            # ── Try Beams table first (for Rolled Beam IS sections: ISMB, ISLB, MB, etc.) ──
            cur.execute(
                'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy '
                'FROM Beams WHERE Designation = ? OR Designation LIKE ?',
                (designation_stripped, like_pattern),
            )
            row = cur.fetchone()
            if row:
                con.close()
                db_des, mass, area, d_val, b, tw, tf, iz, iy, rz, ry, zz, zy, zpz, zpy = row
                return {
                    "_db_designation": db_des,
                    "_section_family": "beam",
                    "D (mm)":    round(d_val, 2),
                    "H (m)":     round(d_val / 1000, 4),
                    "B (m)":     round(b / 1000, 4),
                    "B_top (mm)": round(b,    2),
                    "tf_top (mm)": round(tf,  2),
                    "tw (mm)":   round(tw,    2),
                    "tw (m)":    round(tw / 1000, 4),
                    "tF (m)":    round(tf / 1000, 4),
                    "B_bot (mm)": round(b,    2),
                    "tf_bot (mm)": round(tf,  2),
                    "A (cm²)":   round(area,  4),
                    "Iz (cm⁴)":  round(iz,    4),
                    "Iv (cm⁴)":  round(iy,    4),
                    "M (Kg/m)":  round(mass,  4),
                    "rz (cm)":   rz,
                    "rv (cm)":   ry,
                    "Zz (cm³)":  zz,
                    "Zv (cm³)":  zy,
                    "Zuz (cm³)": zpz,
                    "Zuv (cm³)": zpy,
                }

            # ── Equal/Unequal Angles ──────────────────────────────────────────────────────
            for table in ("EqualAngle", "UnequalAngle"):
                cur.execute(
                    f'SELECT Designation, Mass, Area, a, b, t, Iz, Iy, "Iv(min)", rz, ry, "rv(min)", '
                    f'Zz, Zy, Zpz, Zpy FROM {table} WHERE Designation LIKE ?',
                    (like_pattern,),
                )
                row = cur.fetchone()
                if row:
                    con.close()
                    db_des, mass, area, a, b, t, iz, iy, iv_min, rz, ry, rv_min, zz, zy, zpz, zpy = row
                    return {
                        "_db_designation": db_des,
                        "_section_family": "angle",
                        "L (m)":     round(a / 1000, 4),
                        "H (m)":     round(b / 1000, 4),
                        "B (m)":     round(t / 1000, 4),
                        "tw (m)":    round(t / 1000, 4),
                        "tF (m)":    round(t / 1000, 4),
                        "rz (cm)":   rz,
                        "M (Kg/m)":  mass,
                        "A (cm²)":   area,
                        "Iz (cm⁴)":  iz,
                        "Iv (cm⁴)":  iv_min,
                        "rv (cm)":   rv_min,
                        "Zz (cm³)":  zz,
                        "Zv (cm³)":  zy,
                        "Zuz (cm³)": zpz,
                        "Zuv (cm³)": zpy,
                    }

            # ── Channels ─────────────────────────────────────────────────────────────────
            cur.execute(
                'SELECT Designation, Mass, Area, D, B, tw, T, Iz, Iy, rz, ry, Zz, Zy, Zpz, Zpy '
                'FROM Channels WHERE Designation LIKE ?',
                (like_pattern,),
            )
            row = cur.fetchone()
            if row:
                con.close()
                db_des, mass, area, d_val, b, tw, tf, iz, iy, rz, ry, zz, zy, zpz, zpy = row
                return {
                    "_db_designation": db_des,
                    "_section_family": "channel",
                    "L (m)":     round(d_val / 1000, 4),
                    "H (m)":     round(b     / 1000, 4),
                    "B (m)":     round(b     / 1000, 4),
                    "tw (m)":    round(tw    / 1000, 4),
                    "tF (m)":    round(tf    / 1000, 4),
                    "rz (cm)":   rz,
                    "M (Kg/m)":  mass,
                    "A (cm²)":   area,
                    "Iz (cm⁴)":  iz,
                    "Iv (cm⁴)":  iy,
                    "rv (cm)":   ry,
                    "Zz (cm³)":  zz,
                    "Zv (cm³)":  zy,
                    "Zuz (cm³)": zpz,
                    "Zuv (cm³)": zpy,
                }

            con.close()
        except Exception:
            pass
        return {}

    # ── Design check HTML (no Pair column) ────────────────────────────────

    def _build_cb_design_check_html(self, pair_key: str, forces_dict: dict, designs_dict: dict) -> str:
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        rows_html = []
        pairs     = forces_dict.get("pairs", {})
        vals      = pairs.get(pair_key, {})

        pair_designs = designs_dict.get(pair_key, {})
        n_members = self._members_per_pair.get(pair_key, 1)
        pair_idx = self._pair_keys.index(pair_key) if pair_key in self._pair_keys else 0

        for m_idx in range(n_members):
            member_id = f"B{pair_idx+1}M{m_idx+1}"

            for label, member_type, t_key, c_key in (
                ("Diagonal", "diagonal", "diag_tension_kN",  "diag_compression_kN"),
                ("Chord",    "chord",    "chord_tension_kN", "chord_compression_kN"),
            ):
                member_data = pair_designs.get(member_type, {})

                for force_type, force_key in (
                    ("Tension",     t_key),
                    ("Compression", c_key),
                ):
                    force_kn = vals.get(force_key)
                    if force_kn is None:
                        continue

                    res     = _extract_osdag_summary(member_data.get(force_type.lower()) or {})
                    section = res.get("section")  or "—"
                    cap_kn  = res.get("capacity_kN")
                    eff     = res.get("efficiency")
                    slnd    = res.get("slenderness")
                    conn    = res.get("connection") or "—"

                    cap_str  = self._fmt_float(cap_kn, 2)
                    eff_str  = self._fmt_float(eff, 3)
                    slnd_str = self._fmt_float(slnd, 1)

                    eff_num = self._to_float(eff)
                    if eff_num is None:
                        status_color, status = "#888888", "N/A"
                    elif eff_num <= 1.0:
                        status_color, status = "#3a7d00", "PASS"
                    else:
                        status_color, status = "#c0392b", "FAIL"

                    rows_html.append(
                        f"<tr>"
                        f"<td>{member_id}</td><td>{label} ({force_type})</td>"
                        f"<td>{force_kn:.3f}</td><td>{section}</td><td>{conn}</td>"
                        f"<td>{slnd_str}</td><td>{cap_str}</td><td>{eff_str}</td>"
                        f"<td style='color:{status_color};font-weight:bold;'>{status}</td>"
                        f"</tr>"
                    )

        if not rows_html:
            return self._empty_design_check_html()

        return self._wrap_design_check_table(rows_html)

    def _empty_design_check_html(self) -> str:
        hdr_style = "background:#f0f0f0;font-weight:bold;padding:5px 8px;border-bottom:2px solid #ddd;"
        td_style  = "padding:4px 8px;border-bottom:1px solid #e8e8e8;color:#888888;"
        header = (
            f"<tr>"
            f"<th style='{hdr_style}'>Member</th>"
            f"<th style='{hdr_style}'>Force Type</th>"
            f"<th style='{hdr_style}'>Force (kN)</th>"
            f"<th style='{hdr_style}'>Section</th>"
            f"<th style='{hdr_style}'>Connection</th>"
            f"<th style='{hdr_style}'>λ (slend.)</th>"
            f"<th style='{hdr_style}'>Capacity (kN)</th>"
            f"<th style='{hdr_style}'>Utilization Ratio</th>"
            f"<th style='{hdr_style}'>Status</th>"
            f"</tr>"
        )
        empty_row = (
            f"<tr>" + f"<td style='{td_style}'>—</td>" * 9 + f"</tr>"
        )
        return (
            "<style>"
            "body{margin:0;padding:0;}"
            "table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:11px;margin:0;border:1px solid black;}"
            "tr:nth-child(even){background:#fafafa;}"
            "</style>"
            "<table width='100%'>" + header + empty_row + "</table>"
        )

    def load_design_check_html(self, html: str) -> None:
        self.design_check_text.setHtml(html)


    def _build_ed_design_check_html(self, pair_key: str, forces_dict: dict, designs_dict: dict) -> str:
        from osdagbridge.core.bridge_types.plate_girder.results_data import _extract_osdag_summary

        rows_html    = []
        pairs        = forces_dict.get("pairs", {})
        vals         = pairs.get(pair_key, {})
        pair_designs = designs_dict.get(pair_key, {})
        n_members    = 2  # One end diaphragm at each end of the span
        ed_type      = pair_designs.get("ed_type", "Cross Bracing")
        pair_num     = (self._pair_keys.index(pair_key) + 1) if pair_key in self._pair_keys else 1

        for m_idx in range(n_members):
            member_id = f"E{pair_num}M{m_idx + 1}"   # → E1M1, E1M2 / E2M1, E2M2

            if ed_type in ("Rolled Beam", "Welded Beam"):
                beam_res = pair_designs.get("beam") or {}
                res      = _extract_osdag_summary(beam_res)
                section  = res.get("section") or "—"
                cap_kn   = res.get("capacity_kN") or res.get("capacity_kNm") or beam_res.get("Moment.Strength") or beam_res.get("Shear.Strength")
                eff      = res.get("efficiency") or beam_res.get("Optimum.UR")
                slnd     = res.get("slenderness") or beam_res.get("ESR")
                conn     = res.get("connection") or ("Welded" if ed_type == "Welded Beam" else "Bolted")
                force_val = beam_res.get("Load.Moment") or beam_res.get("Load.Shear")
                force_str = f"{float(force_val):.3f}" if force_val is not None else "—"
                cap_str  = self._fmt_float(cap_kn, 2)
                eff_str  = self._fmt_float(eff, 3)
                slnd_str = self._fmt_float(slnd, 1)

                eff_num = self._to_float(eff)
                if eff_num is None:
                    status_color, status = "#888888", "N/A"
                elif eff_num <= 1.0:
                    status_color, status = "#3a7d00", "PASS"
                else:
                    status_color, status = "#c0392b", "FAIL"
                rows_html.append(
                    f"<tr><td>{member_id}</td><td>{ed_type}</td>"
                    f"<td>{force_str}</td><td>{section}</td><td>{conn}</td>"
                    f"<td>{slnd_str}</td><td>{cap_str}</td><td>{eff_str}</td>"
                    f"<td style='color:{status_color};font-weight:bold;'>{status}</td></tr>"
                )
            else:  # Cross Bracing — same structure as CB but E prefix already handled
                for label, member_type, t_key, c_key in (
                    ("Diagonal", "diagonal", "diag_tension_kN",  "diag_compression_kN"),
                    ("Chord",    "chord",    "chord_tension_kN", "chord_compression_kN"),
                ):
                    member_data = pair_designs.get(member_type, {})
                    for force_type, force_key in (
                        ("Tension",     t_key),
                        ("Compression", c_key),
                    ):
                        force_kn = vals.get(force_key)
                        if force_kn is None:
                            continue
                        res      = _extract_osdag_summary(member_data.get(force_type.lower()) or {})
                        section  = res.get("section")   or "—"
                        cap_kn   = res.get("capacity_kN")
                        eff      = res.get("efficiency")
                        slnd     = res.get("slenderness")
                        conn     = res.get("connection") or "—"
                        cap_str  = self._fmt_float(cap_kn, 2)
                        eff_str  = self._fmt_float(eff, 3)
                        slnd_str = self._fmt_float(slnd, 1)

                        eff_num = self._to_float(eff)
                        if eff_num is None:
                            status_color, status = "#888888", "N/A"
                        elif eff_num <= 1.0:
                            status_color, status = "#3a7d00", "PASS"
                        else:
                            status_color, status = "#c0392b", "FAIL"
                        rows_html.append(
                            f"<tr><td>{member_id}</td><td>{label} ({force_type})</td>"
                            f"<td>{force_kn:.3f}</td><td>{section}</td><td>{conn}</td>"
                            f"<td>{slnd_str}</td><td>{cap_str}</td><td>{eff_str}</td>"
                            f"<td style='color:{status_color};font-weight:bold;'>{status}</td></tr>"
                        )

        if not rows_html:
            return self._empty_design_check_html()

        return self._wrap_design_check_table(rows_html)
    
    def _wrap_design_check_table(self, rows_html: list[str]) -> str:
        hdr_style = "background:#f0f0f0;font-weight:bold;padding:5px 8px;border-bottom:2px solid #ddd;"
        td_style  = "padding:4px 8px;border-bottom:1px solid #e8e8e8;"
        header = (
            f"<tr>"
            f"<th style='{hdr_style}'>Member</th>"
            f"<th style='{hdr_style}'>Force Type</th>"
            f"<th style='{hdr_style}'>Force (kN)</th>"
            f"<th style='{hdr_style}'>Section</th>"
            f"<th style='{hdr_style}'>Connection</th>"
            f"<th style='{hdr_style}'>λ (slend.)</th>"
            f"<th style='{hdr_style}'>Capacity (kN)</th>"
            f"<th style='{hdr_style}'>Utilization Ratio</th>"
            f"<th style='{hdr_style}'>Status</th>"
            f"</tr>"
        )
        rows_styled = [r.replace("<td>", f"<td style='{td_style}'>") for r in rows_html]
        return (
            "<style>body{margin:0;padding:0;}"
            "table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:11px;margin:0;border:1px solid black;}"
            "tr:nth-child(even){background:#fafafa;}</style>"
            "<table width='100%'>" + header + "".join(rows_styled) + "</table>"
        )
    
    def _on_ed_type_changed(self, text: str) -> None:
        is_welded = (text == "Welded Beam")
        is_rolled = (text == "Rolled Beam")
        is_cb     = not (is_welded or is_rolled)

        # Show/hide left panel field rows per type
        for wgt in self._ed_group_widgets.get("crossbracing", []):
            wgt.setVisible(is_cb)
        for wgt in self._ed_group_widgets.get("welded_beam", []):
            wgt.setVisible(is_welded)
        for wgt in self._ed_group_widgets.get("rolled_beam", []):
            wgt.setVisible(is_rolled)

        # Switch right panel cards
        self._switch_ed_right_panel(text)

    def _switch_ed_right_panel(self, ed_type: str) -> None:
        is_welded = (ed_type == "Welded Beam")
        self._ed_cards_cb.setVisible(not is_welded)
        self._ed_cards_wb.setVisible(is_welded)

        # Show/hide Top Chord and Bottom Chord cards for Rolled Beam vs Cross Bracing
        top_chord_card = self._widgets.get(KEY_TD_ED_SECTION_PROPS_TOP_CHORD)
        bot_chord_card = self._widgets.get(KEY_TD_ED_SECTION_PROPS_BOTTOM_CHORD)
        is_cb = (ed_type == "Cross Bracing")
        if top_chord_card is not None:
            top_chord_card.setVisible(is_cb)
        if bot_chord_card is not None:
            bot_chord_card.setVisible(is_cb)

    def _on_tab_changed(self, index: int):
        tab_key = "cb" if index == 0 else "ed"
        # Point self.design_check_text at the active tab's widget
        active = self._tab_result_texts.get(tab_key)
        if active:
            self.design_check_text = active
    
    @staticmethod
    def _section_type_label(backend_type: str) -> str:
        if not backend_type:
            return "Double Angles"
        b_upper = str(backend_type).upper()
        if "DOUBLE CHANNEL" in b_upper:
            return "Double Channel"
        elif "CHANNEL" in b_upper:
            return "Channel"
        elif "SHORT" in b_upper:
            return "Double Angle (Short Leg)"
        elif "DOUBLE" in b_upper or "LONG" in b_upper:
            return "Double Angles"
        elif "ANGLE" in b_upper:
            return "Angle"
        return str(backend_type)

    @staticmethod
    def _fmt_float(val, precision: int = 3, default: str = "—") -> str:
        if val is None or val == "" or val == "—":
            return default
        try:
            return f"{float(val):.{precision}f}"
        except (ValueError, TypeError):
            return str(val)

    @staticmethod
    def _to_float(val) -> float | None:
        if val is None or val == "" or val == "—":
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None