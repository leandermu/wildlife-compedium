"""Storage abstraction.

The rest of the app only ever deals with opaque `storage_key` strings and asks
this module for a public URL. Swapping local disk for S3/R2 later means adding
one subclass and flipping WC_STORAGE_BACKEND.
"""

from __future__ import annotations

import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from .config import settings

ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".heic", ".heif"}


class Storage(ABC):
    @abstractmethod
    def save(self, prefix: str, filename: str, fileobj: BinaryIO) -> str: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def url(self, key: str | None) -> str | None: ...

    @abstractmethod
    def path(self, key: str) -> Path | None:
        """Local filesystem path if this backend has one (used by ZIP export)."""

    @staticmethod
    def build_key(prefix: str, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            suffix = ".jpg"
        return f"{prefix.strip('/')}/{uuid.uuid4().hex}{suffix}"


class LocalStorage(Storage):
    def __init__(self, root: Path, base_url: str) -> None:
        self.root = root
        self.base_url = base_url.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def _abs(self, key: str) -> Path:
        target = (self.root / key).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise ValueError("Ungültiger Storage-Key")
        return target

    def save(self, prefix: str, filename: str, fileobj: BinaryIO) -> str:
        key = self.build_key(prefix, filename)
        dest = self._abs(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            shutil.copyfileobj(fileobj, fh)
        return key

    def save_bytes(self, key: str, data: bytes) -> str:
        dest = self._abs(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return key

    def delete(self, key: str) -> None:
        try:
            self._abs(key).unlink(missing_ok=True)
        except ValueError:
            pass

    def url(self, key: str | None) -> str | None:
        if not key:
            return None
        if key.startswith(("http://", "https://", "/")):
            return key
        return f"{self.base_url}/{key}"

    def path(self, key: str) -> Path | None:
        try:
            p = self._abs(key)
        except ValueError:
            return None
        return p if p.exists() else None


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        if settings.storage_backend != "local":
            raise RuntimeError(
                f"Storage-Backend '{settings.storage_backend}' ist noch nicht implementiert"
            )
        _storage = LocalStorage(settings.local_media_path, settings.media_base_url)
    return _storage


def media_url(key: str | None) -> str | None:
    return get_storage().url(key)
