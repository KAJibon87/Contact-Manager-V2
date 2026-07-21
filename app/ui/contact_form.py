# ui/contact_form.py
"""
ui/contact_form.py

Defines the ContactFormDialog class, the modal dialog used to add a
new contact or edit an existing one, in accordance with the MVC
architecture used in this project.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QTextEdit, QVBoxLayout, QWidget,
)

from models.contact import Contact


class ContactFormDialog(QDialog):
    """Modal dialog for creating or editing a contact."""

    def __init__(self, contact: Optional[Contact] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._contact: Optional[Contact] = contact

        self.first_name_input: QLineEdit
        self.last_name_input: QLineEdit
        self.phone_input: QLineEdit
        self.email_input: QLineEdit
        self.address_input: QLineEdit
        self.notes_input: QTextEdit
        self.button_box: QDialogButtonBox

        self._setup_window()
        self._setup_ui()
        self._connect_signals()

        if contact is not None:
            self._populate_fields(contact)

    def _setup_window(self) -> None:
        title = "Edit Contact" if self._contact is not None else "Add Contact"
        self.setWindowTitle(title)
        self.setModal(True)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(80)

        form_layout.addRow("First Name:", self.first_name_input)
        form_layout.addRow("Last Name:", self.last_name_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def _populate_fields(self, contact: Contact) -> None:
        self.first_name_input.setText(contact.first_name)
        self.last_name_input.setText(contact.last_name)
        self.phone_input.setText(contact.phone)
        self.email_input.setText(contact.email)
        self.address_input.setText(contact.address)
        self.notes_input.setPlainText(contact.notes)

    def get_contact_data(self) -> dict[str, Any]:
        return {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
        }