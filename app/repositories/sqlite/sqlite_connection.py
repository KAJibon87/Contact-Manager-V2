"""
sqlite_connection.py

SQLite connection manager for Contact Manager Pro V2.

Responsibilities:
- Create SQLite connections
- Initialize database schema
- Migrate existing databases when new columns are added
- Enable foreign key support
- Keep database access centralized
- Resolve the correct database path whether running from source or
  as a PyInstaller-built/installed executable

Future migration:
Only this file needs to change when moving from SQLite
to PostgreSQL/MySQL.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional


class SQLiteConnection:
    """
    Central SQLite connection manager.

    This class is responsible for opening database connections and
    ensuring the required schema exists (including migrating
    already-existing databases when new columns are introduced).
    """

    DEFAULT_DB_NAME = "contacts.db"

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialize the connection manager.

        Args:
            db_path:
                Optional custom database path.
                If None, resolves a default path automatically (see
                _resolve_default_db_path).
        """

        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = self._resolve_default_db_path()

        self._initialize_schema()
        self._migrate_schema()

    def _resolve_default_db_path(self) -> Path:
        """
        Resolve the default database file path, working correctly
        both when running from source and when packaged/installed as
        a PyInstaller executable.

        When frozen, data is stored under the user's
        %LOCALAPPDATA%\\ContactManagerProV2 folder (always writable by
        the current user, regardless of where the .exe itself is
        installed — e.g. Program Files, which standard users cannot
        write to).

        Returns:
            Path: The resolved database file path.
        """
        if getattr(sys, "frozen", False):
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                app_root = Path(local_app_data) / "ContactManagerProV2"
            else:
                app_root = Path.home() / "ContactManagerProV2"
        else:
            # Running from source: app/repositories/sqlite -> app
            app_root = Path(__file__).resolve().parents[2]

        data_dir = app_root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        return data_dir / self.DEFAULT_DB_NAME

    def _initialize_schema(self) -> None:
        """
        Create the contacts table if it does not already exist.

        Called once at construction time so that every repository
        method can safely assume the table is present.
        """

        connection = sqlite3.connect(self.db_path)

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                notes TEXT
            )
            """
        )

        connection.commit()
        connection.close()

    def _migrate_schema(self) -> None:
        """
        Add columns introduced after the initial schema to any
        pre-existing database file, without touching existing rows.

        Safe to call on every startup: each ALTER TABLE is wrapped so
        an already-present column is silently skipped.

        Returns:
            None
        """
        connection = sqlite3.connect(self.db_path)

        migrations = [
            "ALTER TABLE contacts ADD COLUMN photo_path TEXT DEFAULT ''",
        ]

        for statement in migrations:
            try:
                connection.execute(statement)
                connection.commit()
            except sqlite3.OperationalError:
                # Column already exists — this migration already ran.
                pass

        connection.close()

    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a SQLite connection.
        """

        connection = sqlite3.connect(self.db_path)

        # Access columns by name
        connection.row_factory = sqlite3.Row

        # Enable Foreign Keys
        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def database_exists(self) -> bool:
        """
        Returns:
            True if database file exists.
        """
        return self.db_path.exists()

    def get_database_path(self) -> Path:
        """
        Returns:
            Current database path.
        """
        return self.db_path

    def close_connection(self, connection: sqlite3.Connection) -> None:
        """
        Safely close a SQLite connection.
        """

        if connection:
            connection.close()