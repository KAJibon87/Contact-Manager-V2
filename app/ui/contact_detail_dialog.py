"""
app/ui/contact_detail_dialog.py

Read-only detail view for a single contact, opened via double-click
on a table row. Shows the contact's photo (large, circular) if set,
along with all other fields. Pure display — no editing, no controller
calls beyond the read that supplied the Contact object.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.models.contact import Contact


class ContactDetailDialog(QDialog):
    """
    Read-only dialog showing full details for a single contact,
    including its photo.
    """

    PHOTO_SIZE = 120

    def __init__(
        self, contact: Contact, parent: Optional[QWidget] = None
    ) -> None:
        """
        Initialize the detail dialog for the given contact.

        Args:
            contact (Contact): The contact to display.
            parent (Optional[QWidget]): Optional parent widget.
        """
        super().__init__(parent)
        self._contact = contact
        self._setup_window()
        self._setup_ui()

    def _setup_window(self) -> None:
        """Configure basic dialog properties."""
        self.setWindowTitle(
            f"{self._contact.first_name} {self._contact.last_name}".strip()
            or "Contact Details"
        )
        self.setMinimumWidth(380)

    def _setup_ui(self) -> None:
        """Build the photo header plus the read-only field layout."""
        layout = QVBoxLayout(self)

        layout.addLayout(self._build_photo_header())

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        fields = [
            ("First Name", self._contact.first_name),
            ("Last Name", self._contact.last_name),
            ("Phone", self._contact.phone),
            ("Email", self._contact.email),
            ("Address", self._contact.address),
            ("Notes", self._contact.notes),
        ]
        for label_text, value in fields:
            value_label = QLabel(value or "—")
            value_label.setWordWrap(True)
            form.addRow(f"{label_text}:", value_label)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _build_photo_header(self) -> QHBoxLayout:
        """
        Build a centered, large circular photo (or an initials
        placeholder if no photo is set / the file is missing).

        Returns:
            QHBoxLayout: The photo header layout.
        """
        layout = QHBoxLayout()

        photo_label = QLabel()
        photo_label.setFixedSize(self.PHOTO_SIZE, self.PHOTO_SIZE)
        photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        photo_path = (self._contact.photo_path or "").strip()
        pixmap = None
        if photo_path and Path(photo_path).exists():
            pixmap = self._build_circular_pixmap(photo_path)

        if pixmap is not None:
            photo_label.setPixmap(pixmap)
        else:
            initials = self._get_initials()
            photo_label.setText(initials)
            photo_label.setStyleSheet(
                "border: 1px solid #d6d6d6; border-radius: "
                f"{self.PHOTO_SIZE // 2}px; background-color: #0b57d0; "
                "color: #ffffff; font-size: 28px; font-weight: 600;"
            )

        layout.addStretch()
        layout.addWidget(photo_label)
        layout.addStretch()

        return layout

    def _get_initials(self) -> str:
        """
        Compute up to two uppercase initials from the contact's name.

        Returns:
            str: One or two uppercase initial letters.
        """
        first = self._contact.first_name.strip()[:1]
        last = self._contact.last_name.strip()[:1]
        initials = f"{first}{last}".upper()
        return initials or "?"

    def _build_circular_pixmap(self, source_path: str) -> Optional[QPixmap]:
        """
        Load an image file and render it as a circular pixmap sized
        to PHOTO_SIZE, cropped to fill the circle (not stretched).

        Args:
            source_path (str): Path to the source image file.

        Returns:
            Optional[QPixmap]: The circular pixmap, or ``None`` if the
            source file could not be loaded as an image.
        """
        source = QPixmap(source_path)
        if source.isNull():
            return None

        size = self.PHOTO_SIZE
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