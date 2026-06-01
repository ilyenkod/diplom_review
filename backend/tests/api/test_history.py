"""API тесты эндпоинтов истории версий документов."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Analysis, Document, History, User
from app.infrastructure.api.deps import get_current_user, get_db
from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.database.repositories.history_repo import HistoryRepository


@pytest.fixture
def test_user() -> User:
    return User(
        id="user-history-test",
        email="history@example.com",
        hashed_password="hashed_pw",
        full_name="History Test User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
async def test_document(db_session: AsyncSession) -> Document:
    doc = Document(
        id="doc-history-test",
        user_id="user-history-test",
        filename="history_doc.txt",
        original_filename="history_doc.txt",
        file_size=300,
        file_type="txt",
        file_path="history_doc.txt",
        content="Document content for history testing.",
        created_at=datetime.now(UTC),
    )
    repo = DocumentRepository(db_session)
    return await repo.create(doc)


@pytest.fixture
async def test_analysis_v1(
    db_session: AsyncSession, test_document: Document
) -> Analysis:
    analysis = Analysis(
        id="analysis-hist-v1",
        document_id=test_document.id,
        status="completed",
        overall_score=6.5,
        results={"structure": {"score": 6.5}},
        created_at=datetime.now(UTC),
    )
    repo = AnalysisRepository(db_session)
    return await repo.create(analysis)


@pytest.fixture
async def test_analysis_v2(
    db_session: AsyncSession, test_document: Document
) -> Analysis:
    analysis = Analysis(
        id="analysis-hist-v2",
        document_id=test_document.id,
        status="completed",
        overall_score=8.0,
        results={"structure": {"score": 8.0}},
        created_at=datetime.now(UTC),
    )
    repo = AnalysisRepository(db_session)
    return await repo.create(analysis)


@pytest.fixture
async def test_history_v1(
    db_session: AsyncSession, test_document: Document, test_analysis_v1: Analysis
) -> History:
    history = History(
        id="history-v1-id",
        document_id=test_document.id,
        version_number=1,
        analysis_id=test_analysis_v1.id,
        changes_summary={"overall_score_diff": None, "summary": "Initial version"},
        created_at=datetime.now(UTC),
    )
    repo = HistoryRepository(db_session)
    return await repo.create(history)


@pytest.fixture
async def test_history_v2(
    db_session: AsyncSession, test_document: Document, test_analysis_v2: Analysis
) -> History:
    history = History(
        id="history-v2-id",
        document_id=test_document.id,
        version_number=2,
        analysis_id=test_analysis_v2.id,
        changes_summary={"overall_score_diff": 1.5, "summary": "Improved version"},
        created_at=datetime.now(UTC),
    )
    repo = HistoryRepository(db_session)
    return await repo.create(history)


@pytest.fixture
async def test_app(db_session: AsyncSession, test_user: User):
    from app.infrastructure.api.v1 import history

    app = FastAPI()
    app.include_router(history.router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return app


@pytest.fixture
async def client(test_app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


@pytest.mark.unit
async def test_get_history_empty(client: AsyncClient, test_user: User) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get("/api/v1/history/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.unit
async def test_get_history_with_records(
    client: AsyncClient, test_history_v1: History
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get("/api/v1/history/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["document_id"] == test_history_v1.document_id


@pytest.mark.unit
async def test_get_history_filter_by_document(
    client: AsyncClient,
    test_document: Document,
    test_history_v1: History,
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(
            f"/api/v1/history/?document_id={test_document.id}"
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.unit
async def test_get_history_filter_document_not_found(client: AsyncClient) -> None:
    with (
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
        patch("app.infrastructure.logging.logger.AppLogger.info"),
    ):
        response = await client.get("/api/v1/history/?document_id=nonexistent-doc")
    assert response.status_code == 404


@pytest.mark.unit
async def test_get_document_versions_success(
    client: AsyncClient,
    test_document: Document,
    test_history_v1: History,
    test_history_v2: History,
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(
            f"/api/v1/history/{test_document.id}/versions"
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    version_numbers = [item["version_number"] for item in data]
    assert 1 in version_numbers
    assert 2 in version_numbers


@pytest.mark.unit
async def test_get_document_versions_not_found(client: AsyncClient) -> None:
    with (
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
        patch("app.infrastructure.logging.logger.AppLogger.info"),
    ):
        response = await client.get("/api/v1/history/nonexistent-doc/versions")
    assert response.status_code == 404


@pytest.mark.unit
async def test_compare_versions_success(
    client: AsyncClient,
    test_document: Document,
    test_history_v1: History,
    test_history_v2: History,
) -> None:
    # The /compare endpoint uses a Pydantic model parameter which FastAPI 0.135+
    # treats as a request body even for GET requests.
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.request(
            "GET",
            "/api/v1/history/compare",
            json={
                "document_id": test_document.id,
                "version_from": 1,
                "version_to": 2,
            },
        )
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == test_document.id
    assert "overall_score_diff" in data
    assert "improved" in data
    assert "degraded" in data


@pytest.mark.unit
async def test_compare_versions_document_not_found(client: AsyncClient) -> None:
    with (
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
        patch("app.infrastructure.logging.logger.AppLogger.info"),
    ):
        response = await client.request(
            "GET",
            "/api/v1/history/compare",
            json={
                "document_id": "nonexistent-doc",
                "version_from": 1,
                "version_to": 2,
            },
        )
    assert response.status_code == 404
