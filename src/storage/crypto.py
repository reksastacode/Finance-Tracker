"""
Encryption services for sensitive user data.

Text values are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) and carry the
``enc:v1:`` marker so encryption is idempotent and old plaintext rows can be
migrated safely.

On Windows the Fernet key itself is wrapped with the current user's DPAPI
profile (no password prompt).  The key is therefore transparent to the user but
cannot be moved to another Windows account or machine.  On non-Windows systems
the key falls back to a restrictive local file and a warning is exposed through
``key_backend``.
"""
from __future__ import annotations

import ctypes
import os
import sys
import threading
from ctypes import wintypes
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from src.storage.file_store import atomic_write_bytes, read_bytes
from src.storage.paths import StoragePaths, storage_paths


ENCRYPTION_PREFIX = "enc:v1:"


class CryptoError(RuntimeError):
    """Raised when a key cannot be created, wrapped, or unwrapped."""


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_byte)),
    ]


def _as_blob(data: bytes):
    buffer = ctypes.create_string_buffer(data, len(data))
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    return blob, buffer


def _dpapi_call(function_name: str, data: bytes, entropy: bytes) -> bytes:
    if sys.platform != "win32":
        raise CryptoError("Windows DPAPI is not available on this platform")

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    function = getattr(crypt32, function_name)

    data_blob, data_buffer = _as_blob(data)
    entropy_blob, entropy_buffer = _as_blob(entropy)
    output_blob = _DataBlob()

    function.argtypes = [
        ctypes.POINTER(_DataBlob),
        wintypes.LPCWSTR,
        ctypes.POINTER(_DataBlob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(_DataBlob),
    ]
    function.restype = wintypes.BOOL

    description = "Keuangan Mandiri data key"
    flags = 0x1  # CRYPTPROTECT_UI_FORBIDDEN
    ok = function(
        ctypes.byref(data_blob),
        description,
        ctypes.byref(entropy_blob),
        None,
        None,
        flags,
        ctypes.byref(output_blob),
    )
    if not ok:
        raise CryptoError(f"DPAPI {function_name} failed (error {ctypes.get_last_error()})")
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(output_blob.pbData)


def _dpapi_protect(data: bytes, entropy: bytes) -> bytes:
    return _dpapi_call("CryptProtectData", data, entropy)


def _dpapi_unprotect(data: bytes, entropy: bytes) -> bytes:
    return _dpapi_call("CryptUnprotectData", data, entropy)


class CryptoService:
    """Fernet encryption with a DPAPI-wrapped key."""

    def __init__(
        self,
        key_path: str | os.PathLike[str] | None = None,
        *,
        use_dpapi: bool | None = None,
        fernet_key: bytes | str | None = None,
    ):
        self.paths = storage_paths
        self.key_path = Path(key_path) if key_path else self.paths.secrets_dir / "master.key.dpapi"
        self._lock = threading.RLock()
        self._entropy = b"KeuanganMandiri:v1"

        if use_dpapi is None:
            use_dpapi = sys.platform == "win32"
        self.use_dpapi = bool(use_dpapi)

        if fernet_key is not None:
            key = fernet_key.encode("ascii") if isinstance(fernet_key, str) else bytes(fernet_key)
            self._fernet = Fernet(key)
            self.key_backend = "injected"
        else:
            key, backend = self._load_or_create_key()
            self._fernet = Fernet(key)
            self.key_backend = backend

    # ------------------------------------------------------------------
    # Key lifecycle
    # ------------------------------------------------------------------
    def _load_or_create_key(self) -> tuple[bytes, str]:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)

        if self.key_path.exists():
            wrapped = read_bytes(self.key_path)
            if not wrapped:
                raise CryptoError(f"Encryption key file is empty: {self.key_path}")
            if self.key_path.suffix == ".dpapi":
                try:
                    return _dpapi_unprotect(wrapped, self._entropy), "dpapi"
                except CryptoError as exc:
                    raise CryptoError(
                        "Kunci enkripsi tidak dapat dibuka oleh profil Windows saat ini. "
                        "Pastikan aplikasi dijalankan oleh pengguna Windows yang sama."
                    ) from exc
            return wrapped, "local-file"

        key = Fernet.generate_key()
        if self.use_dpapi:
            try:
                wrapped = _dpapi_protect(key, self._entropy)
                atomic_write_bytes(self.key_path, wrapped)
                return key, "dpapi"
            except CryptoError:
                # A machine can report Windows without a usable DPAPI profile
                # (for example a restricted CI runner).  Fall back explicitly
                # rather than preventing the whole application from starting.
                self.key_path = self.key_path.with_suffix("")
        atomic_write_bytes(self.key_path, key)
        try:
            os.chmod(self.key_path, 0o600)
        except OSError:
            pass
        return key, "local-file"

    # ------------------------------------------------------------------
    # Text and bytes
    # ------------------------------------------------------------------
    @staticmethod
    def is_encrypted(value: str | None) -> bool:
        return bool(value) and value.startswith(ENCRYPTION_PREFIX)

    def encrypt_text(self, value: str | None) -> str:
        if value is None or value == "":
            return value or ""
        if self.is_encrypted(value):
            return value
        token = self._fernet.encrypt(value.encode("utf-8")).decode("ascii")
        return ENCRYPTION_PREFIX + token

    def decrypt_text(self, value: str | None) -> str:
        if value is None or value == "":
            return value or ""
        if not self.is_encrypted(value):
            return value
        token = value[len(ENCRYPTION_PREFIX):].encode("ascii")
        try:
            return self._fernet.decrypt(token).decode("utf-8")
        except InvalidToken as exc:
            raise CryptoError("Data terenkripsi tidak dapat didekripsi dengan kunci saat ini.") from exc

    def encrypt_bytes(self, data: bytes) -> bytes:
        return self._fernet.encrypt(data)

    def decrypt_bytes(self, token: bytes) -> bytes:
        try:
            return self._fernet.decrypt(token)
        except InvalidToken as exc:
            raise CryptoError("File terenkripsi tidak dapat didekripsi dengan kunci saat ini.") from exc


_crypto_instance: CryptoService | None = None
_crypto_lock = threading.Lock()


def get_crypto() -> CryptoService:
    """Returns the process-wide crypto service."""
    global _crypto_instance
    with _crypto_lock:
        if _crypto_instance is None:
            _crypto_instance = CryptoService()
        return _crypto_instance


def reset_crypto_for_tests(service: CryptoService | None = None):
    """Replaces/invalidates the singleton (used only by isolated tests)."""
    global _crypto_instance
    with _crypto_lock:
        _crypto_instance = service
