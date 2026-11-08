"""
Encrypted local attachment storage.

Attachment files are copied into ``data/attachments`` under random names and
encrypted at rest.  The original filename and metadata live in SQLite; the
original filename is itself encrypted by ``DatabaseManager``.  Files are only
decrypted to a temporary location when the user asks to open them.
"""
from __future__ import annotations

import mimetypes
import os
import shutil
import tempfile
import uuid
from pathlib import Path

from src.storage.crypto import CryptoError, get_crypto
from src.storage.file_store import (
    atomic_write_bytes,
    ensure_parent,
    read_bytes,
    safe_unlink,
    sanitize_filename,
    sha256_bytes,
)
from src.storage.paths import StoragePaths, storage_paths


ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp",
    ".pdf", ".txt",
}


class AttachmentError(RuntimeError):
    """Raised when an attachment cannot be validated or stored."""


class AttachmentService:
    def __init__(
        self,
        paths: StoragePaths | None = None,
        *,
        max_size_mb: int = 10,
        crypto=None,
    ):
        self.paths = paths or storage_paths
        self.attachments_dir = self.paths.attachments_dir
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max(1, int(max_size_mb)) * 1024 * 1024
        self._crypto = crypto

    def _crypto_service(self):
        if self._crypto is not None:
            return self._crypto
        return get_crypto()

    def validate(self, source_path: str | os.PathLike[str]) -> tuple[Path, int, str]:
        source = Path(source_path)
        if not source.is_file():
            raise AttachmentError("File lampiran tidak ditemukan.")
        size = source.stat().st_size
        if size <= 0:
            raise AttachmentError("File lampiran kosong.")
        if size > self.max_size_bytes:
            max_mb = self.max_size_bytes // (1024 * 1024)
            raise AttachmentError(f"Ukuran lampiran melebihi batas {max_mb} MB.")
        extension = source.suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
            raise AttachmentError(f"Format lampiran tidak didukung. Gunakan: {allowed}.")
        mime_type = mimetypes.guess_type(str(source))[0] or "application/octet-stream"
        return source, size, mime_type

    def store(self, source_path: str | os.PathLike[str]) -> dict:
        """Copies and encrypts an attachment, returning metadata for SQLite."""
        source, size, mime_type = self.validate(source_path)
        original_name = sanitize_filename(source.name)
        extension = source.suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{extension}"
        raw = read_bytes(source)
        if not raw:
            raise AttachmentError("File lampiran tidak dapat dibaca.")
        encrypted = self._crypto_service().encrypt_bytes(raw)
        atomic_write_bytes(self.attachments_dir / stored_name, encrypted)
        return {
            "stored_name": stored_name,
            "original_name": original_name,
            "mime_type": mime_type,
            "size_bytes": size,
            "sha256": sha256_bytes(raw),
        }

    def stored_path(self, stored_name: str) -> Path:
        safe_name = Path(str(stored_name)).name
        return self.attachments_dir / safe_name

    def materialize(self, attachment: dict) -> Path:
        """Decrypts an attachment to a temporary file suitable for opening."""
        stored_name = attachment.get("stored_name", "")
        source = self.stored_path(stored_name)
        if not source.is_file():
            raise AttachmentError("File lampiran tidak ditemukan di storage.")
        try:
            raw = self._crypto_service().decrypt_bytes(read_bytes(source))
        except CryptoError as exc:
            raise AttachmentError(str(exc)) from exc

        temp_root = Path(tempfile.mkdtemp(prefix="keuangan_mandiri_attachment_"))
        display_name = sanitize_filename(attachment.get("original_name", source.name), source.name)
        target = ensure_parent(temp_root / display_name)
        target.write_bytes(raw)
        return target

    def delete_file(self, stored_name: str) -> bool:
        if not stored_name:
            return False
        return safe_unlink(self.stored_path(stored_name))

    def clear_all(self) -> int:
        count = 0
        if not self.attachments_dir.exists():
            return count
        for path in self.attachments_dir.iterdir():
            if path.is_file() and safe_unlink(path):
                count += 1
        return count

    def stats(self) -> dict:
        files = [p for p in self.attachments_dir.glob("*") if p.is_file()]
        total = 0
        for path in files:
            try:
                total += path.stat().st_size
            except OSError:
                pass
        return {"count": len(files), "size_bytes": total, "directory": str(self.attachments_dir)}


_attachment_instance: AttachmentService | None = None


def get_attachment_service() -> AttachmentService:
    global _attachment_instance
    if _attachment_instance is None:
        max_mb = 10
        try:
            from src.storage.config import get_config

            max_mb = int(get_config().get("storage.max_attachment_mb", 10))
        except Exception:
            pass
        _attachment_instance = AttachmentService(max_size_mb=max_mb)
    return _attachment_instance


def reset_attachment_service_for_tests(service: AttachmentService | None = None):
    global _attachment_instance
    _attachment_instance = service
