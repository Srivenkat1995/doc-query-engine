from pathlib import Path

import pytest

from app.storage import LocalStorage, Storage


def test_local_storage_implements_storage_protocol(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)

    assert isinstance(storage, Storage)


def test_local_storage_put_get_and_delete(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    key = "invoices/example.pdf"
    content = b"invoice bytes"

    storage.put(key, content)

    assert storage.get(key) == content
    assert (tmp_path / key).read_bytes() == content
    assert storage.delete(key) is True
    assert storage.delete(key) is False


def test_local_storage_replaces_existing_content_atomically(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    key = "invoices/example.pdf"

    storage.put(key, b"old")
    storage.put(key, b"new")

    assert storage.get(key) == b"new"
    assert list((tmp_path / "invoices").iterdir()) == [tmp_path / key]


@pytest.mark.parametrize("key", ["", "/tmp/file", "../file", "invoices/../../file"])
def test_local_storage_rejects_unsafe_keys(tmp_path: Path, key: str) -> None:
    storage = LocalStorage(tmp_path)

    with pytest.raises(ValueError, match="relative path|configured root"):
        storage.put(key, b"content")
