"""
controllers/contact_controller.py

Defines the ContactController class, which mediates between the UI
layer (views) and the data layer (DatabaseManager/Contact model) in
accordance with the MVC architecture used in this project.

The controller exposes Qt signals so that connected views can react
to data changes (e.g. refresh a table) without the controller needing
any direct knowledge of the UI widgets themselves.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal


from database.database import DatabaseManager
from models.contact import Contact


class ContactController(QObject):
    """
    Coordinates operations between the UI and the DatabaseManager.

    This controller performs input validation, delegates persistence
    to a DatabaseManager instance, and emits Qt signals so that any
    connected views can be notified of successful changes or errors.

    Signals:
        contacts_changed (): Emitted whenever the underlying contact
            data set changes (add, update, delete) so views can
            refresh themselves.
        error_occurred (str): Emitted with a human-readable message
            whenever an operation fails.
    """

    contacts_changed = Signal()
    error_occurred = Signal(str)

    def __init__(self, database_manager: DatabaseManager) -> None:
        """
        Initialize the controller with a database manager instance.

        Args:
            database_manager (DatabaseManager): The data-access object
                used to persist and retrieve contacts.
        """
        super().__init__()
        self._db: DatabaseManager = database_manager

    def add_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str = "",
        email: str = "",
        address: str = "",
        notes: str = "",
    ) -> Optional[Contact]:
        """
        Validate input and create a new contact record.

        Args:
            first_name (str): Contact's first name (required).
            last_name (str): Contact's last name (required).
            phone (str): Contact's phone number.
            email (str): Contact's email address.
            address (str): Contact's physical/mailing address.
            notes (str): Free-form notes about the contact.

        Returns:
            Optional[Contact]: The newly created Contact (with its
            assigned id) on success, or ``None`` if validation or
            persistence failed.
        """
        if not self._validate_required_fields(first_name, last_name):
            return None

        contact = Contact(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip(),
            email=email.strip(),
            address=address.strip(),
            notes=notes.strip(),
        )

        try:
            new_id = self._db.add_contact(contact)
            contact.id = new_id
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to add contact: {exc}")
            return None

        self.contacts_changed.emit()
        return contact

    def get_all_contacts(self) -> list[Contact]:
        """
        Retrieve every contact currently stored.

        Returns:
            list[Contact]: A list of all Contact instances. Returns
            an empty list if retrieval fails.
        """
        try:
            return self._db.get_all_contacts()
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to load contacts: {exc}")
            return []

    def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        """
        Retrieve a single contact by its unique id.

        Args:
            contact_id (int): The id of the contact to retrieve.

        Returns:
            Optional[Contact]: The matching Contact instance, or
            ``None`` if not found or on failure.
        """
        try:
            return self._db.get_contact_by_id(contact_id)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to retrieve contact: {exc}")
            return None

    def update_contact(
        self,
        contact_id: int,
        first_name: str,
        last_name: str,
        phone: str = "",
        email: str = "",
        address: str = "",
        notes: str = "",
    ) -> bool:
        """
        Validate input and update an existing contact record.

        Args:
            contact_id (int): The id of the contact to update.
            first_name (str): Contact's first name (required).
            last_name (str): Contact's last name (required).
            phone (str): Contact's phone number.
            email (str): Contact's email address.
            address (str): Contact's physical/mailing address.
            notes (str): Free-form notes about the contact.

        Returns:
            bool: True if the update succeeded, False if validation
            failed, the contact was not found, or an error occurred.
        """
        if not self._validate_required_fields(first_name, last_name):
            return False

        contact = Contact(
            id=contact_id,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip(),
            email=email.strip(),
            address=address.strip(),
            notes=notes.strip(),
        )

        try:
            success = self._db.update_contact(contact)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to update contact: {exc}")
            return False

        if not success:
            self.error_occurred.emit(
                f"No contact found with id {contact_id}."
            )
            return False

        self.contacts_changed.emit()
        return True

    def delete_contact(self, contact_id: int) -> bool:
        """
        Delete a contact by its unique id.

        Args:
            contact_id (int): The id of the contact to delete.

        Returns:
            bool: True if the deletion succeeded, False if the
            contact was not found or an error occurred.
        """
        try:
            success = self._db.delete_contact(contact_id)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to delete contact: {exc}")
            return False

        if not success:
            self.error_occurred.emit(
                f"No contact found with id {contact_id}."
            )
            return False

        self.contacts_changed.emit()
        return True

    def search_contacts(self, keyword: str) -> list[Contact]:
        """
        Search for contacts matching the given keyword.

        Args:
            keyword (str): The search term. An empty or whitespace-only
                keyword returns every contact.

        Returns:
            list[Contact]: A list of matching Contact instances.
            Returns an empty list on failure.
        """
        keyword = keyword.strip()
        if not keyword:
            return self.get_all_contacts()

        try:
            return self._db.search_contacts(keyword)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Search failed: {exc}")
            return []

    def _validate_required_fields(self, first_name: str, last_name: str) -> bool:
        """
        Validate that required contact fields are present.

        Args:
            first_name (str): Contact's first name.
            last_name (str): Contact's last name.

        Returns:
            bool: True if both fields contain non-whitespace text,
            False otherwise. Emits ``error_occurred`` when invalid.
        """
        if not first_name.strip() or not last_name.strip():
            self.error_occurred.emit(
                "First name and last name are required fields."
            )
            return False
        return True