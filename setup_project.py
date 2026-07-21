#!/usr/bin/env python3
"""
setup_project.py

Creates the complete folder/file structure for the "app"
desktop application project. Does not overwrite existing files.

Usage:
    python setup_project.py
"""

from pathlib import Path
import sqlite3

PROJECT_ROOT = Path("app")

DIRECTORIES = [
    PROJECT_ROOT,
    PROJECT_ROOT / "models",
    PROJECT_ROOT / "database",
    PROJECT_ROOT / "ui",
    PROJECT_ROOT / "controllers",
    PROJECT_ROOT / "services",
    PROJECT_ROOT / "assets" / "icons",
    PROJECT_ROOT / "assets" / "images",
    PROJECT_ROOT / "backups",
    PROJECT_ROOT / "data" / "exports",
]

EMPTY_FILES = [
    PROJECT_ROOT / "main.py",
    PROJECT_ROOT / "requirements.txt",
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / ".gitignore",
    PROJECT_ROOT / "models" / "__init__.py",
    PROJECT_ROOT / "models" / "contact.py",
    PROJECT_ROOT / "database" / "__init__.py",
    PROJECT_ROOT / "database" / "database.py",
    PROJECT_ROOT / "ui" / "__init__.py",
    PROJECT_ROOT / "ui" / "main_window.py",
    PROJECT_ROOT / "ui" / "contact_form.py",
    PROJECT_ROOT / "ui" / "contact_table.py",
    PROJECT_ROOT / "controllers" / "__init__.py",
    PROJECT_ROOT / "controllers" / "contact_controller.py",
    PROJECT_ROOT / "services" / "__init__.py",
    PROJECT_ROOT / "services" / "search_service.py",
]

DATABASE_FILE = PROJECT_ROOT / "database" / "contacts.db"


def create_directories():
    created = []
    for directory in DIRECTORIES:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory))
    return created


def create_empty_files():
    created = []
    for file_path in EMPTY_FILES:
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
            created.append(str(file_path))
    return created


def create_database_file():
    created = []
    if not DATABASE_FILE.exists():
        DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DATABASE_FILE)
        connection.close()
        created.append(str(DATABASE_FILE))
    return created


def main():
    print("Setting up 'app' project structure...\n")

    created_dirs = create_directories()
    created_files = create_empty_files()
    created_db = create_database_file()

    print("Created Directories:")
    if created_dirs:
        for d in created_dirs:
            print(f"  [DIR]  {d}")
    else:
        print("  (none - all directories already exist)")

    print("\nCreated Files:")
    if created_files:
        for f in created_files:
            print(f"  [FILE] {f}")
    else:
        print("  (none - all files already exist)")

    print("\nCreated Database:")
    if created_db:
        for db in created_db:
            print(f"  [DB]   {db}")
    else:
        print("  (none - database file already exists)")

    print("\nProject setup complete.")


if __name__ == "__main__":
    main()
