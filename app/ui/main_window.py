"""
app/ui/main_window.py

Top-level view of Contact Manager Pro V2: toolbar (contact actions,
CSV export/import, backup/restore, theme toggle), left sidebar
(All Contacts / Favorites / Recently Added, with live counts), search
bar, contact table, lightweight toast notifications, keyboard
shortcuts, and status bar. All data operations are delegated to the
injected ContactController — no business logic lives here.
"""

from __future__ import annotations

import re
from typing import Optional

from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtGui import QDesktopServices, QFont, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStyle,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.controllers.contact_controller import ContactController
from app.models.contact import Contact
from app.ui.contact_detail_dialog import ContactDetailDialog
from app.ui.contact_form import ContactFormDialog
from app.ui.contact_table import ContactTableWidget


class MainWindow(QMainWindow):
    """
    Top-level application window for Contact Manager Pro V2.
    """

    WINDOW_TITLE: str = "Contact Manager Pro V2"
    DEFAULT_WIDTH: int = 1180
    DEFAULT_HEIGHT: int = 680
    SIDEBAR_WIDTH: int = 220
    RECENT_LIMIT: int = 10

    def __init__(
        self,
        controller: ContactController,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the main window and build its UI.

        Args:
            controller (ContactController): The controller instance
                used for all contact data operations.
            parent (Optional[QWidget]): Optional parent widget.
        """
        super().__init__(parent)
        self.controller: ContactController = controller
        self._dark_mode: bool = False
        self._active_filter: str = "all"  # "all" | "favorites" | "recent"

        self.search_input: QLineEdit
        self.contact_table: ContactTableWidget
        self.add_button: QPushButton
        self.edit_button: QPushButton
        self.delete_button: QPushButton
        self.refresh_button: QPushButton
        self._toast_label: QLabel

        self._setup_window()
        self._apply_system_theme_if_available()
        self._apply_stylesheet()
        self._setup_toolbar()
        self._setup_ui()
        self._setup_toast()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._connect_signals()
        self.load_contacts()

    # ------------------------------------------------------------
    # Window / theme setup
    # ------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configure basic window properties (title, size, font)."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setFont(QFont("Segoe UI", 10))

    def _apply_system_theme_if_available(self) -> None:
        """
        Attempt to detect the OS-level light/dark preference (Qt 6.5+)
        and use it as the initial theme. Silently falls back to light
        mode if the API isn't available on the running Qt version.

        Returns:
            None
        """
        try:
            style_hints = QGuiApplication.styleHints()
            scheme = style_hints.colorScheme()
            self._dark_mode = scheme.name == "Dark"
        except AttributeError:
            self._dark_mode = False

    def _apply_stylesheet(self) -> None:
        """Apply the current theme's stylesheet."""
        self.setStyleSheet(
            self._dark_stylesheet() if self._dark_mode else self._light_stylesheet()
        )

    def _light_stylesheet(self) -> str:
        """Build the light theme stylesheet."""
        return """
            QMainWindow { background-color: #f3f3f3; }
            QToolBar {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
                padding: 6px;
                spacing: 6px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border-radius: 6px;
                padding: 6px 10px;
                color: #1a1a1a;
            }
            QToolBar QToolButton:hover { background-color: #e8f0fe; }
            QToolBar QToolButton:pressed { background-color: #d2e3fc; }
            #Sidebar {
                background-color: #ffffff;
                border-right: 1px solid #e0e0e0;
            }
            #SidebarTitle {
                color: #1a1a1a;
                font-size: 15px;
                font-weight: 600;
                padding: 18px 16px 6px 16px;
            }
            #SidebarSubtitle {
                color: #6b6b6b;
                font-size: 11px;
                padding: 0px 16px 14px 16px;
            }
            #SidebarNavItem {
                background-color: transparent;
                color: #1a1a1a;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 14px;
                font-weight: 600;
                font-size: 13px;
            }
            #SidebarNavItem:hover { background-color: #f0f0f0; }
            #SidebarNavItemActive {
                background-color: #eaf1fe;
                color: #0b57d0;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 14px;
                font-weight: 600;
                font-size: 13px;
            }
            #ContentArea { background-color: #f3f3f3; }
            #SearchInput {
                background-color: #ffffff;
                border: 1px solid #d6d6d6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1a1a1a;
            }
            #SearchInput:focus { border: 1px solid #0b57d0; }
            QPushButton {
                background-color: #0b57d0;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #0a47ab; }
            QPushButton:pressed { background-color: #083a8c; }
            #DeleteButton {
                background-color: #ffffff;
                color: #c5221f;
                border: 1px solid #e0a6a4;
            }
            #DeleteButton:hover { background-color: #fbe9e7; }
            #RefreshButton {
                background-color: #ffffff;
                color: #1a1a1a;
                border: 1px solid #d6d6d6;
            }
            #RefreshButton:hover { background-color: #f0f0f0; }
            #CallButton, #WhatsAppButton, #FavoriteButton, #CopyButton {
                background-color: #ffffff;
                border: 1px solid #d6d6d6;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
                color: #1a1a1a;
                font-weight: 500;
            }
            #CallButton:hover, #WhatsAppButton:hover, #FavoriteButton:hover, #CopyButton:hover {
                background-color: #f0f0f0;
            }
            #CallButton:disabled, #WhatsAppButton:disabled, #CopyButton:disabled {
                color: #bbbbbb;
                border: 1px solid #eeeeee;
            }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                gridline-color: #eeeeee;
                selection-background-color: #d2e3fc;
                selection-color: #1a1a1a;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #fafafa;
                color: #6b6b6b;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 10px;
                font-weight: 600;
                font-size: 12px;
            }
            QTableWidget::item { padding: 6px; }
            QStatusBar {
                background-color: #ffffff;
                border-top: 1px solid #e0e0e0;
                color: #6b6b6b;
                font-size: 12px;
            }
            #Toast {
                background-color: #1a1a1a;
                color: #ffffff;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
            }
        """

    def _dark_stylesheet(self) -> str:
        """Build the dark theme stylesheet."""
        return """
            QMainWindow { background-color: #1e1e1e; }
            QToolBar {
                background-color: #252526;
                border-bottom: 1px solid #3c3c3c;
                padding: 6px;
                spacing: 6px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                border-radius: 6px;
                padding: 6px 10px;
                color: #e6e6e6;
            }
            QToolBar QToolButton:hover { background-color: #37373d; }
            QToolBar QToolButton:pressed { background-color: #094771; }
            #Sidebar {
                background-color: #252526;
                border-right: 1px solid #3c3c3c;
            }
            #SidebarTitle {
                color: #e6e6e6;
                font-size: 15px;
                font-weight: 600;
                padding: 18px 16px 6px 16px;
            }
            #SidebarSubtitle {
                color: #9d9d9d;
                font-size: 11px;
                padding: 0px 16px 14px 16px;
            }
            #SidebarNavItem {
                background-color: transparent;
                color: #e6e6e6;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 14px;
                font-weight: 600;
                font-size: 13px;
            }
            #SidebarNavItem:hover { background-color: #2d2d30; }
            #SidebarNavItemActive {
                background-color: #094771;
                color: #cfe8ff;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 14px;
                font-weight: 600;
                font-size: 13px;
            }
            #ContentArea { background-color: #1e1e1e; }
            #SearchInput {
                background-color: #2d2d30;
                border: 1px solid #3c3c3c;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #e6e6e6;
            }
            #SearchInput:focus { border: 1px solid #3794ff; }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:pressed { background-color: #0a4d7a; }
            #DeleteButton {
                background-color: #2d2d30;
                color: #f48771;
                border: 1px solid #6b3a34;
            }
            #DeleteButton:hover { background-color: #3a2a28; }
            #RefreshButton {
                background-color: #2d2d30;
                color: #e6e6e6;
                border: 1px solid #3c3c3c;
            }
            #RefreshButton:hover { background-color: #37373d; }
            #CallButton, #WhatsAppButton, #FavoriteButton, #CopyButton {
                background-color: #2d2d30;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
                color: #e6e6e6;
                font-weight: 500;
            }
            #CallButton:hover, #WhatsAppButton:hover, #FavoriteButton:hover, #CopyButton:hover {
                background-color: #37373d;
            }
            #CallButton:disabled, #WhatsAppButton:disabled, #CopyButton:disabled {
                color: #6b6b6b;
                border: 1px solid #333333;
            }
            QTableWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 10px;
                gridline-color: #3c3c3c;
                selection-background-color: #094771;
                selection-color: #ffffff;
                font-size: 13px;
                color: #e6e6e6;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #9d9d9d;
                border: none;
                border-bottom: 1px solid #3c3c3c;
                padding: 10px;
                font-weight: 600;
                font-size: 12px;
            }
            QTableWidget::item { padding: 6px; }
            QStatusBar {
                background-color: #252526;
                border-top: 1px solid #3c3c3c;
                color: #9d9d9d;
                font-size: 12px;
            }
            #Toast {
                background-color: #3c3c3c;
                color: #ffffff;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
            }
        """

    def _toggle_theme(self) -> None:
        """Switch between light and dark mode and re-apply the stylesheet."""
        self._dark_mode = not self._dark_mode
        self._apply_stylesheet()
        self._theme_action.setText(
            "☀️ Light Mode" if self._dark_mode else "🌙 Dark Mode"
        )

    # ------------------------------------------------------------
    # Toolbar
    # ------------------------------------------------------------

    def _setup_toolbar(self) -> None:
        """
        Build the top toolbar: contact actions, CSV export/import,
        backup/restore, and the theme toggle.

        Returns:
            None
        """
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        style = self.style()

        self._add_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_FileIcon), "Add Contact"
        )
        self._edit_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView),
            "Edit Contact",
        )
        self._delete_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon),
            "Delete Contact",
        )
        toolbar.addSeparator()
        self._refresh_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Refresh"
        )
        toolbar.addSeparator()
        self._export_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            "Export CSV",
        )
        self._import_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            "Import CSV",
        )
        toolbar.addSeparator()
        self._backup_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DriveHDIcon), "Backup"
        )
        self._restore_action = toolbar.addAction(
            style.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton),
            "Restore",
        )
        toolbar.addSeparator()
        self._theme_action = toolbar.addAction(
            "☀️ Light Mode" if self._dark_mode else "🌙 Dark Mode"
        )

    # ------------------------------------------------------------
    # Main layout: sidebar + content
    # ------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build and arrange the sidebar and main content area."""
        central_widget = QWidget(self)
        central_widget.setObjectName("ContentArea")
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_content_area(), stretch=1)

        self.setCentralWidget(central_widget)

    def _build_sidebar(self) -> QFrame:
        """Build the left navigation sidebar."""
        sidebar = QFrame(self)
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(self.SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        title = QLabel("Contact Manager")
        title.setObjectName("SidebarTitle")
        subtitle = QLabel("Pro V2")
        subtitle.setObjectName("SidebarSubtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(12, 4, 12, 0)
        nav_layout.setSpacing(4)

        self._nav_all = QPushButton("All Contacts")
        self._nav_favorites = QPushButton("★ Favorites")
        self._nav_recent = QPushButton("Recently Added")

        for nav_button in (self._nav_all, self._nav_favorites, self._nav_recent):
            nav_button.setCursor(Qt.CursorShape.PointingHandCursor)
            nav_button.setFlat(True)
            nav_layout.addWidget(nav_button)

        self._nav_all.clicked.connect(lambda: self._set_filter("all"))
        self._nav_favorites.clicked.connect(lambda: self._set_filter("favorites"))
        self._nav_recent.clicked.connect(lambda: self._set_filter("recent"))

        layout.addWidget(nav_container)
        layout.addStretch()
        return sidebar

    def _build_content_area(self) -> QWidget:
        """Build the main content area: search bar, table, action buttons."""
        content = QWidget(self)
        content.setObjectName("ContentArea")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 12)
        layout.setSpacing(14)

        layout.addLayout(self._build_search_bar())

        self.contact_table = ContactTableWidget(content)
        layout.addWidget(self.contact_table, stretch=1)

        layout.addLayout(self._build_action_bar())

        return content

    def _build_search_bar(self) -> QHBoxLayout:
        """Build the search bar layout."""
        layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText(
            "🔍  Search contacts by name, phone, email, address, or notes..."
        )
        layout.addWidget(self.search_input)
        return layout

    def _build_action_bar(self) -> QHBoxLayout:
        """Build the action button bar layout."""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.add_button = QPushButton("Add Contact")
        self.edit_button = QPushButton("Edit Contact")
        self.delete_button = QPushButton("Delete Contact")
        self.delete_button.setObjectName("DeleteButton")
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("RefreshButton")

        for button in (
            self.add_button, self.edit_button, self.delete_button, self.refresh_button
        ):
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout.addWidget(self.add_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)
        layout.addStretch()
        layout.addWidget(self.refresh_button)

        return layout

    # ------------------------------------------------------------
    # Toast notifications
    # ------------------------------------------------------------

    def _setup_toast(self) -> None:
        """
        Create the (initially hidden) toast label used for
        non-blocking success notifications.

        Returns:
            None
        """
        self._toast_label = QLabel(self)
        self._toast_label.setObjectName("Toast")
        self._toast_label.hide()
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._toast_label.hide)

    def _show_toast(self, message: str) -> None:
        """
        Show a brief, non-blocking success notification near the
        bottom of the window.

        Args:
            message (str): The message to display.

        Returns:
            None
        """
        self._toast_label.setText(message)
        self._toast_label.adjustSize()
        x = (self.width() - self._toast_label.width()) // 2
        y = self.height() - self._toast_label.height() - 60
        self._toast_label.move(max(0, x), max(0, y))
        self._toast_label.show()
        self._toast_label.raise_()
        self._toast_timer.start(2500)

    # ------------------------------------------------------------
    # Status bar
    # ------------------------------------------------------------

    def _setup_status_bar(self) -> None:
        """Initialize the status bar shown at the bottom of the window."""
        self.statusBar().showMessage("Ready")

    def _update_status_bar(self, contact_count: int) -> None:
        """Update the status bar with the current contact count."""
        label = "contact" if contact_count == 1 else "contacts"
        self.statusBar().showMessage(f"{contact_count} {label}")

    def _update_sidebar_counts(self, all_contacts: list[Contact]) -> None:
        """
        Update the sidebar navigation labels with live counts.

        Args:
            all_contacts (list[Contact]): The full, unfiltered contact
                list currently loaded.

        Returns:
            None
        """
        favorites_count = sum(
            1 for c in all_contacts if self.contact_table.is_favorite(c.id)
        )
        recent_count = min(len(all_contacts), self.RECENT_LIMIT)

        self._nav_all.setText(f"All Contacts ({len(all_contacts)})")
        self._nav_favorites.setText(f"★ Favorites ({favorites_count})")
        self._nav_recent.setText(f"Recently Added ({recent_count})")

        active_map = {
            "all": self._nav_all,
            "favorites": self._nav_favorites,
            "recent": self._nav_recent,
        }
        for key, button in active_map.items():
            button.setObjectName(
                "SidebarNavItemActive" if key == self._active_filter else "SidebarNavItem"
            )
            button.style().unpolish(button)
            button.style().polish(button)

    # ------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        """
        Register keyboard shortcuts for common actions.

        Returns:
            None
        """
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._on_add_clicked)
        QShortcut(
            QKeySequence("Ctrl+F"), self, activated=self.search_input.setFocus
        )
        QShortcut(
            QKeySequence(Qt.Key.Key_Delete),
            self.contact_table,
            activated=self._on_delete_clicked,
        )

    # ------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Connect widget, toolbar, table, and controller signals."""
        self.search_input.textChanged.connect(self._on_search_text_changed)

        self.add_button.clicked.connect(self._on_add_clicked)
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.refresh_button.clicked.connect(self.load_contacts)

        self._add_action.triggered.connect(self._on_add_clicked)
        self._edit_action.triggered.connect(self._on_edit_clicked)
        self._delete_action.triggered.connect(self._on_delete_clicked)
        self._refresh_action.triggered.connect(self.load_contacts)
        self._theme_action.triggered.connect(self._toggle_theme)
        self._export_action.triggered.connect(self._on_export_csv)
        self._import_action.triggered.connect(self._on_import_csv)
        self._backup_action.triggered.connect(self._on_backup)
        self._restore_action.triggered.connect(self._on_restore)

        self.contact_table.call_requested.connect(self._on_call_requested)
        self.contact_table.whatsapp_requested.connect(self._on_whatsapp_requested)
        self.contact_table.favorite_changed.connect(self.load_contacts)
        self.contact_table.contact_double_clicked.connect(
            self._on_contact_double_clicked
        )

        self.controller.contacts_changed.connect(self.load_contacts)
        self.controller.error_occurred.connect(self._show_error)
        self.controller.success_occurred.connect(self._show_toast)

    # ------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------

    def _set_filter(self, filter_name: str) -> None:
        """
        Switch the active sidebar filter and reload the table.

        Args:
            filter_name (str): One of "all", "favorites", "recent".

        Returns:
            None
        """
        self._active_filter = filter_name
        self.load_contacts()

    def _apply_active_filter(self, contacts: list[Contact]) -> list[Contact]:
        """
        Apply the currently active sidebar filter to a contact list.

        Args:
            contacts (list[Contact]): The full contact list to filter.

        Returns:
            list[Contact]: The filtered contact list.
        """
        if self._active_filter == "favorites":
            return [c for c in contacts if self.contact_table.is_favorite(c.id)]
        if self._active_filter == "recent":
            sorted_contacts = sorted(
                contacts, key=lambda c: (c.id or 0), reverse=True
            )
            return sorted_contacts[: self.RECENT_LIMIT]
        return contacts

    # ------------------------------------------------------------
    # Data operations
    # ------------------------------------------------------------

    def load_contacts(self) -> None:
        """Load, filter, and display contacts from the controller."""
        all_contacts: list[Contact] = self.controller.get_all_contacts()
        visible_contacts = self._apply_active_filter(all_contacts)

        self.contact_table.load_contacts(visible_contacts)
        self._update_status_bar(len(visible_contacts))
        self._update_sidebar_counts(all_contacts)

    def _on_search_text_changed(self, text: str) -> None:
        """Filter the contact table based on the current search text."""
        contacts: list[Contact] = self.controller.search_contacts(text)
        filtered = self._apply_active_filter(contacts)
        self.contact_table.load_contacts(filtered)
        self._update_status_bar(len(filtered))

    def _on_add_clicked(self) -> None:
        """Open the add-contact dialog, checking for duplicates first."""
        dialog = ContactFormDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_contact_data()

            duplicate = self.controller.find_duplicate(
                data.get("phone", ""), data.get("email", "")
            )
            if duplicate is not None:
                confirmation = QMessageBox.question(
                    self,
                    "Possible Duplicate",
                    f"A contact with this phone or email already exists "
                    f"({duplicate.first_name} {duplicate.last_name}). "
                    f"Add this contact anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                if confirmation != QMessageBox.StandardButton.Yes:
                    return

            self.controller.add_contact(
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                phone=data.get("phone", ""),
                email=data.get("email", ""),
                address=data.get("address", ""),
                notes=data.get("notes", ""),
                photo_path=data.get("photo_path", ""),
            )
    def _on_edit_clicked(self) -> None:
        """Open the edit-contact dialog for the selected contact."""
        contact_id = self.contact_table.get_selected_contact_id()
        if contact_id is None:
            self._show_error("Please select a contact to edit.")
            return

        contact = self.controller.get_contact_by_id(contact_id)
        if contact is None:
            self._show_error("Selected contact could not be found.")
            return

        dialog = ContactFormDialog(contact=contact, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_contact_data()
            self.controller.update_contact(
                contact_id=contact_id,
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                phone=data.get("phone", ""),
                email=data.get("email", ""),
                address=data.get("address", ""),
                notes=data.get("notes", ""),
                photo_path=data.get("photo_path", ""),
            )

    def _on_contact_double_clicked(self, contact_id: int) -> None:
        """
        Open a read-only detail view for the double-clicked contact.

        Args:
            contact_id (int): The id of the contact to display.

        Returns:
            None
        """
        contact = self.controller.get_contact_by_id(contact_id)
        if contact is None:
            self._show_error("Selected contact could not be found.")
            return

        dialog = ContactDetailDialog(contact, parent=self)
        dialog.exec()



    def _on_delete_clicked(self) -> None:
        """Delete the currently selected contact after confirmation."""
        contact_id = self.contact_table.get_selected_contact_id()
        if contact_id is None:
            self._show_error("Please select a contact to delete.")
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this contact?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation == QMessageBox.StandardButton.Yes:
            self.controller.delete_contact(contact_id)

    def _on_call_requested(self, phone: str) -> None:
        """Open the system's default call handler for the given phone number."""
        digits = re.sub(r"[^0-9+]", "", phone)
        if not digits:
            self._show_error("This contact has no valid phone number.")
            return
        QDesktopServices.openUrl(QUrl(f"tel:{digits}"))

    def _on_whatsapp_requested(self, phone: str) -> None:
        """Open a WhatsApp chat with the given phone number via wa.me."""
        digits = re.sub(r"[^0-9]", "", phone)
        if not digits:
            self._show_error("This contact has no valid phone number.")
            return
        QDesktopServices.openUrl(QUrl(f"https://wa.me/{digits}"))

    def _on_export_csv(self) -> None:
        """Prompt for a destination file and export all contacts to CSV."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Contacts to CSV", "contacts.csv", "CSV Files (*.csv)"
        )
        if file_path:
            self.controller.export_contacts_to_csv(file_path)

    def _on_import_csv(self) -> None:
        """Prompt for a source CSV file and import contacts from it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Contacts from CSV", "", "CSV Files (*.csv)"
        )
        if file_path:
            self.controller.import_contacts_from_csv(file_path)

    def _on_backup(self) -> None:
        """Prompt for a destination folder and back up the database."""
        directory = QFileDialog.getExistingDirectory(self, "Choose Backup Folder")
        if directory:
            self.controller.backup_database(directory)

    def _on_restore(self) -> None:
        """Prompt for a backup file and restore the database from it."""
        confirmation = QMessageBox.question(
            self,
            "Confirm Restore",
            "Restoring will overwrite your current contacts with the "
            "selected backup. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose Backup File", "", "SQLite Database (*.db)"
        )
        if file_path:
            self.controller.restore_database(file_path)

    def _show_error(self, message: str) -> None:
        """Display an error message to the user in a modal dialog."""
        QMessageBox.critical(self, "Error", message)