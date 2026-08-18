"""
app/main.py

Application entry point for Contact Manager Pro V2.

Wires together the Repository → Service → Controller → UI stack:

    SqliteContactRepository (implements ContactRepository, manages its
    own SQLiteConnection internally)
        -> ContactService
            -> ContactController
                -> MainWindow

Then starts the PySide6 event loop.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config.settings import get_settings
from app.controllers.contact_controller import ContactController
from app.repositories.sqlite.sqlite_contact_repository import (
    SQLiteContactRepository,
)
from app.services.contact_service import ContactService
from app.ui.main_window import MainWindow


class Application:
    """
    Bootstraps and runs the Contact Manager Pro V2 desktop application.

    Attributes:
        qt_app (QApplication): The underlying Qt application instance.
        repository (SQLiteContactRepository): Concrete data-access
            implementation for contacts. Manages its own SQLite
            connection internally (opened/closed per operation).
        service (ContactService): Business-logic layer for contacts.
        controller (ContactController): Mediates between the UI and
            the service layer.
        main_window (MainWindow): The application's top-level window.
    """

    def __init__(self, argv: list[str]) -> None:
        """
        Initialize the Qt application and construct every layer of
        the architecture, from the repository up to the UI.

        Args:
            argv (list[str]): Command-line arguments passed to the
                underlying QApplication (typically ``sys.argv``).
        """
        self.qt_app: QApplication = QApplication(argv)

        # Ensures data/exports/backups/logs directories exist.
        # NOTE: SQLiteConnection's default db path (app/data/contacts.db)
        # is currently independent of settings.paths.database_file
        # (project_root/data/contacts.db) — see the note below.
        get_settings()

        self.repository: SQLiteContactRepository = SQLiteContactRepository()
        self.service: ContactService = ContactService(self.repository)
        self.controller: ContactController = ContactController(self.service)
        self.main_window: MainWindow = MainWindow(self.controller)

    def run(self) -> int:
        """
        Show the main window and start the Qt event loop.

        Returns:
            int: The application's exit code.
        """
        self.main_window.show()
        return self.qt_app.exec()


def main() -> int:
    """
    Create and run the Contact Manager Pro V2 application.

    Returns:
        int: The process exit code, suitable for passing to
        ``sys.exit``.
    """
    app = Application(sys.argv)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())


