"""
app/config/settings.py

Centralized configuration for Contact Manager Pro V2.

This module is the single source of truth for filesystem paths,
feature flags, and default application settings. No other module in
the application (UI, controllers, services, or repositories) should
hardcode a path or a feature flag directly — they import from here
instead.

Keeping configuration centralized is what makes future migrations
easy: swapping the storage engine, moving to a different backup
location, or exposing these same values to a future FastAPI backend
only requires changing this one file.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ThemeMode(str, Enum):
    """
    Supported UI theme modes.

    Using ``str`` as a mixin lets a ThemeMode be stored, compared, and
    serialized (e.g. to a settings file or a future API response) as
    a plain string, while still being a proper enum in code.
    """

    LIGHT = "light"
    DARK = "dark"


class StorageEngine(str, Enum):
    """
    Supported data storage engines.

    Only ``SQLITE`` is implemented in V2's initial phase. The other
    members exist now so that repository selection logic and settings
    persistence never need to change shape when a new engine is
    added later — only a new repository implementation is required.
    """

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass(frozen=True)
class PathConfig:
    """
    Filesystem paths used throughout the application.

    All paths are resolved relative to the project root so the
    application behaves the same regardless of the current working
    directory it was launched from.

    Attributes:
        project_root (Path): Absolute path to the project's root
            directory.
        data_dir (Path): Directory holding the application's data
            files (e.g. the SQLite database).
        database_file (Path): Path to the SQLite database file.
        exports_dir (Path): Directory where CSV/Excel exports are
            written.
        backups_manual_dir (Path): Directory for manually triggered
            backups.
        backups_auto_dir (Path): Directory for scheduled automatic
            backups.
        logs_dir (Path): Directory holding application log files.
        log_file (Path): Path to the main rotating log file.
        assets_dir (Path): Directory holding static assets.
        icons_dir (Path): Directory holding icon assets.
        images_dir (Path): Directory holding image assets.
        theme_dir (Path): Directory holding ``.qss`` theme stylesheets.
    """

    project_root: Path
    data_dir: Path = field(init=False)
    database_file: Path = field(init=False)
    exports_dir: Path = field(init=False)
    backups_manual_dir: Path = field(init=False)
    backups_auto_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    log_file: Path = field(init=False)
    assets_dir: Path = field(init=False)
    icons_dir: Path = field(init=False)
    images_dir: Path = field(init=False)
    theme_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        """
        Derive all dependent paths from ``project_root``.

        Uses ``object.__setattr__`` because this dataclass is frozen
        (immutable after construction) but its derived fields still
        need to be computed once, at construction time.

        Returns:
            None
        """
        object.__setattr__(self, "data_dir", self.project_root / "data")
        object.__setattr__(
            self, "database_file", self.data_dir / "contacts.db"
        )
        object.__setattr__(
            self, "exports_dir", self.data_dir / "exports"
        )
        object.__setattr__(
            self, "backups_manual_dir", self.project_root / "backups" / "manual"
        )
        object.__setattr__(
            self, "backups_auto_dir", self.project_root / "backups" / "auto"
        )
        object.__setattr__(self, "logs_dir", self.project_root / "logs")
        object.__setattr__(self, "log_file", self.logs_dir / "app.log")
        object.__setattr__(self, "assets_dir", self.project_root / "assets")
        object.__setattr__(self, "icons_dir", self.assets_dir / "icons")
        object.__setattr__(self, "images_dir", self.assets_dir / "images")
        object.__setattr__(
            self, "theme_dir", self.project_root / "app" / "ui" / "theme"
        )

    def ensure_directories_exist(self) -> None:
        """
        Create every directory referenced by this configuration if it
        does not already exist.

        This is idempotent and safe to call on every application
        startup.

        Returns:
            None
        """
        directories = (
            self.data_dir,
            self.exports_dir,
            self.backups_manual_dir,
            self.backups_auto_dir,
            self.logs_dir,
            self.assets_dir,
            self.icons_dir,
            self.images_dir,
        )
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class FeatureFlags:
    """
    Toggles for features that are being incrementally rolled out
    across development phases.

    Each flag defaults to the value appropriate for the current
    development phase. Flags are flipped on as their corresponding
    phase is completed, without requiring changes anywhere flags are
    consumed.

    Attributes:
        groups_and_tags_enabled (bool): Enables group/tag features
            (Phase 5).
        advanced_search_enabled (bool): Enables advanced search and
            filters (Phase 6).
        import_export_enabled (bool): Enables CSV/Excel import and
            export (Phase 7).
        backup_enabled (bool): Enables manual/automatic backup and
            restore (Phase 8).
        auto_backup_enabled (bool): Enables the scheduled automatic
            backup job specifically (only meaningful if
            ``backup_enabled`` is also True).
        settings_ui_enabled (bool): Enables the in-app Settings dialog
            (Phase 9).
    """

    groups_and_tags_enabled: bool = False
    advanced_search_enabled: bool = False
    import_export_enabled: bool = False
    backup_enabled: bool = False
    auto_backup_enabled: bool = False
    settings_ui_enabled: bool = False


@dataclass(frozen=True)
class AppSettings:
    """
    Top-level application settings, composing paths, feature flags,
    and general defaults.

    A single instance of this class is created via
    :func:`get_settings` and passed down explicitly through
    controllers/services/repositories — it is never imported and used
    as a hidden global inside business logic, keeping dependencies
    explicit and testable.

    Attributes:
        app_name (str): Human-readable application name.
        app_version (str): Current application version string.
        paths (PathConfig): Resolved filesystem paths.
        features (FeatureFlags): Feature toggles for in-progress work.
        storage_engine (StorageEngine): The active data storage
            engine. Only ``StorageEngine.SQLITE`` is supported in this
            phase.
        default_theme (ThemeMode): The theme applied on first launch,
            before any user preference has been saved.
        auto_backup_interval_hours (int): How often automatic backups
            run, in hours, once ``FeatureFlags.auto_backup_enabled``
            is True.
        max_backups_to_keep (int): Maximum number of automatic backup
            files retained before the oldest is deleted.
    """

    app_name: str = "Contact Manager Pro V2"
    app_version: str = "2.0.0-dev"
    paths: PathConfig = field(default_factory=lambda: PathConfig(_default_project_root()))
    features: FeatureFlags = field(default_factory=FeatureFlags)
    storage_engine: StorageEngine = StorageEngine.SQLITE
    default_theme: ThemeMode = ThemeMode.LIGHT
    auto_backup_interval_hours: int = 24
    max_backups_to_keep: int = 10


def _default_project_root() -> Path:
    """
    Determine the project root directory.

    Resolution order:
        1. The ``CONTACT_MANAGER_ROOT`` environment variable, if set
           (useful for tests or alternate deployment layouts).
        2. The parent directory of the ``app`` package, which is the
           project root in the standard layout (this file lives at
           ``app/config/settings.py``, so the project root is two
           levels up).

    Returns:
        Path: The resolved, absolute project root directory.
    """
    env_override = os.environ.get("CONTACT_MANAGER_ROOT")
    if env_override:
        return Path(env_override).resolve()

    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "ContactManagerProV2"
        return Path.home() / "ContactManagerProV2"

    return Path(__file__).resolve().parent.parent.parent


_settings_instance: AppSettings | None = None


def get_settings() -> AppSettings:
    """
    Retrieve the application's settings singleton, creating it on
    first call.

    Using a function (rather than a bare module-level constant) keeps
    construction explicit and lazy, and gives a single seam where
    settings could later be loaded from a config file or environment
    variables without changing any call site.

    Returns:
        AppSettings: The application's settings instance, with all
        directories guaranteed to exist on disk.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AppSettings()
        _settings_instance.paths.ensure_directories_exist()
    return _settings_instance