"""API тесты эндпоинтов отчетов."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Analysis, Document, Report, User
from app.infrastructure.api.deps import get_current_user, get_db, get_llm_client
from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.database.repositories.report_repo import ReportRepository


@pytest.fixture
def test_user() -> User:
    return User(
        id="user-reports-test",
        email="reports@example.com",
        hashed_password="hashed_pw",
        full_name="Reports Test User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
async def test_document(db_session: AsyncSession) -> Document:
    doc = Document(
        id="doc-for-reports",
        user_id="user-reports-test",
        filename="report_doc.txt",
        original_filename="report_doc.txt",
        file_size=500,
        file_type="txt",
        file_path="report_doc.txt",
        content="Thesis content for report testing.",
        created_at=datetime.now(UTC),
    )
    repo = DocumentRepository(db_session)
    return await repo.create(doc)


@pytest.fixture
async def test_analysis(db_session: AsyncSession, test_document: Document) -> Analysis:
    analysis = Analysis(
        id="analysis-reports-test",
        document_id=test_document.id,
        status="completed",
        overall_score=8.0,
        results={
            "structure": {"score": 8.0, "comments": ["Good"]},
            "style": {"score": 8.0, "comments": ["OK"]},
        },
        created_at=datetime.now(UTC),
    )
    repo = AnalysisRepository(db_session)
    return await repo.create(analysis)


@pytest.fixture
async def test_report(db_session: AsyncSession, test_analysis: Analysis) -> Report:
    report = Report(
        id="report-test-id",
        analysis_id=test_analysis.id,
        overall_assessment="Good work (8.0/10.0)",
        recommendations=["Improve conclusions"],
        supervisor_comments=["Well structured"],
        generated_at=datetime.now(UTC),
    )
    repo = ReportRepository(db_session)
    return await repo.create(report)


@pytest.fixture
async def test_app(
    db_session: AsyncSession,
    test_user: User,
    mock_llm_client,
):
    from app.infrastructure.api.v1 import reports

    app = FastAPI()
    app.include_router(reports.router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return test_user

    def override_get_llm_client():
        return mock_llm_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_llm_client] = override_get_llm_client
    return app


@pytest.fixture
async def client(test_app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


@pytest.mark.unit
async def test_get_report_success(
    client: AsyncClient, test_analysis: Analysis, test_report: Report
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(f"/api/v1/reports/{test_analysis.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == test_analysis.id
    assert "overall_score" in data
    assert "recommendations" in data
    assert "strengths" in data
    assert "weaknesses" in data


@pytest.mark.unit
async def test_get_report_not_found_no_generate(
    client: AsyncClient, test_analysis: Analysis
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(f"/api/v1/reports/{test_analysis.id}")
    assert response.status_code == 404


@pytest.mark.unit
async def test_get_report_with_generate_flag(
    client: AsyncClient, test_analysis: Analysis
) -> None:
    with (
        patch("app.infrastructure.logging.logger.AppLogger.info"),
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
    ):
        response = await client.get(
            f"/api/v1/reports/{test_analysis.id}?generate=true"
        )
    assert response.status_code == 200
    data = response.json()
    assert data["analysis_id"] == test_analysis.id


@pytest.mark.unit
async def test_get_report_analysis_not_found(client: AsyncClient) -> None:
    with (
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
        patch("app.infrastructure.logging.logger.AppLogger.info"),
    ):
        response = await client.get("/api/v1/reports/nonexistent-analysis")
    assert response.status_code == 404


@pytest.mark.unit
async def test_download_report_pdf_success(
    client: AsyncClient, test_analysis: Analysis, test_report: Report
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(f"/api/v1/reports/{test_analysis.id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0


@pytest.mark.unit
async def test_download_report_pdf_generates_if_missing(
    client: AsyncClient, test_analysis: Analysis
) -> None:
    with (
        patch("app.infrastructure.logging.logger.AppLogger.info"),
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
    ):
        response = await client.get(f"/api/v1/reports/{test_analysis.id}/pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


@pytest.mark.unit
async def test_download_report_docx_success(
    client: AsyncClient, test_analysis: Analysis, test_report: Report
) -> None:
    with patch("app.infrastructure.logging.logger.AppLogger.info"):
        response = await client.get(f"/api/v1/reports/{test_analysis.id}/docx")
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]
    assert len(response.content) > 0


@pytest.mark.unit
async def test_download_report_docx_analysis_not_found(client: AsyncClient) -> None:
    with (
        patch("app.infrastructure.logging.logger.AppLogger.warning"),
        patch("app.infrastructure.logging.logger.AppLogger.error"),
    ):
        response = await client.get("/api/v1/reports/nonexistent-analysis/docx")
    assert response.status_code == 404
