"""
database/database.py

Provides the DatabaseManager class, responsible for all SQLite database
interactions for the app application (schema creation
and CRUD operations on the contacts table).

This module contains no UI or controller logic, in accordance with the
MVC architecture used in this project.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from models.contact import Contact

DEFAULT_DB_PATH = Path(__file__).parent / "contacts.db"


class DatabaseManager:
    """
    Manages the SQLite connection and all CRUD operations for contacts.

    Attributes:
        db_path (Path): Filesystem path to the SQLite database file.
        connection (sqlite3.Connection): Active connection to the
            SQLite database.
    """

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        """
        Initialize the DatabaseManager, open a connection, and ensure
        the contacts table exists.

        Args:
            db_path (Path | str): Path to the SQLite database file.
                Defaults to ``database/contacts.db``.
        """
        self.db_path: Path = Path(db_path)
        self.connection: sqlite3.Connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self._create_table()

    def _create_table(self) -> None:
        """
        Create the ``contacts`` table if it does not already exist.

        Returns:
            None
        """
        query = """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                notes TEXT
            );
        """
        with self.connection:
            self.connection.execute(query)

    def add_contact(self, contact: Contact) -> int:
        """
        Insert a new contact into the database.

        Args:
            contact (Contact): The contact instance to persist. Its
                ``id`` field is ignored/overwritten.

        Returns:
            int: The auto-generated id assigned to the new contact.
        """
        query = """
            INSERT INTO contacts
                (first_name, last_name, phone, email, address, notes)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        with self.connection:
            cursor = self.connection.execute(query, contact.to_tuple())
            return int(cursor.lastrowid)

    def get_all_contacts(self) -> list[Contact]:
        """
        Retrieve every contact stored in the database.

        Returns:
            list[Contact]: A list of Contact instances ordered by
            last name, then first name.
        """
        query = """
            SELECT id, first_name, last_name, phone, email, address, notes
            FROM contacts
            ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE;
        """
        cursor = self.connection.execute(query)
        rows = cursor.fetchall()
        return [Contact.from_row(row) for row in rows]

    def get_contact_by_id(self, contact_id: int) -> Optional[Contact]:
        """
        Retrieve a single contact by its unique id.

        Args:
            contact_id (int): The id of the contact to retrieve.

        Returns:
            Optional[Contact]: The matching Contact instance, or
            ``None`` if no contact with that id exists.
        """
        query = """
            SELECT id, first_name, last_name, phone, email, address, notes
            FROM contacts
            WHERE id = ?;
        """
        cursor = self.connection.execute(query, (contact_id,))
        row = cursor.fetchone()
        return Contact.from_row(row) if row is not None else None

    def update_contact(self, contact: Contact) -> bool:
        """
        Update an existing contact's information.

        Args:
            contact (Contact): The contact instance containing updated
                field values. Its ``id`` must correspond to an existing
                record.

        Returns:
            bool: True if a record was updated, False if no contact
            with the given id was found.

        Raises:
            ValueError: If ``contact.id`` is ``None``.
        """
        if contact.id is None:
            raise ValueError("Cannot update a contact without an id.")

        query = """
            UPDATE contacts
            SET first_name = ?,
                last_name = ?,
                phone = ?,
                email = ?,
                address = ?,
                notes = ?
            WHERE id = ?;
        """
        with self.connection:
            cursor = self.connection.execute(
                query, (*contact.to_tuple(), contact.id)
            )
            return cursor.rowcount > 0

    def delete_contact(self, contact_id: int) -> bool:
        """
        Delete a contact from the database by its id.

        Args:
            contact_id (int): The id of the contact to delete.

        Returns:
            bool: True if a record was deleted, False if no contact
            with the given id was found.
        """
        query = "DELETE FROM contacts WHERE id = ?;"
        with self.connection:
            cursor = self.connection.execute(query, (contact_id,))
            return cursor.rowcount > 0

    def search_contacts(self, keyword: str) -> list[Contact]:
        """
        Search for contacts whose first name, last name, phone,
        email, address, or notes contain the given keyword.

        Args:
            keyword (str): The search term. Matching is case-insensitive
                and matches substrings anywhere in the relevant fields.

        Returns:
            list[Contact]: A list of matching Contact instances ordered
            by last name, then first name.
        """
        query = """
            SELECT id, first_name, last_name, phone, email, address, notes
            FROM contacts
            WHERE first_name LIKE ?
               OR last_name LIKE ?
               OR phone LIKE ?
               OR email LIKE ?
               OR address LIKE ?
               OR notes LIKE ?
            ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE;
        """
        pattern = f"%{keyword}%"
        params = (pattern,) * 6
        cursor = self.connection.execute(query, params)
        rows = cursor.fetchall()
        return [Contact.from_row(row) for row in rows]

    def close(self) -> None:
        """
        Close the underlying SQLite connection.

        Returns:
            None
        """
        self.connection.close()

    def __enter__(self) -> "DatabaseManager":
        """
        Enter the runtime context for use as a context manager.

        Returns:
            DatabaseManager: This instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the runtime context, ensuring the connection is closed.

        Args:
            exc_type: Exception type, if raised within the context.
            exc_val: Exception value, if raised within the context.
            exc_tb: Exception traceback, if raised within the context.

        Returns:
            None
        """
        self.close()
