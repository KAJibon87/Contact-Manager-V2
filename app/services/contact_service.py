# ============================================================
# contact_service.py
# PART 1 START
# ============================================================

"""
Service layer for Contact operations.

This class sits between the UI/Controller and Repository.

Responsibilities:
- Business logic
- Basic validation
- Calling repository methods
"""

from __future__ import annotations

from typing import List, Optional

from app.models.contact import Contact
from app.repositories.interfaces.contact_repository import ContactRepository


class ContactService:
    """
    Contact business service.
    """

    # --------------------------------------------------------
    # Constructor
    # --------------------------------------------------------
    def __init__(self, repository: ContactRepository):
        """
        Initialize service with repository.

        Args:
            repository (ContactRepository)
        """
        self.repository = repository

    # --------------------------------------------------------
    # Get All Contacts
    # --------------------------------------------------------
    def get_all(self) -> List[Contact]:
        """
        Return all contacts.
        """
        return self.repository.get_all()

    # --------------------------------------------------------
    # Get Contact By ID
    # --------------------------------------------------------
    def get_by_id(self, contact_id: int) -> Optional[Contact]:
        """
        Return a contact by ID.
        """
        return self.repository.get_by_id(contact_id)

    # --------------------------------------------------------
    # Add Contact
    # --------------------------------------------------------
    def add(self, contact: Contact) -> int:
        """
        Add a new contact after validation.
        """

        # First name is required
        if not contact.first_name.strip():
            raise ValueError("First name is required.")

        # Last name is required
        if not contact.last_name.strip():
            raise ValueError("Last name is required.")

        return self.repository.add(contact)

    # --------------------------------------------------------
    # Check Contact Exists
    # --------------------------------------------------------
    def exists(self, contact_id: int) -> bool:
        """
        Check whether a contact exists.
        """
        return self.repository.exists(contact_id)

# ============================================================
# PART 1 END
# ============================================================
# ============================================================
# contact_service.py
# PART 2 START
# ============================================================

    # --------------------------------------------------------
    # Update Contact
    # --------------------------------------------------------
    def update(self, contact: Contact) -> bool:
        """
        Update an existing contact.

        Args:
            contact (Contact): Updated contact object.

        Returns:
            bool: True if update successful.
        """

        # Contact ID is required
        if contact.id is None:
            raise ValueError("Contact ID is required.")

        # Contact must exist before updating
        if not self.repository.exists(contact.id):
            raise ValueError("Contact not found.")

        # First name validation
        if not contact.first_name.strip():
            raise ValueError("First name is required.")

        # Last name validation
        if not contact.last_name.strip():
            raise ValueError("Last name is required.")

        return self.repository.update(contact)

    # --------------------------------------------------------
    # Delete Contact
    # --------------------------------------------------------
    def delete(self, contact_id: int) -> bool:
        """
        Delete a contact.

        Args:
            contact_id (int)

        Returns:
            bool
        """

        # Check contact exists
        if not self.repository.exists(contact_id):
            return False

        return self.repository.delete(contact_id)

    # --------------------------------------------------------
    # Search Contacts
    # --------------------------------------------------------
    def search(self, keyword: str) -> List[Contact]:
        """
        Search contacts.

        Args:
            keyword (str)

        Returns:
            List[Contact]
        """

        # Remove leading/trailing spaces
        keyword = keyword.strip()

        # Empty keyword returns all contacts
        if not keyword:
            return self.repository.get_all()

        return self.repository.search(keyword)

# ============================================================
# PART 2 END
# ============================================================