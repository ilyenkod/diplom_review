"""API тесты эндпоинтов анализа документов."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Analysis, Document, User
from app.infrastructure.api.deps import get_cache, get_current_user, get_db, get_llm_client
from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
from app.infrastructure.database.repositories.document_repo import DocumentRepository


@pytest.fixture
def test_user() -> User:
    return User(
        id="user-analysis-test",
        email="analysis@example.com",
        hashed_password="hashed_pw",
        full_name="Analysis Test User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
async def test_document(db_session: AsyncSession) -> Document:
    doc = Document(
        id="doc-for-analysis",
        user_id="user-analysis-test",
        filename="test_doc.txt",
        original_filename="test_doc.txt",
        file_size=500,
        file_type="txt",
        file_path="test_doc.txt",
        content="Sample thesis content for analysis testing.",
        created_at=datetime.now(UTC),
    )
    repo = DocumentRepository(db_session)
    return await repo.create(doc)


@pytest.fixture
async def test_analysis(db_session: AsyncSession, test_document: Document) -> Analysis:
    analysis = Analysis(
        id="analysis-test-id",
        document_id=test_document.id,
        status="completed",
        overall_score=7.5,
        results={
            "structure": {"score": 8.0, "comments": ["Good structure"]},
            "style": {"score": 7.0, "comments": ["Acceptable style"]},
        },
        created_at=datetime.now(UTC),
    )
    repo = AnalysisRepository(db_session)
    return await repo.create(analysis)


@pytest.fixture
async def test_app(
    db_session: AsyncSession,
    test_user: User,
    mock_cache_client,
    mock_llm_client,
) -> FastAPI:
    from app.infrastructure.api.v1 import analysis

    app = FastAPI()
    app.include_router(analysis.router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return test_user

    async def override_get_cache():
        return mock_cache_client

    def override_get_llm_client():
        return mock_llm_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_cache] = override_get_cache
    app.dependency_overrides[get_llm_client] = override_get_llm_client
    return app


@pytest.fixture
async def client(test_app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


@pytest.mark.unit
async def test_start_analysis_success(client: AsyncClient, test_document: Document) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.post(
            "/api/v1/analysis/start",
            json={"document_id": test_document.id},
        )
    assert response.status_code == 202
    data = response.json()
    assert data["document_id"] == test_document.id
    assert "id" in data
    assert "status" in data


@pytest.mark.unit
async def test_start_analysis_document_not_found(client: AsyncClient) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.warning"):
        response = await client.post(
            "/api/v1/analysis/start",
            json={"document_id": "nonexistent-doc"},
        )
    assert response.status_code == 404


@pytest.mark.unit
async def test_get_analysis_status_success(
    client: AsyncClient, test_analysis: Analysis
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(f"/api/v1/analysis/{test_analysis.id}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_analysis.id
    assert "status" in data
    assert "progress" in data


@pytest.mark.unit
async def test_get_analysis_status_not_found(client: AsyncClient) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.warning"):
        response = await client.get("/api/v1/analysis/nonexistent-id/status")
    assert response.status_code == 404


@pytest.mark.unit
async def test_get_analysis_success(client: AsyncClient, test_analysis: Analysis) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(f"/api/v1/analysis/{test_analysis.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_analysis.id
    assert data["document_id"] == test_analysis.document_id
    assert "criteria_scores" in data
    assert "recommendations" in data


@pytest.mark.unit
async def test_get_analysis_not_found(client: AsyncClient) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.warning"):
        response = await client.get("/api/v1/analysis/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.unit
async def test_reanalyze_success(client: AsyncClient, test_analysis: Analysis) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.post(
            f"/api/v1/analysis/{test_analysis.id}/reanalyze",
            json={"document_id": test_analysis.document_id, "force": True},
        )
    assert response.status_code == 202
    data = response.json()
    assert data["document_id"] == test_analysis.document_id


@pytest.mark.unit
async def test_reanalyze_analysis_not_found(client: AsyncClient) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.warning"):
        response = await client.post(
            "/api/v1/analysis/nonexistent-id/reanalyze",
            json={"document_id": "some-doc", "force": False},
        )
    assert response.status_code == 404
