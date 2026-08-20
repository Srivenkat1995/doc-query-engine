from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol, runtime_checkable

from app.config import get_settings


@runtime_checkable
class Storage(Protocol):
    """Minimal binary storage contract for uploaded documents."""

    def put(self, key: str, content: bytes) -> None:
        """Persist content under a storage key."""

    def get(self, key: str) -> bytes:
        """Read content for a storage key."""

    def delete(self, key: str) -> bool:
        """Delete content and report whether it existed."""


def _safe_relative_key(key: str) -> Path:
    path = Path(key)
    if not key or path.is_absolute() or ".." in path.parts:
        raise ValueError("Storage key must be a non-empty relative path")
    return path


class LocalStorage:
    """Filesystem storage rooted inside one configured directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        relative_path = _safe_relative_key(key)
        path = (self.root / relative_path).resolve()
        if self.root != path and self.root not in path.parents:
            raise ValueError("Storage key escapes the configured root")
        return path

    def put(self, key: str, content: bytes) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)

    def get(self, key: str) -> bytes:
        return self._path_for(key).read_bytes()

    def delete(self, key: str) -> bool:
        path = self._path_for(key)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        return True


@lru_cache
def get_storage() -> LocalStorage:
    """Return the process-local storage adapter for API dependencies."""

    return LocalStorage(Path(get_settings().storage_root))
