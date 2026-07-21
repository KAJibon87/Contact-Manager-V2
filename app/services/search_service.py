# services/search_service.py
"""
services/search_service.py

Defines the SearchService class, which provides in-memory search and
filtering logic over a list of Contact instances.
"""

from __future__ import annotations

from models.contact import Contact


class SearchService:
    """Provides keyword-based filtering over an in-memory list of contacts."""

    @staticmethod
    def filter_contacts(contacts: list[Contact], keyword: str) -> list[Contact]:
        keyword = keyword.strip().lower()
        if not keyword:
            return list(contacts)
        return [c for c in contacts if SearchService._matches(c, keyword)]

    @staticmethod
    def _matches(contact: Contact, keyword: str) -> bool:
        searchable_fields = (
            contact.first_name, contact.last_name, contact.phone,
            contact.email, contact.address, contact.notes,
        )
        return any(keyword in field.lower() for field in searchable_fields)

    @staticmethod
    def sort_by_name(contacts: list[Contact]) -> list[Contact]:
        return sorted(contacts, key=lambda c: (c.last_name.lower(), c.first_name.lower()))