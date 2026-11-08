"""
Versioned JSON configuration for Keuangan Mandiri.

The file lives at ``data/config.json`` by default and is intentionally small,
human readable, and free of secrets.  Sensitive material always belongs in the
encrypted database or the DPAPI-protected key file.
"""
from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path
from typing import Any

from src.storage.file_store import atomic_write_text, read_text
from src.storage.paths import StoragePaths, storage_paths


DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "ui": {
        "page_size": 50,
        "last_page": 0,
        "window_geometry": "",
        "chart_period": "Minggu ini",
    },
    "storage": {
        "export_dir": "data/exports",
        "attachment_dir": "data/attachments",
        "backup_dir": "data/backups",
        "max_attachment_mb": 10,
    },
    "cache": {
        "enabled": True,
        "ttl_seconds": 300,
    },
    "backup": {
        "auto_before_migration": True,
        "max_backups": 10,
    },
    "encryption": {
        "enabled": True,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class ConfigManager:
    """Loads, validates, and atomically persists application preferences."""

    def __init__(self, path: str | os.PathLike[str] | None = None, paths: StoragePaths | None = None):
        self.paths = paths or storage_paths
        self.path = Path(path or self.paths.config_path)
        self._lock = threading.RLock()
        self._data: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    # ------------------------------------------------------------------
    # Loading / saving
    # ------------------------------------------------------------------
    def load(self) -> dict[str, Any]:
        with self._lock:
            raw = read_text(self.path, "")
            if not raw.strip():
                self._data = copy.deepcopy(DEFAULT_CONFIG)
                self.save()
                return copy.deepcopy(self._data)

            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("configuration root must be an object")
                self._data = _deep_merge(DEFAULT_CONFIG, parsed)
                self._validate()
            except (ValueError, TypeError, json.JSONDecodeError):
                # Keep the broken file for inspection instead of silently
                # destroying a user's preferences.
                try:
                    backup = self.path.with_suffix(
                        self.path.suffix + f".corrupt-{int(__import__('time').time())}"
                    )
                    os.replace(self.path, backup)
                except OSError:
                    pass
                self._data = copy.deepcopy(DEFAULT_CONFIG)
                self.save()
            return copy.deepcopy(self._data)

    def _validate(self):
        ui = self._data.setdefault("ui", {})
        try:
            ui["page_size"] = max(10, min(int(ui.get("page_size", 50)), 500))
        except (TypeError, ValueError):
            ui["page_size"] = 50
        if ui.get("chart_period") not in ("Minggu ini", "Bulan ini", "Tahun ini"):
            ui["chart_period"] = "Minggu ini"

        cache = self._data.setdefault("cache", {})
        try:
            cache["ttl_seconds"] = max(0, int(cache.get("ttl_seconds", 300)))
        except (TypeError, ValueError):
            cache["ttl_seconds"] = 300

        backup = self._data.setdefault("backup", {})
        try:
            backup["max_backups"] = max(1, min(int(backup.get("max_backups", 10)), 100))
        except (TypeError, ValueError):
            backup["max_backups"] = 10

        storage = self._data.setdefault("storage", {})
        try:
            storage["max_attachment_mb"] = max(1, min(int(storage.get("max_attachment_mb", 10)), 100))
        except (TypeError, ValueError):
            storage["max_attachment_mb"] = 10

    def save(self) -> Path:
        with self._lock:
            self._validate()
            content = json.dumps(self._data, indent=2, ensure_ascii=False) + "\n"
            return atomic_write_text(self.path, content)

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def get(self, dotted_key: str, default: Any = None) -> Any:
        with self._lock:
            current: Any = self._data
            for part in dotted_key.split("."):
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]
            return copy.deepcopy(current)

    def set(self, dotted_key: str, value: Any, save: bool = True) -> Any:
        with self._lock:
            parts = dotted_key.split(".")
            current = self._data
            for part in parts[:-1]:
                current = current.setdefault(part, {})
                if not isinstance(current, dict):
                    raise ValueError(f"configuration key is not an object: {part}")
            current[parts[-1]] = copy.deepcopy(value)
            # Type coercion happens in _validate(); read values after saving.
            if save:
                self.save()
            return self.get(dotted_key)

    def update(self, values: dict[str, Any], save: bool = True) -> dict[str, Any]:
        with self._lock:
            for key, value in (values or {}).items():
                parts = key.split(".")
                current = self._data
                for part in parts[:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = copy.deepcopy(value)
            if save:
                self.save()
            return self.as_dict()

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._data)

    def reset(self, save: bool = True) -> dict[str, Any]:
        with self._lock:
            self._data = copy.deepcopy(DEFAULT_CONFIG)
            if save:
                self.save()
            return copy.deepcopy(self._data)


_config_instance: ConfigManager | None = None
_config_lock = threading.Lock()


def get_config() -> ConfigManager:
    """Returns the process-wide configuration manager."""
    global _config_instance
    with _config_lock:
        if _config_instance is None:
            _config_instance = ConfigManager()
        return _config_instance
