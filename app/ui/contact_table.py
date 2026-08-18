"""
app/ui/contact_table.py

Defines the ContactTableWidget class: contact list with initials
avatar, favorite star (persisted via QSettings, not the database),
copy-to-clipboard, Call/WhatsApp actions, and column-header sorting.

Action buttons (Copy/Call/Chat) use plain text labels rather than
stock Qt icons, and each has an explicit minimum width so its text is
never clipped regardless of how narrow the column's ResizeToContents
sizing ends up (which is driven by header text length, not button
content).

This module contains no database or controller logic — it only
renders Contact instances and emits signals for the parent window to
act on. Favorite state is UI-local persistence (QSettings), kept
deliberately separate from the Contact model/database schema.
"""

from __future__ import annotations

from typing import Optional

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QClipboard, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app.models.contact import Contact

FAVORITES_SETTINGS_KEY = "favorites/contact_ids"
ACTION_BUTTON_MIN_WIDTH = 64


class ContactTableWidget(QTableWidget):
    """
    Table widget that displays a list of contacts with avatar,
    favorite, and quick-action columns.

    Signals:
        call_requested (str): Emitted with a contact's phone number
            when the row's Call button is clicked.
        whatsapp_requested (str): Emitted with a contact's phone
            number when the row's Chat (WhatsApp) button is clicked.
        favorite_changed (): Emitted whenever a favorite is toggled,
            so the parent window can refresh a "Favorites" filter.

    Attributes:
        COLUMN_HEADERS (list[str]): Display labels for each column.
    """

    call_requested = Signal(str)
    whatsapp_requested = Signal(str)
    favorite_changed = Signal()
    contact_double_clicked = Signal(int)

    COL_AVATAR = 0
    COL_FAVORITE = 1
    COL_FIRST_NAME = 2
    COL_LAST_NAME = 3
    COL_PHONE = 4
    COL_EMAIL = 5
    COL_ADDRESS = 6
    COL_NOTES = 7
    COL_COPY_PHONE = 8
    COL_COPY_EMAIL = 9
    COL_CALL = 10
    COL_WHATSAPP = 11

    COLUMN_HEADERS: list[str] = [
        "",
        "★",
        "First Name",
        "Last Name",
        "Phone",
        "Email",
        "Address",
        "Notes",
        "Number",
        "Email",
        "Call",
        "WhatsApp",
    ]

    AVATAR_COLORS: list[str] = [
        "#0b57d0", "#c5221f", "#188038", "#e37400",
        "#9334e6", "#12676a", "#a52714", "#1a73e8",
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the table widget and configure its appearance
        and selection behavior.

        Args:
            parent (Optional[QWidget]): Optional parent widget.
        """
        super().__init__(parent)
        self._settings = QSettings("ContactManagerProV2", "ContactTable")
        self._configure_table()
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def _on_cell_double_clicked(self, row: int, _column: int) -> None:
        """
        Emit contact_double_clicked with the double-clicked row's
        contact id.

        Args:
            row (int): The row that was double-clicked.
            _column (int): The column that was double-clicked
                (unused — any column in the row opens the detail view).

        Returns:
            None
        """
        item = self.item(row, self.COL_FIRST_NAME)
        if item is not None:
            contact_id = item.data(Qt.ItemDataRole.UserRole)
            if contact_id is not None:
                self.contact_double_clicked.emit(contact_id)

    def _configure_table(self) -> None:
        """
        Configure column count, headers, and selection/sort/edit
        behavior.

        Returns:
            None
        """
        self.setColumnCount(len(self.COLUMN_HEADERS))
        self.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(40)
        self.setSortingEnabled(True)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for column in (
            self.COL_AVATAR,
            self.COL_FAVORITE,
            self.COL_COPY_PHONE,
            self.COL_COPY_EMAIL,
            self.COL_CALL,
            self.COL_WHATSAPP,
        ):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )

    # ------------------------------------------------------------
    # Favorites persistence (QSettings-based, not the database)
    # ------------------------------------------------------------

    def _load_favorite_ids(self) -> set[int]:
        """
        Load the set of favorite contact ids from QSettings.

        Returns:
            set[int]: The stored favorite contact ids.
        """
        raw = self._settings.value(FAVORITES_SETTINGS_KEY, [])
        try:
            return {int(value) for value in raw}
        except (TypeError, ValueError):
            return set()

    def _save_favorite_ids(self, favorite_ids: set[int]) -> None:
        """
        Persist the given set of favorite contact ids to QSettings.

        Args:
            favorite_ids (set[int]): The favorite contact ids to save.

        Returns:
            None
        """
        self._settings.setValue(FAVORITES_SETTINGS_KEY, list(favorite_ids))

    def is_favorite(self, contact_id: Optional[int]) -> bool:
        """
        Check whether a contact is marked as favorite.

        Args:
            contact_id (Optional[int]): The contact id to check.

        Returns:
            bool: True if the contact is a favorite.
        """
        if contact_id is None:
            return False
        return contact_id in self._load_favorite_ids()

    def _toggle_favorite(self, contact_id: Optional[int]) -> None:
        """
        Toggle a contact's favorite status and persist the change.

        Args:
            contact_id (Optional[int]): The contact id to toggle.

        Returns:
            None
        """
        if contact_id is None:
            return
        favorites = self._load_favorite_ids()
        if contact_id in favorites:
            favorites.remove(contact_id)
        else:
            favorites.add(contact_id)
        self._save_favorite_ids(favorites)
        self.favorite_changed.emit()

    # ------------------------------------------------------------
    # Population
    # ------------------------------------------------------------

    def load_contacts(self, contacts: list[Contact]) -> None:
        """
        Populate the table with the given list of contacts, replacing
        any previously displayed rows.

        Args:
            contacts (list[Contact]): The contacts to display.

        Returns:
            None
        """
        was_sorting = self.isSortingEnabled()
        self.setSortingEnabled(False)
        self.setRowCount(0)

        for row_index, contact in enumerate(contacts):
            self.insertRow(row_index)
            self._set_avatar(row_index, contact)
            self._set_favorite_widget(row_index, contact)

            text_values = {
                self.COL_FIRST_NAME: contact.first_name,
                self.COL_LAST_NAME: contact.last_name,
                self.COL_PHONE: contact.phone,
                self.COL_EMAIL: contact.email,
                self.COL_ADDRESS: contact.address,
                self.COL_NOTES: contact.notes,
            }
            for column, value in text_values.items():
                item = QTableWidgetItem(value)
                if column == self.COL_FIRST_NAME:
                    item.setData(Qt.ItemDataRole.UserRole, contact.id)
                self.setItem(row_index, column, item)

            self._set_copy_button(row_index, self.COL_COPY_PHONE, contact.phone)
            self._set_copy_button(row_index, self.COL_COPY_EMAIL, contact.email)
            self._set_call_button(row_index, contact.phone)
            self._set_whatsapp_button(row_index, contact.phone)

        self.setSortingEnabled(was_sorting)

    AVATAR_SIZE = 30

    def _set_avatar(self, row_index: int, contact: Contact) -> None:
        """
        Create and place the avatar for a single row: the contact's
        actual photo (if set and the file still exists) as a circular
        image, otherwise a colored circle with the contact's initials.

        Args:
            row_index (int): The row to place the avatar in.
            contact (Contact): The contact whose avatar to show.

        Returns:
            None
        """
        photo_path = (contact.photo_path or "").strip()
        if photo_path and Path(photo_path).exists():
            pixmap = self._build_circular_pixmap(photo_path)
            if pixmap is not None:
                label = QLabel()
                label.setFixedSize(self.AVATAR_SIZE, self.AVATAR_SIZE)
                label.setPixmap(pixmap)
                self.setCellWidget(row_index, self.COL_AVATAR, label)
                return

        initials = self._get_initials(contact)
        color = self._get_avatar_color(contact)

        label = QPushButton(initials)
        label.setEnabled(False)
        label.setFixedSize(self.AVATAR_SIZE, self.AVATAR_SIZE)
        label.setStyleSheet(
            f"""
                QPushButton {{
                    background-color: {color};
                    color: #ffffff;
                    border-radius: 15px;
                    font-weight: 600;
                    font-size: 11px;
                    border: none;
                }}
                """
        )
        self.setCellWidget(row_index, self.COL_AVATAR, label)

    def _build_circular_pixmap(self, source_path: str) -> Optional[QPixmap]:
        """
        Load an image file and render it as a circular pixmap sized
        to AVATAR_SIZE.

        Args:
            source_path (str): Path to the source image file.

        Returns:
            Optional[QPixmap]: The circular pixmap, or ``None`` if the
            source file could not be loaded as an image.
        """
        source = QPixmap(source_path)
        if source.isNull():
            return None

        size = self.AVATAR_SIZE
        scaled = source.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        circular = QPixmap(size, size)
        circular.fill(Qt.GlobalColor.transparent)

        painter = QPainter(circular)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        clip_path = QPainterPath()
        clip_path.addEllipse(0, 0, size, size)
        painter.setClipPath(clip_path)

        x = (size - scaled.width()) // 2
        y = (size - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)
        painter.end()

        return circular

    @staticmethod
    def _get_initials(contact: Contact) -> str:
        """
        Compute up to two uppercase initials from a contact's name.

        Args:
            contact (Contact): The contact to compute initials for.

        Returns:
            str: One or two uppercase initial letters.
        """
        first = contact.first_name.strip()[:1]
        last = contact.last_name.strip()[:1]
        initials = f"{first}{last}".upper()
        return initials or "?"

    def _get_avatar_color(self, contact: Contact) -> str:
        """
        Deterministically pick an avatar background color based on
        the contact's name, so the same contact always gets the same
        color.

        Args:
            contact (Contact): The contact to pick a color for.

        Returns:
            str: A hex color string.
        """
        seed = f"{contact.first_name}{contact.last_name}"
        index = sum(ord(character) for character in seed) % len(
            self.AVATAR_COLORS
        )
        return self.AVATAR_COLORS[index]

    def _set_favorite_widget(self, row_index: int, contact: Contact) -> None:
        """
        Create and place the favorite-star toggle button for a single
        row.

        Args:
            row_index (int): The row to place the button in.
            contact (Contact): The contact this row represents.

        Returns:
            None
        """
        button = QPushButton("★" if self.is_favorite(contact.id) else "☆")
        button.setObjectName("FavoriteButton")
        button.setFixedSize(28, 28)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolTip("Toggle favorite")

        def handle_click(_checked: bool = False, cid=contact.id, btn=button) -> None:
            self._toggle_favorite(cid)
            btn.setText("★" if self.is_favorite(cid) else "☆")

        button.clicked.connect(handle_click)
        self.setCellWidget(row_index, self.COL_FAVORITE, button)

    def _set_copy_button(self, row_index: int, column: int, value: str) -> None:
        """
        Create and place a copy-to-clipboard button for a single cell.

        A fixed minimum width guarantees the "Copy" label is never
        clipped, regardless of the column's ResizeToContents width
        (which is driven by the — here empty — header text, not the
        button's own content).

        Args:
            row_index (int): The row to place the button in.
            column (int): The column to place the button in (should be
                COL_COPY_PHONE or COL_COPY_EMAIL).
            value (str): The value to copy when clicked.

        Returns:
            None
        """
        button = QPushButton("Copy")
        button.setObjectName("CopyButton")
        button.setToolTip("Copy to clipboard")
        button.setEnabled(bool(value.strip()))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumWidth(ACTION_BUTTON_MIN_WIDTH)
        button.setMinimumHeight(30)
        button.clicked.connect(
            lambda _checked=False, v=value: QApplication.clipboard().setText(
                v, QClipboard.Mode.Clipboard
            )
        )
        self.setCellWidget(row_index, column, button)

    def _set_call_button(self, row_index: int, phone: str) -> None:
        """
        Create and place the Call button for a single row.

        Args:
            row_index (int): The row to place the button in.
            phone (str): The contact's phone number.

        Returns:
            None
        """
        button = QPushButton("Call")
        button.setObjectName("CallButton")
        button.setToolTip("Call this contact")
        button.setEnabled(bool(phone.strip()))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumWidth(ACTION_BUTTON_MIN_WIDTH)
        button.setMinimumHeight(30)
        button.clicked.connect(
            lambda _checked=False, p=phone: self.call_requested.emit(p)
        )
        self.setCellWidget(row_index, self.COL_CALL, button)

    def _set_whatsapp_button(self, row_index: int, phone: str) -> None:
        """
        Create and place the WhatsApp (Chat) button for a single row.

        Args:
            row_index (int): The row to place the button in.
            phone (str): The contact's phone number.

        Returns:
            None
        """
        button = QPushButton("Chat")
        button.setObjectName("WhatsAppButton")
        button.setToolTip("Open WhatsApp chat with this contact")
        button.setEnabled(bool(phone.strip()))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumWidth(ACTION_BUTTON_MIN_WIDTH)
        button.setMinimumHeight(30)
        button.clicked.connect(
            lambda _checked=False, p=phone: self.whatsapp_requested.emit(p)
        )
        self.setCellWidget(row_index, self.COL_WHATSAPP, button)

    # ------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------

    def get_selected_contact_id(self) -> Optional[int]:
        """
        Return the database id of the currently selected contact.

        Returns:
            Optional[int]: The selected contact's id, or ``None`` if
            no row is currently selected.
        """
        selected_rows = self.selectionModel().selectedRows(self.COL_FIRST_NAME)
        if not selected_rows:
            return None

        row = selected_rows[0].row()
        item = self.item(row, self.COL_FIRST_NAME)
        if item is None:
            return None

        return item.data(Qt.ItemDataRole.UserRole)