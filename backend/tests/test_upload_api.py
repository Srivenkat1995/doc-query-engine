from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app
from app.storage import Storage, get_storage
from app.upload_validation import MAX_UPLOAD_BYTES


class MemoryStorage:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.fail_put = False

    def put(self, key: str, content: bytes) -> None:
        if self.fail_put:
            raise OSError("storage unavailable")
        self.files[key] = content

    def get(self, key: str) -> bytes:
        return self.files[key]

    def delete(self, key: str) -> bool:
        return self.files.pop(key, None) is not None


@pytest.fixture
def upload_client() -> Generator[tuple[TestClient, MemoryStorage], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(engine)
    storage = MemoryStorage()

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def override_get_storage() -> Storage:
        return storage

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage
    try:
        yield TestClient(app), storage
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_upload_persists_file_and_invoice(
    upload_client: tuple[TestClient, MemoryStorage],
) -> None:
    client, storage = upload_client

    response = client.post(
        "/invoices/upload",
        files={"file": ("invoice.pdf", b"invoice bytes", "application/pdf")},
    )

    assert response.status_code == 201
    invoice = response.json()
    assert invoice["status"] == "uploaded"
    assert invoice["original_filename"] == "invoice.pdf"
    assert invoice["size_bytes"] == len(b"invoice bytes")
    assert storage.files[invoice["storage_key"]] == b"invoice bytes"


def test_upload_rejects_unsupported_file_without_storage_write(
    upload_client: tuple[TestClient, MemoryStorage],
) -> None:
    client, storage = upload_client

    response = client.post(
        "/invoices/upload",
        files={"file": ("notes.txt", b"not an invoice", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unsupported_type"
    assert storage.files == {}


def test_upload_returns_storage_failure_without_invoice(
    upload_client: tuple[TestClient, MemoryStorage],
) -> None:
    client, storage = upload_client
    storage.fail_put = True

    response = client.post(
        "/invoices/upload",
        files={"file": ("invoice.pdf", b"invoice bytes", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_unavailable"
    assert storage.files == {}


def test_upload_rejects_empty_file_without_storage_write(
    upload_client: tuple[TestClient, MemoryStorage],
) -> None:
    client, storage = upload_client

    response = client.post(
        "/invoices/upload",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "empty_file"
    assert storage.files == {}


def test_upload_rejects_file_over_limit_without_storage_write(
    upload_client: tuple[TestClient, MemoryStorage],
) -> None:
    client, storage = upload_client

    response = client.post(
        "/invoices/upload",
        files={
            "file": (
                "large.pdf",
                b"x" * (MAX_UPLOAD_BYTES + 1),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "file_too_large"
    assert storage.files == {}


def test_upload_deletes_file_when_database_commit_fails(
    upload_client: tuple[TestClient, MemoryStorage],
) -> None:
    client, storage = upload_client
    app = client.app
    original_get_db = app.dependency_overrides[get_db]

    def failing_get_db() -> Generator[Session, None, None]:
        db_generator = original_get_db()
        session = next(db_generator)

        def fail_commit() -> None:
            raise RuntimeError("database unavailable")

        session.commit = fail_commit  # type: ignore[method-assign]
        try:
            yield session
        finally:
            session.close()
            db_generator.close()

    app.dependency_overrides[get_db] = failing_get_db
    try:
        response = client.post(
            "/invoices/upload",
            files={"file": ("invoice.pdf", b"invoice bytes", "application/pdf")},
        )
    finally:
        app.dependency_overrides[get_db] = original_get_db

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "persistence_failed"
    assert storage.files == {}
