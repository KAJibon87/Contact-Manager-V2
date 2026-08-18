"""
contact_repository.py

Defines the abstract repository contract for Contact persistence.

All concrete repository implementations (SQLite, PostgreSQL, MySQL, API, etc.)
must implement this interface.

This keeps the Service layer independent from the database engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.contact import Contact


class ContactRepository(ABC):
    """Abstract repository interface for Contact data."""

    @abstractmethod
    def get_all(self) -> List[Contact]:
        """Return all contacts."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, contact_id: int) -> Optional[Contact]:
        """Return a contact by its ID."""
        raise NotImplementedError

    @abstractmethod
    def search(self, keyword: str) -> List[Contact]:
        """Search contacts."""
        raise NotImplementedError

    @abstractmethod
    def add(self, contact: Contact) -> int:
        """
        Save a new contact.

        Returns:
            Newly created contact ID.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, contact: Contact) -> bool:
        """Update an existing contact."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, contact_id: int) -> bool:
        """Delete a contact."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, contact_id: int) -> bool:
        """Check whether a contact exists."""
        raise NotImplementedError