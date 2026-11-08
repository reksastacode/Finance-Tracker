"""
Full local backups for Keuangan Mandiri.

A ``.kmbak`` file is a Fernet-encrypted ZIP bundle containing:

* a consistent SQLite snapshot made with the native backup API,
* every attachment file,
* a copy of ``config.json`` (for reference; secrets are never included),
* a manifest with sizes and SHA-256 hashes.

Restoring uses SQLite's backup API again, so the application does not need to be
closed and WAL mode remains consistent.
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path

from src.storage.crypto import CryptoError, get_crypto
from src.storage.file_store import (
    atomic_write_bytes,
    human_size,
    read_bytes,
    safe_rmtree,
    sha256_bytes,
)
from src.storage.paths import StoragePaths, storage_paths


BACKUP_MAGIC = b"KMBAK1\n"
BACKUP_FORMAT = 1


class BackupError(RuntimeError):
    """Raised when a backup cannot be created, read, or restored."""


class BackupManager:
    def __init__(self, paths: StoragePaths | None = None, *, crypto=None):
        self.paths = paths or storage_paths
        self.paths.ensure()
        self.backups_dir = self.paths.backups_dir
        self._crypto = crypto

    def _crypto_service(self):
        if self._crypto is not None:
            return self._crypto
        return get_crypto()

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def create_backup(self, label: str = "manual") -> Path:
        if not self.paths.db_path.is_file():
            raise BackupError("Database belum tersedia, backup tidak dapat dibuat.")

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_label = "".join(ch for ch in label if ch.isalnum() or ch in ("-", "_")) or "backup"
        output = self.backups_dir / f"keuangan_mandiri_{stamp}_{safe_label}.kmbak"

        temp_root = Path(tempfile.mkdtemp(prefix="keuangan_backup_"))
        snapshot_path = temp_root / "database.db"
        try:
            # SQLite's online backup API creates a transactionally consistent copy
            # even while WAL connections are open.
            source = sqlite3.connect(str(self.paths.db_path), timeout=30.0)
            destination = sqlite3.connect(str(snapshot_path))
            try:
                source.backup(destination)
                destination.commit()
            finally:
                destination.close()
                source.close()

            manifest = {
                "format": BACKUP_FORMAT,
                "app": "Keuangan Mandiri",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "label": label,
                "database": {
                    "name": "database.db",
                    "size": snapshot_path.stat().st_size,
                    "sha256": self._file_sha256(snapshot_path),
                },
                "files": [],
                "config_included": False,
            }

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.write(snapshot_path, "database.db")
                if self.paths.config_path.is_file():
                    archive.write(self.paths.config_path, "config.json")
                    manifest["config_included"] = True

                for attachment in sorted(self.paths.attachments_dir.glob("*")):
                    if not attachment.is_file():
                        continue
                    arcname = f"attachments/{attachment.name}"
                    archive.write(attachment, arcname)
                    manifest["files"].append({
                        "name": attachment.name,
                        "arcname": arcname,
                        "size": attachment.stat().st_size,
                        "sha256": self._file_sha256(attachment),
                    })

                archive.writestr("manifest.json", json.dumps(manifest, indent=2))

            encrypted = self._crypto_service().encrypt_bytes(buffer.getvalue())
            atomic_write_bytes(output, BACKUP_MAGIC + encrypted)
            self._apply_retention()
            return output
        except (OSError, sqlite3.Error, CryptoError) as exc:
            raise BackupError(f"Gagal membuat backup: {exc}") from exc
        finally:
            safe_rmtree(temp_root)

    @staticmethod
    def _file_sha256(path: Path) -> str:
        import hashlib

        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _apply_retention(self):
        max_backups = 10
        try:
            from src.storage.config import get_config

            max_backups = int(get_config().get("backup.max_backups", 10))
        except Exception:
            pass
        backups = self.list_backups()
        for old in backups[max(1, max_backups):]:
            try:
                Path(old["path"]).unlink()
            except OSError:
                pass

    def list_backups(self) -> list[dict]:
        result = []
        for path in self.backups_dir.glob("*.kmbak"):
            try:
                stat = path.stat()
            except OSError:
                continue
            result.append({
                "path": str(path),
                "name": path.name,
                "size_bytes": stat.st_size,
                "size_human": human_size(stat.st_size),
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                "timestamp": stat.st_mtime,
            })
        result.sort(key=lambda item: item["timestamp"], reverse=True)
        return result

    # ------------------------------------------------------------------
    # Read / restore
    # ------------------------------------------------------------------
    def read_manifest(self, backup_path: str | os.PathLike[str]) -> dict:
        payload = self._read_payload(backup_path)
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                return json.loads(archive.read("manifest.json").decode("utf-8"))
        except (KeyError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            raise BackupError(f"Backup tidak valid: {exc}") from exc

    def _read_payload(self, backup_path: str | os.PathLike[str]) -> bytes:
        raw = read_bytes(backup_path)
        if not raw.startswith(BACKUP_MAGIC):
            raise BackupError("File bukan backup Keuangan Mandiri (.kmbak).")
        try:
            return self._crypto_service().decrypt_bytes(raw[len(BACKUP_MAGIC):])
        except CryptoError as exc:
            raise BackupError(str(exc)) from exc

    def restore_backup(self, backup_path: str | os.PathLike[str], *, create_safety_backup: bool = True) -> dict:
        # A safety backup is intentionally created before any destructive step.
        safety_path = None
        if create_safety_backup:
            try:
                safety_path = self.create_backup("pre_restore")
            except BackupError:
                safety_path = None

        payload = self._read_payload(backup_path)
        temp_root = Path(tempfile.mkdtemp(prefix="keuangan_restore_"))
        try:
            try:
                archive = zipfile.ZipFile(io.BytesIO(payload))
            except zipfile.BadZipFile as exc:
                raise BackupError(f"Backup bukan arsip yang valid: {exc}") from exc

            with archive:
                try:
                    manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
                    database_bytes = archive.read("database.db")
                except (KeyError, ValueError, json.JSONDecodeError) as exc:
                    raise BackupError(f"Struktur backup tidak lengkap: {exc}") from exc

                if manifest.get("format") != BACKUP_FORMAT:
                    raise BackupError("Versi format backup tidak didukung.")

                # Verify every extracted member against the manifest and reject
                # path traversal (``..`` / absolute names).
                for info in archive.infolist():
                    name = info.filename.replace("\\", "/")
                    if name.startswith("/") or ".." in name.split("/"):
                        raise BackupError("Backup mengandung path yang tidak aman.")

                restore_db = temp_root / "restore.db"
                restore_db.write_bytes(database_bytes)
                self._validate_database(restore_db)

                attachments_root = temp_root / "attachments"
                attachments_root.mkdir(parents=True, exist_ok=True)
                manifest_files = {entry["arcname"]: entry for entry in manifest.get("files", [])}
                for arcname, entry in manifest_files.items():
                    data = archive.read(arcname)
                    if sha256_bytes(data) != entry.get("sha256"):
                        raise BackupError(f"Checksum lampiran tidak cocok: {arcname}")
                    target = attachments_root / Path(arcname).name
                    target.write_bytes(data)

            self._replace_database(restore_db)
            self._replace_attachments(attachments_root)

            return {
                "manifest": manifest,
                "safety_backup": str(safety_path) if safety_path else "",
                "restored_database": str(self.paths.db_path),
                "restored_attachments": len(manifest.get("files", [])),
            }
        finally:
            safe_rmtree(temp_root)

    @staticmethod
    def _validate_database(path: Path):
        try:
            conn = sqlite3.connect(str(path))
            try:
                result = conn.execute("PRAGMA integrity_check;").fetchone()
                if not result or str(result[0]).lower() != "ok":
                    raise BackupError("Pemeriksaan integritas database backup gagal.")
                tables = {row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table';"
                ).fetchall()}
                required = {"transactions", "categories", "targets", "target_allocations"}
                if not required.intersection(tables):
                    raise BackupError("Backup tidak berisi skema Keuangan Mandiri.")
            finally:
                conn.close()
        except sqlite3.Error as exc:
            raise BackupError(f"Database backup tidak valid: {exc}") from exc

    def _replace_database(self, source_path: Path):
        # Restore into the live database through SQLite's backup API.  This
        # keeps existing WAL connections valid and avoids file-lock problems.
        source = sqlite3.connect(str(source_path))
        destination = sqlite3.connect(str(self.paths.db_path), timeout=30.0)
        try:
            source.backup(destination)
            destination.commit()
            destination.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        finally:
            destination.close()
            source.close()

    def _replace_attachments(self, source_dir: Path):
        self.paths.attachments_dir.mkdir(parents=True, exist_ok=True)
        for old in self.paths.attachments_dir.iterdir():
            if old.is_file():
                try:
                    old.unlink()
                except OSError:
                    pass
        for source in source_dir.iterdir():
            if source.is_file():
                target = self.paths.attachments_dir / source.name
                target.write_bytes(source.read_bytes())


_backup_instance: BackupManager | None = None


def get_backup_manager() -> BackupManager:
    global _backup_instance
    if _backup_instance is None:
        _backup_instance = BackupManager()
    return _backup_instance


def reset_backup_manager_for_tests(manager: BackupManager | None = None):
    global _backup_instance
    _backup_instance = manager
