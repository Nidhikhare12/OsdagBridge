from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QSizeGrip,
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.utils.styled_scroll_area import StyledScrollArea
from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import StatusBadge
from osdagbridge.desktop.ui.utils.custom_widgets import PercentBarWidget

# Import the schema
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import DECK_DESIGN_SUMMARY_SCHEMA


class NoScrollTable(QTableWidget):
    """Passes wheel events to parent scroll area — table never scrolls."""
    def wheelEvent(self, event):
        event.ignore()


class DeckDesign(QDialog):
    """
    Deck Design dialog — schema-driven dialog that displays deck properties, 
    reinforcement details, utilization ratios, and design check results.
    """

    _REBAR_ROW_HEIGHT  = 50
    _REBAR_HEADER_HEIGHT = 48

    def __init__(self, parent=None):
        super().__init__(None)
        self._main_window = parent
        self.setObjectName("DeckDesign")
        self.resize(1024, 720)
        self.setMinimumSize(900, 520)
        self.schema = DECK_DESIGN_SUMMARY_SCHEMA
        self.init_ui()

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #90AF13;
            }
        """)

    def setupWrapper(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | Qt.Window
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar()
        self.title_bar.setTitle("Deck Design")
        main_layout.addWidget(self.title_bar)

        self.content_widget = QWidget(self)
        main_layout.addWidget(self.content_widget, 1)

        size_grip = QSizeGrip(self)
        size_grip.setFixedSize(16, 16)

        overlay = QHBoxLayout()
        overlay.setContentsMargins(0, 0, 4, 4)
        overlay.addStretch(1)
        overlay.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)
        main_layout.addLayout(overlay)

    def init_ui(self):
        self.setupWrapper()

        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        scroll_area = StyledScrollArea()

        container = QWidget()
        container.setStyleSheet("background-color: white;")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(12)

        # Deck Properties — left half only
        props_row = QHBoxLayout()
        props_row.setContentsMargins(0, 0, 0, 0)
        props_row.setSpacing(0)
        props_row.addWidget(self._build_properties_section(), 1)
        props_row.addStretch(1)
        container_layout.addLayout(props_row)

        container_layout.addWidget(self._build_reinforcement_section())
        container_layout.addWidget(self._build_utilization_section())
        container_layout.addWidget(self._build_design_check_section())
        container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        backend = getattr(self._main_window, "backend", None)
        if backend is not None and getattr(backend, "grillage_geometry", None) is not None:
            try:
                result = backend.output_dict.get("deck_design_results")
                self.load_data(result)
            except Exception:
                self.design_check_text.setHtml(
                    "<p style='color:#c0392b;font-size:11px;padding:12px;'>"
                    "Deck design could not be computed. Check inputs and try again."
                    "</p>"
                )
        else:
            self.design_check_text.setHtml(
                "<p style='color:#888888;font-size:11px;padding:16px;'>"
                "Click <b>Design</b> in the Input panel to run the analysis, "
                "then re-open this dialog to see deck design results."
                "</p>"
            )

    def _create_card_frame(self) -> QFrame:
        frame = QFrame(self)
        frame.setObjectName("girderCard")
        frame.setStyleSheet(
            "QFrame#girderCard {"
            "  background-color: white;"
            "  border: 1px solid #b0b0b0;"
            "  border-radius: 6px;"
            "}"
        )
        return frame

    def _create_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            "font-size: 13px; color: #2B2B2B; font-weight: bold;"
            " background: transparent; border: none;"
        )
        label.setAutoFillBackground(False)
        return label

    def _create_small_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setTextFormat(Qt.RichText)
        label.setStyleSheet(
            "font-size: 11px; color: #333333;"
            " background: transparent; border: none;"
        )
        label.setAutoFillBackground(False)
        return label

    def _readonly_field(self) -> QLineEdit:
        field = QLineEdit()
        field.setReadOnly(True)
        field.setMinimumWidth(80)
        field.setMinimumHeight(28)
        field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        apply_field_style(field)
        return field

    def _make_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(12)
        grid.setColumnMinimumWidth(0, 230)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        return grid

    def _add_row(self, grid, row, text, widget):
        grid.addWidget(
            self._create_small_label(text), row, 0,
            Qt.AlignLeft | Qt.AlignVCenter,
        )
        grid.addWidget(widget, row, 1)
        return row + 1

    def _build_properties_section(self) -> QFrame:
        prop_schema = self.schema.get("properties_card", {})
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label(prop_schema.get("title", "Deck Properties:")))

        grid = self._make_grid()
        self._prop_fields = {}
        
        r = 0
        for field_def in prop_schema.get("fields", []):
            field = self._readonly_field()
            data_key = field_def.get("data_key")
            if data_key:
                self._prop_fields[data_key] = field
            r = self._add_row(grid, r, field_def.get("label", ""), field)

        card_layout.addLayout(grid)
        return card

    def _build_reinforcement_section(self) -> QFrame:
        reinf_schema = self.schema.get("reinforcement_table", {})
        card = self._create_card_frame()
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)
        card_layout.addWidget(self._create_label(reinf_schema.get("title", "Reinforcement Details:")))

        rows_def = reinf_schema.get("rows", [])
        headers  = reinf_schema.get("columns", [])
        num_rows = len(rows_def)
        num_cols = len(headers)

        self._overhang_row_idx = next(
            (i for i, r in enumerate(rows_def) if r.get("is_overhang")), None
        )

        self.rebar_table = NoScrollTable()
        self.rebar_table.setRowCount(num_rows)
        self.rebar_table.setColumnCount(num_cols)
        self.rebar_table.setHorizontalHeaderLabels(headers)

        for row, row_def in enumerate(rows_def):
            for col, text in enumerate([
                row_def.get("direction", ""),
                row_def.get("zone", ""),
                row_def.get("face", ""),
            ]):
                item = QTableWidgetItem(text)
                item.setFlags(Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignCenter)
                self.rebar_table.setItem(row, col, item)
            for col in range(3, num_cols):
                cell = QTableWidgetItem("")
                cell.setFlags(Qt.ItemIsEnabled)
                cell.setTextAlignment(Qt.AlignCenter)
                self.rebar_table.setItem(row, col, cell)

        if self._overhang_row_idx is not None:
            self.rebar_table.setRowHidden(self._overhang_row_idx, True)

        h_header = self.rebar_table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        h_header.setDefaultAlignment(Qt.AlignCenter)

        v_header = self.rebar_table.verticalHeader()
        v_header.setVisible(False)
        v_header.setDefaultSectionSize(self._REBAR_ROW_HEIGHT)
        v_header.setSectionResizeMode(QHeaderView.Stretch)

        self.rebar_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.rebar_table.setSelectionMode(QTableWidget.NoSelection)
        self.rebar_table.setFocusPolicy(Qt.NoFocus)
        self.rebar_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rebar_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rebar_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rebar_table.setAlternatingRowColors(True)

        n_non_overhang = sum(1 for r in rows_def if not r.get("is_overhang", False))
        self.rebar_table.setFixedHeight(
            self._REBAR_HEADER_HEIGHT + n_non_overhang * self._REBAR_ROW_HEIGHT + 2
        )

        self.rebar_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: 1px solid #e0e0e0;
                color: #333333;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
                color: #333333;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                color: #333333;
                padding: 8px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
                font-size: 11px;
            }
        """)

        card_layout.addWidget(self.rebar_table)

        self._overhang_note = QLabel(reinf_schema.get("overhang_note", ""))
        self._overhang_note.setStyleSheet(
            "font-size: 10px; color: #666666; background: transparent; border: none;"
        )
        self._overhang_note.setWordWrap(False)
        self._overhang_note.setVisible(False)
        card_layout.addWidget(self._overhang_note)

        return card

    def _build_utilization_section(self) -> QFrame:
        util_schema = self.schema.get("utilization_card", {})
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)
        card_layout.addWidget(self._create_label(util_schema.get("title", "Utilization Summary:")))

        self._ur_widgets: dict = {}

        for check_def in util_schema.get("checks", []):
            key = check_def.get("key")
            label = check_def.get("label", "")
            is_overhang = check_def.get("is_overhang", False)
            
            bar = PercentBarWidget(label=label, value=0.0, parent=self)
            
            card_layout.addWidget(bar)
            bar.setVisible(not is_overhang)

            self._ur_widgets[key] = {
                "bar":   bar,
                "is_overhang": is_overhang,
            }

        return card

    def _build_design_check_section(self) -> QFrame:
        dc_schema = self.schema.get("design_check_card", {})
        card = self._create_card_frame()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)
        card_layout.addWidget(self._create_label(dc_schema.get("title", "Design Check:")))

        self.design_check_text = QTextEdit()
        self.design_check_text.setReadOnly(True)
        self.design_check_text.setMinimumHeight(200)
        self.design_check_text.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding,
        )
        self.design_check_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-size: 11px;
                color: #333333;
            }
        """)
        card_layout.addWidget(self.design_check_text)
        return card

    @staticmethod
    def _text_to_html(text: str) -> str:
        lines = []
        for line in text.split("\n"):
            esc = (line
                   .replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;"))
            esc = esc.replace(
                "PASS",
                '<span style="color:#1a7a4a;font-weight:bold">PASS</span>',
            )
            esc = esc.replace(
                "FAIL",
                '<span style="color:#8b0000;font-weight:bold">FAIL</span>',
            )
            esc = esc.replace("&lt;sub&gt;", "<sub>")
            esc = esc.replace("&lt;/sub&gt;", "</sub>")
            
            lines.append(esc)
        return (
            "<pre style='font-family:monospace;font-size:11px;"
            "color:#333333;line-height:1.55;margin:0;'>"
            + "<br>".join(lines)
            + "</pre>"
        )

    def load_data(self, output_dict: dict) -> None:
        if not output_dict:
            return

        # ── Properties ───────────────────────────────────────────────────────
        prop_schema = self.schema.get("properties_card", {})
        for field_def in prop_schema.get("fields", []):
            data_key = field_def.get("data_key")
            if data_key and data_key in self._prop_fields:
                self._prop_fields[data_key].setText(str(output_dict.get(data_key, "")))

        # ── Reinforcement table ───────────────────────────────────────────────
        reinf_schema = self.schema.get("reinforcement_table", {})
        rows_def     = reinf_schema.get("rows", [])
        _DATA_KEYS   = ["bar_key", "spacing_key", "prov_key", "req_key", "cover_key", "d_key"]
        _FACE_TAG    = {"Bottom": " (bot)", "Top": " (top)"}
        _OPP_TAG     = {"Bottom": " (top)", "Top": " (bot)"}  # d is from the opposite (compression) face
        has_overhang = False

        for row, row_def in enumerate(rows_def):
            is_overhang = row_def.get("is_overhang", False)
            face        = row_def.get("face", "")

            if is_overhang:
                has_overhang = bool(output_dict.get(row_def.get("bar_key", ""), ""))
                self.rebar_table.setRowHidden(row, not has_overhang)
                if not has_overhang:
                    continue

            for col_offset, key_name in enumerate(_DATA_KEYS):
                data_key = row_def.get(key_name, "")
                raw      = output_dict.get(data_key, "") if data_key else ""
                if raw and col_offset == 4:       # cover: measured from the bar's own face
                    value = f"{raw}{_FACE_TAG.get(face, '')}"
                elif raw and col_offset == 5:     # d: measured from the opposite (compression) face
                    value = f"{raw}{_OPP_TAG.get(face, '')}"
                else:
                    value = str(raw)
                item = QTableWidgetItem(value)
                item.setFlags(Qt.ItemIsEnabled)
                item.setTextAlignment(Qt.AlignCenter)
                self.rebar_table.setItem(row, 3 + col_offset, item)

        n_visible = sum(1 for r in rows_def if not r.get("is_overhang", False)) + (1 if has_overhang else 0)
        self.rebar_table.setFixedHeight(
            self._REBAR_HEADER_HEIGHT + n_visible * self._REBAR_ROW_HEIGHT + 2
        )
        if hasattr(self, "_overhang_note"):
            self._overhang_note.setVisible(has_overhang)

        # ── Utilization bars ──────────────────────────────────────────────────
        for key, widgets in self._ur_widgets.items():
            if widgets["is_overhang"]:
                widgets["bar"].setVisible(has_overhang)

            raw = output_dict.get(key)
            if raw is None:
                widgets["bar"].set_value(0.0)
            else:
                widgets["bar"].set_value(float(raw) * 100.0)

        # ── Design check text ─────────────────────────────────────────────────
        dc_schema = self.schema.get("design_check_card", {})
        dc_key = dc_schema.get("data_key", "deck_design_check")
        raw_text = str(output_dict.get(dc_key, ""))
        
        if raw_text:
            self.design_check_text.setHtml(self._text_to_html(raw_text))
        else:
            self.design_check_text.clear()
