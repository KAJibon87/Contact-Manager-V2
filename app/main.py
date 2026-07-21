"""
main.py

Application entry point for app. Wires together the
DatabaseManager, ContactController, and MainWindow, then starts the
PySide6 event loop, in accordance with the MVC architecture used in
this project.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from controllers.contact_controller import ContactController
from database.database import DatabaseManager
from ui.main_window import MainWindow


class Application:
    """
    Bootstraps and runs the app desktop application.

    Attributes:
        qt_app (QApplication): The underlying Qt application instance.
        db_manager (DatabaseManager): Handles SQLite persistence.
        controller (ContactController): Mediates between the UI and
            the database layer.
        main_window (MainWindow): The application's top-level window.
    """

    def __init__(self, argv: list[str]) -> None:
        """
        Initialize the Qt application and construct the MVC layers.

        Args:
            argv (list[str]): Command-line arguments passed to the
                underlying QApplication (typically ``sys.argv``).
        """
        self.qt_app: QApplication = QApplication(argv)
        self.db_manager: DatabaseManager = DatabaseManager()
        self.controller: ContactController = ContactController(self.db_manager)
        self.main_window: MainWindow = MainWindow(self.controller)

    def run(self) -> int:
        """
        Show the main window and start the Qt event loop.

        Returns:
            int: The application's exit code.
        """
        self.main_window.show()
        exit_code = self.qt_app.exec()
        self.db_manager.close()
        return exit_code


def main() -> int:
    """
    Create and run the app application.

    Returns:
        int: The process exit code, suitable for passing to
        ``sys.exit``.
    """
    app = Application(sys.argv)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())