"""
Persistent, version-aware cache for derived dashboard data.

Cache entries are invalidated when the database's ``data_version`` changes, when
their TTL expires, or when the user clears the cache explicitly.  Payloads are
encrypted with the same key as sensitive database fields.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable

from src.storage.crypto import CryptoError, get_crypto
from src.storage.file_store import atomic_write_text, human_size, read_text, safe_unlink
from src.storage.paths import StoragePaths, storage_paths


class CacheManager:
    def __init__(
        self,
        base_dir: str | os.PathLike[str] | None = None,
        *,
        ttl_seconds: int = 300,
        version_provider: Callable[[], int | str] | None = None,
        crypto=None,
        paths: StoragePaths | None = None,
    ):
        self.paths = paths or storage_paths
        self.cache_dir = Path(base_dir) if base_dir else self.paths.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = max(0, int(ttl_seconds))
        self._version_provider = version_provider or self._database_version
        self._crypto = crypto
        self._lock = threading.RLock()

    @staticmethod
    def _database_version() -> int:
        try:
            from src.database.db_manager import get_db

            return get_db().get_data_version()
        except Exception:
            return 0

    def _file_for(self, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
        return self.cache_dir / f"{digest}.json"

    def _crypto_service(self):
        if self._crypto is not None:
            return self._crypto
        return get_crypto()

    def get(self, key: str, ttl_seconds: int | None = None) -> Any | None:
        with self._lock:
            path = self._file_for(key)
            raw = read_text(path, "")
            if not raw:
                return None
            try:
                envelope = json.loads(raw)
                ttl = self.ttl_seconds if ttl_seconds is None else max(0, int(ttl_seconds))
                if ttl and (time.time() - float(envelope.get("created_at", 0))) > ttl:
                    safe_unlink(path)
                    return None
                if str(envelope.get("data_version")) != str(self._version_provider()):
                    safe_unlink(path)
                    return None
                payload = envelope.get("payload", "")
                if envelope.get("encrypted"):
                    payload = self._crypto_service().decrypt_text(payload)
                return json.loads(payload)
            except (ValueError, TypeError, CryptoError, json.JSONDecodeError):
                safe_unlink(path)
                return None

    def set(self, key: str, value: Any) -> bool:
        with self._lock:
            try:
                payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                payload = self._crypto_service().encrypt_text(payload)
                envelope = {
                    "key": key,
                    "created_at": time.time(),
                    "data_version": self._version_provider(),
                    "encrypted": True,
                    "payload": payload,
                }
                atomic_write_text(self._file_for(key), json.dumps(envelope, ensure_ascii=False))
                return True
            except (TypeError, ValueError, CryptoError):
                return False

    def invalidate(self, key: str | None = None):
        with self._lock:
            if key is not None:
                safe_unlink(self._file_for(key))
                return
            for path in self.cache_dir.glob("*.json"):
                safe_unlink(path)

    clear = invalidate

    def stats(self) -> dict:
        files = list(self.cache_dir.glob("*.json"))
        total = 0
        for path in files:
            try:
                total += path.stat().st_size
            except OSError:
                pass
        return {
            "entries": len(files),
            "size_bytes": total,
            "size_human": human_size(total),
            "directory": str(self.cache_dir),
            "ttl_seconds": self.ttl_seconds,
        }


_cache_instance: CacheManager | None = None
_cache_lock = threading.Lock()


def get_cache() -> CacheManager:
    """Returns the process-wide cache manager."""
    global _cache_instance
    with _cache_lock:
        if _cache_instance is None:
            ttl = 300
            try:
                from src.storage.config import get_config

                config = get_config()
                if not config.get("cache.enabled", True):
                    ttl = 0
                else:
                    ttl = int(config.get("cache.ttl_seconds", 300))
            except Exception:
                pass
            _cache_instance = CacheManager(ttl_seconds=ttl)
        return _cache_instance


def reset_cache_for_tests(manager: CacheManager | None = None):
    global _cache_instance
    with _cache_lock:
        _cache_instance = manager
