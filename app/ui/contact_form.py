"""
app/ui/contact_form.py

Defines the ContactFormDialog class, the modal dialog used to add a
new contact or edit an existing one, in accordance with the MVC
architecture used in this project.

Includes a photo picker with a large, circular preview: the chosen
image is copied into app/assets/images/contacts/ (via the centralized
settings paths) so the stored photo_path remains valid regardless of
where the original source file lives or moves to later.

This module contains no database logic — it only collects and
returns user input for the controller to persist.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.config.settings import get_settings
from app.models.contact import Contact


class ContactFormDialog(QDialog):
    """
    Modal dialog for creating or editing a contact.

    When constructed with an existing Contact, its fields (including
    photo) are pre-filled for editing. When constructed without one,
    the dialog starts blank for adding a new contact.
    """

    PHOTO_PREVIEW_SIZE = 160

    def __init__(
        self,
        contact: Optional[Contact] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the dialog, optionally pre-filled with an existing
        contact's data.

        Args:
            contact (Optional[Contact]): The contact to edit. If
                ``None``, the dialog is set up for adding a new
                contact.
            parent (Optional[QWidget]): Optional parent widget.
        """
        super().__init__(parent)
        self._contact: Optional[Contact] = contact
        self._photo_path: str = contact.photo_path if contact else ""

        self.first_name_input: QLineEdit
        self.last_name_input: QLineEdit
        self.phone_input: QLineEdit
        self.email_input: QLineEdit
        self.address_input: QLineEdit
        self.notes_input: QTextEdit
        self.photo_preview: QLabel
        self.button_box: QDialogButtonBox

        self._setup_window()
        self._setup_ui()
        self._connect_signals()

        if contact is not None:
            self._populate_fields(contact)

        self._refresh_photo_preview()

    def _setup_window(self) -> None:
        """Configure basic dialog properties (title and modality)."""
        title = "Edit Contact" if self._contact is not None else "Add Contact"
        self.setWindowTitle(title)
        self.setModal(True)

    def _setup_ui(self) -> None:
        """Build and arrange all child widgets and layouts."""
        layout = QVBoxLayout(self)

        layout.addLayout(self._build_photo_section())

        form_layout = QFormLayout()

        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(80)

        form_layout.addRow("First Name:", self.first_name_input)
        form_layout.addRow("Last Name:", self.last_name_input)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("Notes:", self.notes_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.button_box)

    def _build_photo_section(self) -> QHBoxLayout:
        """
        Build the photo preview + choose/remove buttons row.

        Returns:
            QHBoxLayout: The photo section layout.
        """
        layout = QHBoxLayout()

        self.photo_preview = QLabel()
        self.photo_preview.setFixedSize(
            self.PHOTO_PREVIEW_SIZE, self.PHOTO_PREVIEW_SIZE
        )
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setStyleSheet(
            "border: 1px solid #d6d6d6; border-radius: "
            f"{self.PHOTO_PREVIEW_SIZE // 2}px; background-color: #f0f0f0;"
        )

        buttons_layout = QVBoxLayout()
        self.choose_photo_button = QPushButton("Choose Photo")
        self.remove_photo_button = QPushButton("Remove Photo")
        buttons_layout.addWidget(self.choose_photo_button)
        buttons_layout.addWidget(self.remove_photo_button)
        buttons_layout.addStretch()

        layout.addWidget(self.photo_preview)
        layout.addLayout(buttons_layout)
        layout.addStretch()

        return layout

    def _connect_signals(self) -> None:
        """Connect the dialog button box and photo buttons to their slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.choose_photo_button.clicked.connect(self._on_choose_photo)
        self.remove_photo_button.clicked.connect(self._on_remove_photo)

    def _populate_fields(self, contact: Contact) -> None:
        """
        Pre-fill the form fields with an existing contact's data.

        Args:
            contact (Contact): The contact whose data should populate
                the form.

        Returns:
            None
        """
        self.first_name_input.setText(contact.first_name)
        self.last_name_input.setText(contact.last_name)
        self.phone_input.setText(contact.phone)
        self.email_input.setText(contact.email)
        self.address_input.setText(contact.address)
        self.notes_input.setPlainText(contact.notes)

    def _on_choose_photo(self) -> None:
        """
        Open a file picker, copy the chosen image into the app's
        managed photo storage folder, and update the preview.

        Returns:
            None
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Contact Photo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)",
        )
        if not file_path:
            return

        try:
            stored_path = self._copy_photo_into_storage(file_path)
        except OSError as exc:
            self.photo_preview.setText("Failed")
            self.photo_preview.setToolTip(f"Could not copy photo: {exc}")
            return

        self._photo_path = stored_path
        self._refresh_photo_preview()

    def _on_remove_photo(self) -> None:
        """
        Clear the selected photo (does not delete the file from disk,
        only detaches it from this contact).

        Returns:
            None
        """
        self._photo_path = ""
        self._refresh_photo_preview()

    @staticmethod
    def _copy_photo_into_storage(source_path: str) -> str:
        """
        Copy the given image file into the app's managed
        assets/images/contacts folder under a unique filename, so the
        stored path remains valid even if the original file is moved
        or deleted.

        Args:
            source_path (str): Path to the originally selected image.

        Returns:
            str: The new, stable path to the copied image.
        """
        settings = get_settings()
        contacts_photo_dir = settings.paths.images_dir / "contacts"
        contacts_photo_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(source_path).suffix or ".png"
        unique_name = f"contact_{uuid.uuid4().hex}{extension}"
        destination = contacts_photo_dir / unique_name

        shutil.copy2(source_path, destination)
        return str(destination)

    def _refresh_photo_preview(self) -> None:
        """
        Update the preview label to show the currently selected
        photo — cropped to a circle and scaled to fill the preview
        box (not stretched), or a placeholder if none is set / the
        file is missing.

        Returns:
            None
        """
        if self._photo_path and Path(self._photo_path).exists():
            circular = self._build_circular_pixmap(self._photo_path)
            if circular is not None:
                self.photo_preview.setPixmap(circular)
                self.photo_preview.setText("")
                return

        self.photo_preview.setPixmap(QPixmap())
        self.photo_preview.setText("No\nPhoto")

    def _build_circular_pixmap(self, source_path: str) -> Optional[QPixmap]:
        """
        Load an image file and render it as a circular pixmap sized
        to PHOTO_PREVIEW_SIZE, cropped to fill the circle (not
        stretched — the image is scaled up/down proportionally, then
        centered and clipped).

        Args:
            source_path (str): Path to the source image file.

        Returns:
            Optional[QPixmap]: The circular pixmap, or ``None`` if the
            source file could not be loaded as an image.
        """
        source = QPixmap(source_path)
        if source.isNull():
            return None

        size = self.PHOTO_PREVIEW_SIZE
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

    def get_contact_data(self) -> dict[str, Any]:
        """
        Retrieve the current values entered into the form.

        Returns:
            dict[str, Any]: A dictionary with keys ``first_name``,
            ``last_name``, ``phone``, ``email``, ``address``,
            ``notes``, and ``photo_path``, containing the trimmed
            field values.
        """
        return {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "photo_path": self._photo_path,
        }