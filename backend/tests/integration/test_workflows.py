"""Интеграционные тесты полных рабочих сценариев."""

import io
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.interfaces.storage import FileMetadata, StorageResult
from app.infrastructure.api.deps import (
    get_cache,
    get_current_user,
    get_db,
    get_llm_client,
)
from app.infrastructure.api.deps_composites import get_processors, get_storage


class _IntegrationMockStorage:
    """Mock хранилища для интеграционных тестов."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    async def save(self, key: str, content: bytes, content_type: str) -> StorageResult:
        self._files[key] = content
        return StorageResult(
            success=True,
            key=key,
            metadata=FileMetadata(
                filename=key,
                size=len(content),
                content_type=content_type,
                created_at=datetime.now(UTC),
            ),
        )

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


def _make_processor_mock() -> MagicMock:
    from unittest.mock import AsyncMock

    result = MagicMock(success=True, text="Sample thesis content for analysis.", error=None, metadata={})
    proc = MagicMock()
    proc.process_bytes = AsyncMock(return_value=result)
    proc.process = AsyncMock(return_value=result)
    return proc


@pytest.fixture
async def integration_app(db_session: AsyncSession, mock_cache_client, mock_llm_client):
    """Полное тестовое приложение с реальными сервисами и mock-инфраструктурой."""
    from app.infrastructure.api import deps_composites
    from app.infrastructure.api.v1 import analysis, auth, documents, reports

    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")

    storage = _IntegrationMockStorage()
    processors = {
        "txt": _make_processor_mock(),
        "docx": _make_processor_mock(),
        "pdf": _make_processor_mock(),
    }

    deps_composites._logger = MagicMock()

    async def override_get_db():
        yield db_session

    async def override_get_cache():
        return mock_cache_client

    def override_get_llm_client():
        return mock_llm_client

    def override_get_storage():
        return storage

    def override_get_processors():
        return processors

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = override_get_cache
    app.dependency_overrides[get_llm_client] = override_get_llm_client
    app.dependency_overrides[get_storage] = override_get_storage
    app.dependency_overrides[get_processors] = override_get_processors

    with (
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
        patch("app.infrastructure.logging.logger.AppLogger.info"),
        patch("app.infrastructure.logging.logger.AppLogger.error"),
    ):
        yield app


@pytest.fixture
async def integration_client(integration_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=integration_app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.integration
async def test_register_and_login_workflow(integration_client: AsyncClient) -> None:
    """Тест сценария: регистрация → логин → получение токенов."""
    # Регистрация
    register_resp = await integration_client.post(
        "/api/v1/auth/register",
        json={
            "email": "workflow@example.com",
            "password": "WorkflowPass123",
            "full_name": "Workflow User",
        },
    )
    assert register_resp.status_code == 201
    user_data = register_resp.json()
    assert user_data["email"] == "workflow@example.com"
    assert user_data["is_active"] is True

    # Логин
    login_resp = await integration_client.post(
        "/api/v1/auth/login",
        json={"email": "workflow@example.com", "password": "WorkflowPass123"},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


@pytest.mark.integration
async def test_duplicate_registration_rejected(integration_client: AsyncClient) -> None:
    """Тест сценария: повторная регистрация отклоняется."""
    payload = {
        "email": "dup_workflow@example.com",
        "password": "WorkflowPass123",
        "full_name": "Dup Workflow User",
    }
    first = await integration_client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await integration_client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.integration
async def test_token_refresh_workflow(integration_client: AsyncClient) -> None:
    """Тест сценария: логин → обновление токена."""
    await integration_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh_workflow@example.com",
            "password": "WorkflowPass123",
            "full_name": "Refresh Workflow User",
        },
    )
    login_resp = await integration_client.post(
        "/api/v1/auth/login",
        json={"email": "refresh_workflow@example.com", "password": "WorkflowPass123"},
    )
    tokens = login_resp.json()

    refresh_resp = await integration_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"


@pytest.mark.integration
async def test_upload_and_list_documents_workflow(
    integration_app: FastAPI, db_session: AsyncSession
) -> None:
    """Тест сценария: загрузка документов → получение списка."""
    from app.core.domain import User

    test_user = User(
        id="wf-user-docs",
        email="docs_wf@example.com",
        hashed_password="h",
        full_name="Docs WF User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )

    async def override_user():
        return test_user

    integration_app.dependency_overrides[get_current_user] = override_user

    async with AsyncClient(
        transport=ASGITransport(app=integration_app), base_url="http://test"
    ) as c:
        # Upload first document
        r1 = await c.post(
            "/api/v1/documents/upload",
            files={"file": ("thesis.txt", io.BytesIO(b"Thesis content one"), "text/plain")},
        )
        assert r1.status_code == 201
        doc1 = r1.json()
        assert doc1["original_filename"] == "thesis.txt"

        # Upload second document
        r2 = await c.post(
            "/api/v1/documents/upload",
            files={"file": ("thesis2.txt", io.BytesIO(b"Thesis content two"), "text/plain")},
        )
        assert r2.status_code == 201

        # List documents
        list_resp = await c.get("/api/v1/documents/")
        assert list_resp.status_code == 200
        docs = list_resp.json()
        assert len(docs) == 2

        # Get single document
        get_resp = await c.get(f"/api/v1/documents/{doc1['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == doc1["id"]

        # Delete document
        del_resp = await c.delete(f"/api/v1/documents/{doc1['id']}")
        assert del_resp.status_code == 204

        # Verify it's gone
        list_after = await c.get("/api/v1/documents/")
        assert len(list_after.json()) == 1


@pytest.mark.integration
async def test_analysis_workflow(
    integration_app: FastAPI, db_session: AsyncSession
) -> None:
    """Тест сценария: загрузка документа → запуск анализа → получение результата."""
    from app.core.domain import User

    test_user = User(
        id="wf-user-analysis",
        email="analysis_wf@example.com",
        hashed_password="h",
        full_name="Analysis WF User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )

    async def override_user():
        return test_user

    integration_app.dependency_overrides[get_current_user] = override_user

    async with AsyncClient(
        transport=ASGITransport(app=integration_app), base_url="http://test"
    ) as c:
        # Upload document
        upload_resp = await c.post(
            "/api/v1/documents/upload",
            files={"file": ("thesis_for_analysis.txt", io.BytesIO(b"Thesis content"), "text/plain")},
        )
        assert upload_resp.status_code == 201
        doc_id = upload_resp.json()["id"]

        # Start analysis
        analysis_resp = await c.post(
            "/api/v1/analysis/start",
            json={"document_id": doc_id},
        )
        assert analysis_resp.status_code == 202
        analysis_id = analysis_resp.json()["id"]

        # Get analysis status
        status_resp = await c.get(f"/api/v1/analysis/{analysis_id}/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["id"] == analysis_id
        assert "status" in status_data

        # Get analysis details
        detail_resp = await c.get(f"/api/v1/analysis/{analysis_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["document_id"] == doc_id


@pytest.mark.integration
async def test_report_generation_workflow(
    integration_app: FastAPI, db_session: AsyncSession
) -> None:
    """Тест сценария: создание анализа → генерация отчёта → скачивание PDF."""
    from app.core.domain import Analysis, Document, User
    from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
    from app.infrastructure.database.repositories.document_repo import DocumentRepository

    test_user = User(
        id="wf-user-report",
        email="report_wf@example.com",
        hashed_password="h",
        full_name="Report WF User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )

    async def override_user():
        return test_user

    integration_app.dependency_overrides[get_current_user] = override_user

    # Pre-create document and completed analysis directly
    doc = Document(
        id="wf-doc-report",
        user_id=test_user.id,
        filename="wf_report_doc.txt",
        original_filename="wf_report_doc.txt",
        file_size=200,
        file_type="txt",
        file_path="wf_report_doc.txt",
        content="Thesis content for report workflow.",
        created_at=datetime.now(UTC),
    )
    await DocumentRepository(db_session).create(doc)

    analysis = Analysis(
        id="wf-analysis-report",
        document_id=doc.id,
        status="completed",
        overall_score=7.8,
        results={
            "structure": {"score": 8.0, "comments": ["Good"]},
            "style": {"score": 7.5, "comments": ["OK"]},
        },
        created_at=datetime.now(UTC),
    )
    await AnalysisRepository(db_session).create(analysis)

    async with AsyncClient(
        transport=ASGITransport(app=integration_app), base_url="http://test"
    ) as c:
        # Generate and get report
        report_resp = await c.get(
            f"/api/v1/reports/{analysis.id}?generate=true"
        )
        assert report_resp.status_code == 200
        report_data = report_resp.json()
        assert report_data["analysis_id"] == analysis.id
        assert "overall_score" in report_data

        # Download PDF
        pdf_resp = await c.get(f"/api/v1/reports/{analysis.id}/pdf")
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert len(pdf_resp.content) > 0

        # Download DOCX
        docx_resp = await c.get(f"/api/v1/reports/{analysis.id}/docx")
        assert docx_resp.status_code == 200
        assert "wordprocessingml" in docx_resp.headers["content-type"]
