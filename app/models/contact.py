"""
models/contact.py

Defines the Contact data model used throughout the app
application. This class represents a single contact record and provides
helper methods for converting to/from SQLite rows and dictionaries.

This module contains no database or UI logic (pure data model), in
accordance with the MVC architecture used in this project.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


@dataclass
class Contact:
    """
    Represents a single contact entry.

    Attributes:
        id (Optional[int]): Unique identifier of the contact in the
            database. ``None`` for a contact that has not yet been
            persisted.
        first_name (str): Contact's first name.
        last_name (str): Contact's last name.
        phone (str): Contact's phone number.
        email (str): Contact's email address.
        address (str): Contact's physical/mailing address.
        notes (str): Free-form notes about the contact.
    """

    first_name: str
    last_name: str
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""
    id: Optional[int] = field(default=None)

    @property
    def full_name(self) -> str:
        """
        Return the contact's full name.

        Returns:
            str: The concatenation of first and last name, separated
            by a single space, with surrounding whitespace stripped.
        """
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self) -> dict[str, Any]:
        """
        Convert this Contact instance into a plain dictionary.

        Returns:
            dict[str, Any]: A dictionary representation of the contact,
            suitable for serialization or passing to the database layer.
        """
        return asdict(self)

    def to_tuple(self) -> tuple[str, str, str, str, str, str]:
        """
        Convert this Contact instance into a tuple of field values,
        excluding the id, in the order expected by SQL INSERT/UPDATE
        statements.

        Returns:
            tuple[str, str, str, str, str, str]: A tuple containing
            (first_name, last_name, phone, email, address, notes).
        """
        return (
            self.first_name,
            self.last_name,
            self.phone,
            self.email,
            self.address,
            self.notes,
        )

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Contact":
        """
        Create a Contact instance from a dictionary.

        Args:
            data (dict[str, Any]): A dictionary containing contact
                field values. Missing optional fields default to
                empty strings or ``None``.

        Returns:
            Contact: A new Contact instance populated from the given
            dictionary.
        """
        return Contact(
            id=data.get("id"),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            address=data.get("address", ""),
            notes=data.get("notes", ""),
        )

    @staticmethod
    def from_row(row: tuple[Any, ...]) -> "Contact":
        """
        Create a Contact instance from a raw SQLite row tuple.

        The expected row column order is:
        (id, first_name, last_name, phone, email, address, notes)

        Args:
            row (tuple[Any, ...]): A tuple representing a single row
                fetched from the ``contacts`` SQLite table.

        Returns:
            Contact: A new Contact instance populated from the row.

        Raises:
            ValueError: If the row does not contain exactly 7 fields.
        """
        if len(row) != 7:
            raise ValueError(
                f"Expected 7 columns in row, got {len(row)}: {row}"
            )

        (
            contact_id,
            first_name,
            last_name,
            phone,
            email,
            address,
            notes,
        ) = row

        return Contact(
            id=contact_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            address=address,
            notes=notes,
        )

    @property
    def __str__(self) -> str:
        """
        Return a human-readable string representation of the contact.

        Returns:
            str: The contact's full name and phone number.
        """
        return f"{self.full_name} ({self.phone})"