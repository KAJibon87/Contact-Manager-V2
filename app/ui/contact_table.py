# ui/contact_table.py
"""
ui/contact_table.py

Defines the ContactTableWidget class, the view component responsible
for displaying the list of contacts in a table, in accordance with
the MVC architecture used in this project.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from models.contact import Contact


class ContactTableWidget(QTableWidget):
    """Table widget that displays a list of contacts."""

    COLUMN_HEADERS: list[str] = [
        "First Name", "Last Name", "Phone", "Email", "Address", "Notes",
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._configure_table()

    def _configure_table(self) -> None:
        self.setColumnCount(len(self.COLUMN_HEADERS))
        self.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def load_contacts(self, contacts: list[Contact]) -> None:
        self.setRowCount(0)
        for row_index, contact in enumerate(contacts):
            self.insertRow(row_index)
            values = [contact.first_name, contact.last_name, contact.phone,
                      contact.email, contact.address, contact.notes]
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column_index == 0:
                    item.setData(Qt.ItemDataRole.UserRole, contact.id)
                self.setItem(row_index, column_index, item)

    def get_selected_contact_id(self) -> Optional[int]:
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        item = self.item(row, 0)
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)