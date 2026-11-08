"""
Centralized filesystem locations used by Keuangan Mandiri.

The application keeps its data inside the project's ``data/`` directory by
default.  Tests and portable deployments can override the location with the
``KEUANGAN_MANDIRI_DATA_DIR`` environment variable or by constructing
``StoragePaths`` with an explicit base directory.
"""
from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DB_NAME = "keuangan_mandiri.db"


class StoragePaths:
    """Resolves and creates every directory used by the local storage layer."""

    def __init__(self, base_dir: str | os.PathLike[str] | None = None):
        env_dir = os.environ.get("KEUANGAN_MANDIRI_DATA_DIR")
        self.base_dir = Path(base_dir or env_dir or DEFAULT_DATA_DIR).expanduser().resolve()

    @property
    def db_path(self) -> Path:
        return self.base_dir / DEFAULT_DB_NAME

    @property
    def config_path(self) -> Path:
        return self.base_dir / "config.json"

    @property
    def cache_dir(self) -> Path:
        return self.base_dir / "cache"

    @property
    def attachments_dir(self) -> Path:
        return self.base_dir / "attachments"

    @property
    def backups_dir(self) -> Path:
        return self.base_dir / "backups"

    @property
    def exports_dir(self) -> Path:
        return self.base_dir / "exports"

    @property
    def secrets_dir(self) -> Path:
        return self.base_dir / "secrets"

    @property
    def temp_dir(self) -> Path:
        return self.base_dir / "temp"

    def ensure(self) -> "StoragePaths":
        """Creates all storage directories if they do not exist yet."""
        for directory in (
            self.base_dir,
            self.cache_dir,
            self.attachments_dir,
            self.backups_dir,
            self.exports_dir,
            self.secrets_dir,
            self.temp_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        return self

    def as_dict(self) -> dict:
        self.ensure()
        return {
            "base_dir": str(self.base_dir),
            "db_path": str(self.db_path),
            "config_path": str(self.config_path),
            "cache_dir": str(self.cache_dir),
            "attachments_dir": str(self.attachments_dir),
            "backups_dir": str(self.backups_dir),
            "exports_dir": str(self.exports_dir),
            "secrets_dir": str(self.secrets_dir),
        }


# Shared default paths.  Consumers that need an isolated location (unit tests)
# should instantiate ``StoragePaths(temp_dir)`` instead.
storage_paths = StoragePaths()
