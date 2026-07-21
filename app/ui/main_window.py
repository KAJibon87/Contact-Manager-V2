"""
ui/main_window.py

Defines the MainWindow class, the top-level view of the Mini Contact
Manager application. It composes the search bar, the contact table
(ui.contact_table.ContactTableWidget) and the add/edit dialog
(ui.contact_form.ContactFormDialog), and delegates all data operations
to a ContactController instance, in accordance with the MVC
architecture used in this project.

This module contains no direct database access — all persistence is
routed through the injected ContactController.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

sys.path.append(str(Path(__file__).resolve().parent.parent))

from controllers.contact_controller import ContactController
from models.contact import Contact
from ui.contact_form import ContactFormDialog
from ui.contact_table import ContactTableWidget


class MainWindow(QMainWindow):
    """
    Top-level application window for app.

    Composes a search bar, a contact table, and action buttons
    (Add, Edit, Delete, Refresh), and coordinates user interaction
    with the ContactController.

    Attributes:
        controller (ContactController): Handles validation and
            persistence for all contact operations.
        search_input (QLineEdit): Text field used to filter contacts.
        contact_table (ContactTableWidget): Widget displaying the
            list of contacts.
        add_button (QPushButton): Button that opens the add-contact
            dialog.
        edit_button (QPushButton): Button that opens the edit-contact
            dialog for the selected row.
        delete_button (QPushButton): Button that deletes the selected
            contact.
        refresh_button (QPushButton): Button that reloads the full
            contact list.
    """

    WINDOW_TITLE: str = "app"
    DEFAULT_WIDTH: int = 800
    DEFAULT_HEIGHT: int = 500

    def __init__(
        self,
        controller: ContactController,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the main window and build its UI.

        Args:
            controller (ContactController): The controller instance
                used for all contact data operations.
            parent (Optional[QWidget]): Optional parent widget.
        """
        super().__init__(parent)
        self.controller: ContactController = controller

        self.search_input: QLineEdit
        self.contact_table: ContactTableWidget
        self.add_button: QPushButton
        self.edit_button: QPushButton
        self.delete_button: QPushButton
        self.refresh_button: QPushButton

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self.load_contacts()

    def _setup_window(self) -> None:
        """
        Configure basic window properties (title and size).

        Returns:
            None
        """
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    def _setup_ui(self) -> None:
        """
        Build and arrange all child widgets and layouts.

        Returns:
            None
        """
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)

        main_layout.addLayout(self._build_search_bar())

        self.contact_table = ContactTableWidget(central_widget)
        main_layout.addWidget(self.contact_table)

        main_layout.addLayout(self._build_action_bar())

        self.setCentralWidget(central_widget)

    def _build_search_bar(self) -> QHBoxLayout:
        """
        Build the search bar layout.

        Returns:
            QHBoxLayout: A layout containing the search input field.
        """
        layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search contacts by name, phone, email, address, or notes..."
        )
        layout.addWidget(self.search_input)
        return layout

    def _build_action_bar(self) -> QHBoxLayout:
        """
        Build the action button bar layout.

        Returns:
            QHBoxLayout: A layout containing the Add, Edit, Delete,
            and Refresh buttons.
        """
        layout = QHBoxLayout()

        self.add_button = QPushButton("Add Contact")
        self.edit_button = QPushButton("Edit Contact")
        self.delete_button = QPushButton("Delete Contact")
        self.refresh_button = QPushButton("Refresh")

        layout.addWidget(self.add_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)
        layout.addStretch()
        layout.addWidget(self.refresh_button)

        return layout

    def _connect_signals(self) -> None:
        """
        Connect widget signals and controller signals to their
        corresponding handler methods.

        Returns:
            None
        """
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.add_button.clicked.connect(self._on_add_clicked)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.refresh_button.clicked.connect(self.load_contacts)

        self.controller.contacts_changed.connect(self.load_contacts)
        self.controller.error_occurred.connect(self._show_error)

    def load_contacts(self) -> None:
        """
        Load and display every contact from the controller.

        Returns:
            None
        """
        contacts: list[Contact] = self.controller.get_all_contacts()
        self.contact_table.load_contacts(contacts)

    def _on_search_text_changed(self, text: str) -> None:
        """
        Filter the contact table based on the current search text.

        Args:
            text (str): The current text of the search input field.

        Returns:
            None
        """
        contacts: list[Contact] = self.controller.search_contacts(text)
        self.contact_table.load_contacts(contacts)

    def _on_add_clicked(self) -> None:
        """
        Open the add-contact dialog and persist the new contact if
        the dialog is accepted.

        Returns:
            None
        """
        dialog = ContactFormDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_contact_data()
            self.controller.add_contact(
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                phone=data.get("phone", ""),
                email=data.get("email", ""),
                address=data.get("address", ""),
                notes=data.get("notes", ""),
            )

    def _on_edit_clicked(self) -> None:
        """
        Open the edit-contact dialog for the currently selected
        contact and persist changes if the dialog is accepted.

        Returns:
            None
        """
        contact_id = self.contact_table.get_selected_contact_id()
        if contact_id is None:
            self._show_error("Please select a contact to edit.")
            return

        contact = self.controller.get_contact_by_id(contact_id)
        if contact is None:
            self._show_error("Selected contact could not be found.")
            return

        dialog = ContactFormDialog(contact=contact, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_contact_data()
            self.controller.update_contact(
                contact_id=contact_id,
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                phone=data.get("phone", ""),
                email=data.get("email", ""),
                address=data.get("address", ""),
                notes=data.get("notes", ""),
            )

    def _on_delete_clicked(self) -> None:
        """
        Delete the currently selected contact after user confirmation.

        Returns:
            None
        """
        contact_id = self.contact_table.get_selected_contact_id()
        if contact_id is None:
            self._show_error("Please select a contact to delete.")
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this contact?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation == QMessageBox.StandardButton.Yes:
            self.controller.delete_contact(contact_id)

    def _show_error(self, message: str) -> None:
        """
        Display an error message to the user in a modal dialog.

        Args:
            message (str): The error message to display.

        Returns:
            None
        """
        QMessageBox.critical(self, "Error", message)