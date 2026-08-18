"""
app/controllers/contact_controller.py

Thin controller mediating between the UI layer and the ContactService,
plus orchestration for CSV import/export and database backup/restore.

All contact business logic and validation still live in
ContactService. Import/export/backup use separate, focused services
(ImportExportService, BackupService) so this controller stays an
orchestrator, not a place where new logic accumulates.
"""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from app.models.contact import Contact
from app.services.backup_service import BackupService
from app.services.contact_service import ContactService
from app.services.import_export_service import ImportExportService


class ContactController(QObject):
    """
    Coordinates operations between the UI and the ContactService,
    plus CSV import/export and backup/restore.

    Signals:
        contacts_changed (): Emitted whenever the underlying contact
            data set changes (add, update, delete, import, restore)
            so views can refresh themselves.
        error_occurred (str): Emitted with a human-readable message
            whenever an operation fails.
        success_occurred (str): Emitted with a human-readable message
            whenever a non-critical operation succeeds (used for toast
            notifications instead of blocking dialogs).
    """

    contacts_changed = Signal()
    error_occurred = Signal(str)
    success_occurred = Signal(str)

    def __init__(self, service: ContactService) -> None:
        """
        Initialize the controller with a ContactService instance.

        Args:
            service (ContactService): The business-logic service used
                for all contact operations.
        """
        super().__init__()
        self._service: ContactService = service

    # ------------------------------------------------------------
    # Core CRUD (unchanged behavior)
    # ------------------------------------------------------------

    def add_contact(
            self,
            first_name: str,
            last_name: str,
            phone: str = "",
            email: str = "",
            address: str = "",
            notes: str = "",
            photo_path: str = "",
    ) -> Optional[Contact]:
        """
        Build a Contact from the given fields and ask the service to
        persist it.
        """
        contact = Contact(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip(),
            email=email.strip(),
            address=address.strip(),
            notes=notes.strip(),
            photo_path=photo_path.strip(),
        )

        try:
            new_id = self._service.add(contact)
        except ValueError as exc:
            self.error_occurred.emit(str(exc))
            return None
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to add contact: {exc}")
            return None

        contact.id = new_id
        self.contacts_changed.emit()
        return contact

    def get_all_contacts(self) -> List[Contact]:
        """Retrieve every contact currently stored."""
        try:
            return self._service.get_all()
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to load contacts: {exc}")
            return []

    def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        """Retrieve a single contact by its unique id."""
        try:
            return self._service.get_by_id(contact_id)
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
            photo_path: str = "",
    ) -> bool:
        """
        Build a Contact from the given fields and ask the service to
        update the existing record.
        """
        contact = Contact(
            id=contact_id,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip(),
            email=email.strip(),
            address=address.strip(),
            notes=notes.strip(),
            photo_path=photo_path.strip(),
        )

        try:
            success = self._service.update(contact)
        except ValueError as exc:
            self.error_occurred.emit(str(exc))
            return False
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Failed to update contact: {exc}")
            return False

        if success:
            self.contacts_changed.emit()
        return success

    def delete_contact(self, contact_id: int) -> bool:
        """Delete a contact by its unique id."""
        try:
            success = self._service.delete(contact_id)
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

    def search_contacts(self, keyword: str) -> List[Contact]:
        """Search for contacts matching the given keyword."""
        try:
            return self._service.search(keyword)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Search failed: {exc}")
            return []

    # ------------------------------------------------------------
    # Duplicate detection (new)
    # ------------------------------------------------------------

    def find_duplicate(
        self, phone: str, email: str
    ) -> Optional[Contact]:
        """
        Check whether an existing contact already has the given phone
        number or email address.

        Args:
            phone (str): Phone number to check (ignored if blank).
            email (str): Email address to check (ignored if blank).

        Returns:
            Optional[Contact]: The first matching existing contact, or
            ``None`` if no match is found or both inputs are blank.
        """
        phone = phone.strip()
        email = email.strip().lower()
        if not phone and not email:
            return None

        for contact in self.get_all_contacts():
            phone_match = bool(phone) and contact.phone.strip() == phone
            email_match = (
                bool(email) and contact.email.strip().lower() == email
            )
            if phone_match or email_match:
                return contact
        return None

    # ------------------------------------------------------------
    # CSV import / export (new)
    # ------------------------------------------------------------

    def export_contacts_to_csv(self, file_path: str) -> None:
        """
        Export every contact to a CSV file.

        Args:
            file_path (str): Destination CSV file path.

        Returns:
            None
        """
        try:
            contacts = self._service.get_all()
            count = ImportExportService.export_to_csv(contacts, file_path)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Export failed: {exc}")
            return

        self.success_occurred.emit(f"Exported {count} contact(s) to CSV.")

    def import_contacts_from_csv(self, file_path: str) -> None:
        """
        Import contacts from a CSV file. Rows matching an existing
        contact's phone or email are skipped (not overwritten).

        Args:
            file_path (str): Source CSV file path.

        Returns:
            None
        """
        try:
            rows = ImportExportService.import_from_csv(file_path)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Import failed: {exc}")
            return

        added = 0
        skipped = 0

        for row in rows:
            duplicate = self.find_duplicate(row["phone"], row["email"])
            if duplicate is not None:
                skipped += 1
                continue

            contact = Contact(
                first_name=row["first_name"],
                last_name=row["last_name"],
                phone=row["phone"],
                email=row["email"],
                address=row["address"],
                notes=row["notes"],
            )
            try:
                self._service.add(contact)
                added += 1
            except ValueError:
                skipped += 1

        self.contacts_changed.emit()
        self.success_occurred.emit(
            f"Import complete: {added} added, {skipped} skipped "
            f"(duplicates or invalid rows)."
        )

    # ------------------------------------------------------------
    # Backup / restore (new)
    # ------------------------------------------------------------

    def _get_database_path(self) -> Optional[str]:
        """
        Retrieve the live SQLite database file path from the
        underlying repository, if it exposes one.

        Returns:
            Optional[str]: The database file path, or ``None`` if the
            repository does not expose it (e.g. a future non-SQLite
            repository implementation).
        """
        repository = getattr(self._service, "repository", None)
        connection_manager = getattr(repository, "db", None)
        get_path = getattr(connection_manager, "get_database_path", None)
        if callable(get_path):
            return str(get_path())
        return None

    def backup_database(self, destination_dir: str) -> None:
        """
        Create a timestamped backup of the live database file.

        Args:
            destination_dir (str): Directory to place the backup in.

        Returns:
            None
        """
        db_path = self._get_database_path()
        if db_path is None:
            self.error_occurred.emit(
                "Backup is not supported by the current repository."
            )
            return

        try:
            backup_path = BackupService.create_backup(db_path, destination_dir)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Backup failed: {exc}")
            return

        self.success_occurred.emit(f"Backup created: {backup_path}")

    def restore_database(self, backup_path: str) -> None:
        """
        Restore the live database file from a backup file.

        Args:
            backup_path (str): Path to the backup file to restore
                from.

        Returns:
            None
        """
        db_path = self._get_database_path()
        if db_path is None:
            self.error_occurred.emit(
                "Restore is not supported by the current repository."
            )
            return

        try:
            BackupService.restore_backup(backup_path, db_path)
        except Exception as exc:  # noqa: BLE001
            self.error_occurred.emit(f"Restore failed: {exc}")
            return

        self.contacts_changed.emit()
        self.success_occurred.emit("Database restored from backup.")