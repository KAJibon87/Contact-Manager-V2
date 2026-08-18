"""
app/services/import_export_service.py

CSV import/export logic for contacts. Pure I/O + parsing — no
persistence decisions and no UI code. The controller decides what to
do with the rows this service returns/writes.
"""

from __future__ import annotations

import csv
from typing import Any, Dict, List

from app.models.contact import Contact

CSV_FIELDS: List[str] = [
    "first_name",
    "last_name",
    "phone",
    "email",
    "address",
    "notes",
]


class ImportExportService:
    """
    Provides CSV export and import for Contact records.
    """

    @staticmethod
    def export_to_csv(contacts: List[Contact], file_path: str) -> int:
        """
        Write the given contacts to a CSV file.

        Args:
            contacts (List[Contact]): Contacts to export.
            file_path (str): Destination CSV file path.

        Returns:
            int: Number of rows written.
        """
        with open(file_path, mode="w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for contact in contacts:
                writer.writerow(
                    {
                        "first_name": contact.first_name,
                        "last_name": contact.last_name,
                        "phone": contact.phone,
                        "email": contact.email,
                        "address": contact.address,
                        "notes": contact.notes,
                    }
                )
        return len(contacts)

    @staticmethod
    def import_from_csv(file_path: str) -> List[Dict[str, Any]]:
        """
        Read contact rows from a CSV file.

        Expected header: first_name,last_name,phone,email,address,notes.
        Missing columns default to an empty string.

        Args:
            file_path (str): Source CSV file path.

        Returns:
            List[Dict[str, Any]]: Raw row dictionaries, one per data
            row, ready to be turned into Contact objects by the
            caller.
        """
        rows: List[Dict[str, Any]] = []
        with open(file_path, mode="r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(
                    {
                        "first_name": (row.get("first_name") or "").strip(),
                        "last_name": (row.get("last_name") or "").strip(),
                        "phone": (row.get("phone") or "").strip(),
                        "email": (row.get("email") or "").strip(),
                        "address": (row.get("address") or "").strip(),
                        "notes": (row.get("notes") or "").strip(),
                    }
                )
        return rows