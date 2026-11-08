"""
Small, dependency-free filesystem helpers.

All writes go through a temporary file in the destination directory followed by
``os.replace`` so a crash can never leave a half-written configuration, cache,
backup, or attachment file.
"""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path


_UNSAFE_FILENAME_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def ensure_parent(path: str | os.PathLike[str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def atomic_write_bytes(path: str | os.PathLike[str], data: bytes) -> Path:
    """Writes *data* atomically to *path*."""
    target = ensure_parent(path)
    fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return target


def atomic_write_text(path: str | os.PathLike[str], text: str, encoding: str = "utf-8") -> Path:
    return atomic_write_bytes(path, text.encode(encoding))


def read_text(path: str | os.PathLike[str], default: str = "", encoding: str = "utf-8") -> str:
    try:
        return Path(path).read_text(encoding=encoding)
    except (OSError, UnicodeError):
        return default


def read_bytes(path: str | os.PathLike[str], default: bytes = b"") -> bytes:
    try:
        return Path(path).read_bytes()
    except OSError:
        return default


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_filename(name: str, fallback: str = "file") -> str:
    """Returns a safe, display-only file name (without any directory part)."""
    candidate = Path(str(name or "")).name
    candidate = _UNSAFE_FILENAME_RE.sub("_", candidate).strip(" .")
    return candidate or fallback


def safe_unlink(path: str | os.PathLike[str]) -> bool:
    try:
        Path(path).unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def safe_rmtree(path: str | os.PathLike[str]) -> bool:
    import shutil

    try:
        shutil.rmtree(path, ignore_errors=False)
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def human_size(size_bytes: int | float) -> str:
    value = float(max(0, size_bytes))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"
