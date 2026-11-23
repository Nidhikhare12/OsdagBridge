"""
Multi-select dual-list dialog for picking
SAIL-approved plate thicknesses.

Extracted from girder_details_tab.py.

Usage:
    dlg = CustomMultiSelectDialog(
        title="Top Flange Thickness",
        selected_values=["10", "12"],
        allowed_values=["8", "10", "12", "16", "20"],
        parent=self,
    )
    if dlg.exec():
        values = dlg.selected_values()   # → ["10", "12"]
"""
from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QHBoxLayout, QLabel,
    QListWidget, QPushButton, QVBoxLayout, QWidget,
)

from osdagbridge.desktop.ui.utils.custom_titlebar import CustomTitleBar


class CustomMultiSelectDialog(QDialog):
    def __init__(
        self,
        title: str,
        selected_values: List[str],
        allowed_values: List[str],
        parent=None,
    ):
        super().__init__(parent)
        self._allowed_values = [str(v).strip() for v in allowed_values if str(v).strip()]
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        self.setMinimumSize(620, 520)
        self.setStyleSheet("QDialog { background: #ffffff; border: 1px solid #90AF13; }")

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(parent=self)
        self.title_bar.setTitle(title)
        root_layout.addWidget(self.title_bar)

        content = QWidget(self)
        content.setStyleSheet("background: #f3f3f3;")
        root_layout.addWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(18)

        # Available list
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        left_lbl = QLabel("Available")
        left_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1f1f1f;")
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.available_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c8c8c8; border-radius: 10px;"
            " font-size: 14px; color: #1f1f1f; padding: 4px; }"
        )
        left_col.addWidget(left_lbl)
        left_col.addWidget(self.available_list, 1)

        # Move buttons
        buttons_col = QVBoxLayout()
        buttons_col.setSpacing(10)
        buttons_col.addStretch(1)
        self.move_all_right_btn = self._move_btn(">>", primary=True)
        self.move_right_btn     = self._move_btn(">",  primary=False)
        self.move_left_btn      = self._move_btn("<",  primary=False)
        self.move_all_left_btn  = self._move_btn("<<", primary=True)
        for btn in (self.move_all_right_btn, self.move_right_btn,
                    self.move_left_btn, self.move_all_left_btn):
            buttons_col.addWidget(btn)
        buttons_col.addStretch(1)

        # Selected list
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        right_lbl = QLabel("Selected")
        right_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1f1f1f;")
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selected_list.setStyleSheet(
            "QListWidget { background: #ffffff; border: 1px solid #c8c8c8; border-radius: 10px;"
            " font-size: 14px; color: #1f1f1f; padding: 4px; }"
        )
        right_col.addWidget(right_lbl)
        right_col.addWidget(self.selected_list, 1)

        top_row.addLayout(left_col, 1)
        top_row.addLayout(buttons_col)
        top_row.addLayout(right_col, 1)
        layout.addLayout(top_row, 1)

        # Submit button
        submit_row = QHBoxLayout()
        submit_row.addStretch(1)
        submit_btn = QPushButton("Submit")
        submit_btn.setMinimumHeight(40)
        submit_btn.setMinimumWidth(220)
        submit_btn.setStyleSheet(
            "QPushButton { background: #90AF13; color: #ffffff;"
            " border: 1px solid #90AF13; border-radius: 10px;"
            " font-size: 14px; font-weight: 700; }"
            "QPushButton:hover   { background: #7f9d11; }"
            "QPushButton:pressed { background: #6f8b0f; }"
        )
        submit_btn.clicked.connect(self.accept)
        submit_row.addWidget(submit_btn)
        submit_row.addStretch(1)
        layout.addLayout(submit_row)

        # Populate lists
        selected  = [v for v in selected_values if v in self._allowed_values] or list(self._allowed_values)
        available = [v for v in self._allowed_values if v not in selected]
        self.available_list.addItems(available)
        self.selected_list.addItems(selected)

        # Wire move buttons
        self.move_all_right_btn.clicked.connect(self._move_all_right)
        self.move_right_btn.clicked.connect(self._move_selected_right)
        self.move_left_btn.clicked.connect(self._move_selected_left)
        self.move_all_left_btn.clicked.connect(self._move_all_left)

        self._refresh_button_states()
        self.available_list.itemSelectionChanged.connect(self._refresh_button_states)
        self.selected_list.itemSelectionChanged.connect(self._refresh_button_states)

    # ── Button factory ────────────────────────────────────────────────────────

    def _move_btn(self, text: str, primary: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumSize(84, 48)
        if primary:
            btn.setStyleSheet(
                "QPushButton { background: #90AF13; color: #ffffff; border: 1px solid #90AF13;"
                " border-radius: 10px; font-size: 18px; font-weight: 800; }"
                "QPushButton:hover   { background: #7f9d11; }"
                "QPushButton:pressed { background: #6f8b0f; }"
                "QPushButton:disabled { background: #d2d2d2; color: #8a8a8a; border-color: #d2d2d2; }"
            )
        else:
            btn.setStyleSheet(
                "QPushButton { background: #cfcfcf; color: #6b6b6b; border: 1px solid #cfcfcf;"
                " border-radius: 10px; font-size: 18px; font-weight: 800; }"
                "QPushButton:disabled { background: #dcdcdc; color: #9a9a9a; border-color: #dcdcdc; }"
            )
        return btn

    # ── Move logic ────────────────────────────────────────────────────────────

    def _move_selected_right(self) -> None:
        self._move_items(self.available_list, self.selected_list, selected_only=True)

    def _move_selected_left(self) -> None:
        self._move_items(self.selected_list, self.available_list, selected_only=True)

    def _move_all_right(self) -> None:
        self._move_items(self.available_list, self.selected_list, selected_only=False)

    def _move_all_left(self) -> None:
        self._move_items(self.selected_list, self.available_list, selected_only=False)

    def _move_items(self, source: QListWidget, target: QListWidget, selected_only: bool) -> None:
        rows = (
            sorted([source.row(i) for i in source.selectedItems()], reverse=True)
            if selected_only
            else list(range(source.count() - 1, -1, -1))
        )
        moved = []
        for row in rows:
            item = source.takeItem(row)
            if item is not None:
                moved.append(item.text())
        for text in moved:
            target.addItem(text)
        self._sort_list(self.available_list)
        self._sort_list(self.selected_list)
        self._refresh_button_states()

    def _sort_list(self, widget: QListWidget) -> None:
        values = [widget.item(i).text() for i in range(widget.count())]
        values.sort(key=lambda v: self._allowed_values.index(v) if v in self._allowed_values else 9999)
        widget.clear()
        widget.addItems(values)

    def _refresh_button_states(self) -> None:
        self.move_right_btn.setEnabled(bool(self.available_list.selectedItems()))
        self.move_left_btn.setEnabled(bool(self.selected_list.selectedItems()))
        self.move_all_right_btn.setEnabled(self.available_list.count() > 0)
        self.move_all_left_btn.setEnabled(self.selected_list.count() > 0)

    # ── Public API ────────────────────────────────────────────────────────────

    def selected_values(self) -> List[str]:
        return [self.selected_list.item(i).text() for i in range(self.selected_list.count())]