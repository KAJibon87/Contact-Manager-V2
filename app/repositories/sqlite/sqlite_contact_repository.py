"""
SQLite implementation of ContactRepository.

This class contains all database operations related to contacts.
It communicates directly with SQLite and converts database rows
into Contact objects.
"""

from __future__ import annotations


from typing import List, Optional

from app.models.contact import Contact
from app.repositories.interfaces.contact_repository import ContactRepository
from app.repositories.sqlite.sqlite_connection import SQLiteConnection


class SQLiteContactRepository(ContactRepository):
    """
    SQLite implementation of the Contact Repository.
    """

    def __init__(self):
        """
        Initialize the repository.

        Creates a SQLiteConnection object which will be reused
        for every database operation.
        """
        self.db = SQLiteConnection()

    def add(self, contact: Contact) -> int:
        """
        Insert a new contact into the database.

        Args:
            contact (Contact): Contact object.

        Returns:
            int:
                Newly inserted Contact ID.
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO contacts
            (
                first_name,
                last_name,
                phone,
                email,
                address,
                notes,
                photo_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            contact.to_tuple(),
        )

        conn.commit()

        contact_id = int(cursor.lastrowid or 0)

        conn.close()

        return contact_id

    def get_all(self) -> List[Contact]:
        """
        Retrieve every contact from database.

        Returns:
            List[Contact]
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                phone,
                email,
                address,
                notes,
                photo_path
            FROM contacts
            ORDER BY first_name ASC
            """
        )

        rows = cursor.fetchall()

        conn.close()

        contacts = []

        for row in rows:
            contacts.append(Contact.from_row(row))

        return contacts

    def get_by_id(self, contact_id: int) -> Optional[Contact]:
        """
        Find a contact by database ID.

        Args:
            contact_id (int)

        Returns:
            Contact | None
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                phone,
                email,
                address,
                notes,
                photo_path
            FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        )

        row = cursor.fetchone()

        conn.close()

        if row:
            return Contact.from_row(row)

        return None

    def exists(self, contact_id: int) -> bool:
        """
        Check whether a contact exists.

        Args:
            contact_id (int)

        Returns:
            bool
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM contacts
            WHERE id = ?
            LIMIT 1
            """,
            (contact_id,),
        )

        exists = cursor.fetchone() is not None

        conn.close()

        return exists

    def update(self, contact: Contact) -> bool:
        """
        Update an existing contact.

        Args:
            contact (Contact): Contact object with updated information.

        Returns:
            bool:
                True if update was successful.
                False if no record was updated.
        """

        if contact.id is None:
            return False

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE contacts
            SET
                first_name = ?,
                last_name = ?,
                phone = ?,
                email = ?,
                address = ?,
                notes = ?,
                photo_path = ?
            WHERE id = ?
            """,
            (
                contact.first_name,
                contact.last_name,
                contact.phone,
                contact.email,
                contact.address,
                contact.notes,
                contact.photo_path,
                contact.id,
            ),
        )

        conn.commit()

        updated = cursor.rowcount > 0

        conn.close()

        return updated

    def delete(self, contact_id: int) -> bool:
        """
        Delete a contact by ID.

        Args:
            contact_id (int)

        Returns:
            bool
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM contacts
            WHERE id = ?
            """,
            (contact_id,),
        )

        conn.commit()

        deleted = cursor.rowcount > 0

        conn.close()

        return deleted

    def search(self, keyword: str) -> List[Contact]:
        """
        Search contacts by name, phone or email.

        Args:
            keyword (str)

        Returns:
            List[Contact]
        """

        conn = self.db.get_connection()
        cursor = conn.cursor()

        search_text = f"%{keyword}%"

        cursor.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                phone,
                email,
                address,
                notes,
                photo_path
            FROM contacts
            WHERE
                first_name LIKE ?
                OR last_name LIKE ?
                OR phone LIKE ?
                OR email LIKE ?
            ORDER BY first_name ASC
            """,
            (
                search_text,
                search_text,
                search_text,
                search_text,
            ),
        )

        rows = cursor.fetchall()

        conn.close()

        contacts = []

        for row in rows:
            contacts.append(Contact.from_row(row))

        return contacts