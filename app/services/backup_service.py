"""
app/services/backup_service.py

Manual database backup and restore for the SQLite data file. Pure
file operations — no business logic, no UI code.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


class BackupService:
    """
    Provides manual backup and restore of a SQLite database file.
    """

    @staticmethod
    def create_backup(db_path: str, destination_dir: str) -> str:
        """
        Copy the live database file into a timestamped backup file.

        Args:
            db_path (str): Path to the live SQLite database file.
            destination_dir (str): Directory to place the backup in.

        Returns:
            str: The full path of the created backup file.

        Raises:
            FileNotFoundError: If ``db_path`` does not exist.
        """
        source = Path(db_path)
        if not source.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        dest_dir = Path(destination_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = dest_dir / f"contacts_backup_{timestamp}.db"

        shutil.copy2(source, backup_path)
        return str(backup_path)

    @staticmethod
    def restore_backup(backup_path: str, db_path: str) -> None:
        """
        Restore the live database file from a backup file, overwriting
        the current data.

        Args:
            backup_path (str): Path to the backup file to restore
                from.
            db_path (str): Path to the live SQLite database file to
                overwrite.

        Raises:
            FileNotFoundError: If ``backup_path`` does not exist.
        """
        source = Path(backup_path)
        if not source.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        shutil.copy2(source, Path(db_path))