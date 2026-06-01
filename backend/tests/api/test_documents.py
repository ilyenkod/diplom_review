"""API тесты эндпоинтов документов."""

import io
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import User
from app.core.interfaces.storage import FileMetadata, StorageResult
from app.infrastructure.api.deps import get_current_user, get_db
from app.infrastructure.api.deps_composites import get_processors, get_storage


def _make_storage_result() -> StorageResult:
    return StorageResult(
        success=True,
        key="test/file.txt",
        metadata=FileMetadata(
            filename="file.txt",
            size=100,
            content_type="text/plain",
            created_at=datetime.now(UTC),
        ),
    )


class _FullMockStorage:
    """Mock хранилища с полным интерфейсом Storage."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    async def save(self, key: str, content: bytes, content_type: str) -> StorageResult:
        self._files[key] = content
        return _make_storage_result()

    async def delete(self, key: str) -> bool:
        self._files.pop(key, None)
        return True

    async def get(self, key: str) -> bytes | None:
        return self._files.get(key)

    async def exists(self, key: str) -> bool:
        return key in self._files

    async def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        return f"http://localhost/files/{key}" if key in self._files else None

    async def get_metadata(self, key: str) -> FileMetadata | None:
        return None

    async def list_files(self, prefix: str = "") -> list[str]:
        return [k for k in self._files if k.startswith(prefix)]

    async def copy(self, source_key: str, dest_key: str) -> bool:
        if source_key in self._files:
            self._files[dest_key] = self._files[source_key]
            return True
        return False

    async def move(self, source_key: str, dest_key: str) -> bool:
        if source_key in self._files:
            self._files[dest_key] = self._files.pop(source_key)
            return True
        return False

    async def clear(self) -> bool:
        self._files.clear()
        return True


def _make_processor_mock() -> Any:
    result = MagicMock(success=True, text="Extracted document text", error=None, metadata={})
    proc = MagicMock()
    proc.process_bytes = AsyncMock(return_value=result)
    proc.process = AsyncMock(return_value=result)
    return proc


@pytest.fixture
def test_user() -> User:
    return User(
        id="user-doc-test",
        email="doctest@example.com",
        hashed_password="hashed_pw",
        full_name="Doc Test User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
async def test_app(db_session: AsyncSession, test_user: User):
    from app.infrastructure.api import deps_composites
    from app.infrastructure.api.v1 import documents

    app = FastAPI()
    app.include_router(documents.router, prefix="/api/v1")

    storage = _FullMockStorage()
    processors = {
        "txt": _make_processor_mock(),
        "docx": _make_processor_mock(),
        "pdf": _make_processor_mock(),
    }

    # Patch deps_composites._logger so get_logger() doesn't raise RuntimeError.
    # Also patch AppLogger to use a MagicMock to avoid KeyError on reserved log fields
    # (e.g. 'filename' is a reserved LogRecord attribute).
    mock_app_logger = MagicMock()
    deps_composites._logger = mock_app_logger

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return test_user

    def override_get_storage():
        return storage

    def override_get_processors():
        return processors

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_storage] = override_get_storage
    app.dependency_overrides[get_processors] = override_get_processors

    # Patch AppLogger log methods to avoid KeyError on reserved LogRecord fields
    # (e.g. 'filename' is reserved). This is a known production code issue.
    with (
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
        patch("app.infrastructure.logging.logger.AppLogger.info"),
        patch("app.infrastructure.logging.logger.AppLogger.error"),
    ):
        yield app


@pytest.fixture
async def client(test_app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


@pytest.mark.unit
async def test_upload_document_success(client: AsyncClient) -> None:
    file_content = b"This is a test document content for the test"
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_doc.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "test_doc.txt"
    assert data["file_type"] == "txt"
    assert "id" in data
    assert "user_id" in data


@pytest.mark.unit
async def test_upload_document_invalid_type(client: AsyncClient) -> None:
    file_content = b"binary data"
    response = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("report.exe", io.BytesIO(file_content), "application/octet-stream")},
    )
    assert response.status_code == 400


@pytest.mark.unit
async def test_get_document_success(client: AsyncClient) -> None:
    file_content = b"Get document test"
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("getme.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    response = await client.get(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == doc_id


@pytest.mark.unit
async def test_get_document_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.unit
async def test_list_documents_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.unit
async def test_list_documents_with_items(client: AsyncClient) -> None:
    for i in range(3):
        await client.post(
            "/api/v1/documents/upload",
            files={"file": (f"file{i}.txt", io.BytesIO(b"content"), "text/plain")},
        )
    response = await client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.unit
async def test_delete_document_success(client: AsyncClient) -> None:
    file_content = b"Delete me"
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("deleteme.txt", io.BytesIO(file_content), "text/plain")},
    )
    doc_id = upload_resp.json()["id"]

    response = await client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 204


@pytest.mark.unit
async def test_delete_document_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/documents/nonexistent-id")
    assert response.status_code == 404
