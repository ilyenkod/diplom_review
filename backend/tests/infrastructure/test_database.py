"""
Unit-тесты для репозиториев базы данных.

Тестирует все репозитории:
- BaseRepository
- UserRepository
- DocumentRepository
- AnalysisRepository
- ReportRepository
- HistoryRepository
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.core.const import AnalysisStatus
from app.core.domain import Analysis, Document, History, Report, User


# ========== BaseRepository Tests ==========


@pytest.mark.unit
class TestBaseRepository:
    """Тесты для базового репозитория."""

    @pytest.mark.asyncio
    async def test_create_entity(self, user_repository, sample_user):
        """Тестирует создание сущности."""
        created_user = await user_repository.create(sample_user)

        assert created_user.id == sample_user.id
        assert created_user.email == sample_user.email

    @pytest.mark.asyncio
    async def test_get_by_id(self, user_repository, sample_user):
        """Тестирует получение сущности по ID."""
        await user_repository.create(sample_user)

        found_user = await user_repository.get_by_id(sample_user.id)

        assert found_user is not None
        assert found_user.id == sample_user.id
        assert found_user.email == sample_user.email

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository):
        """Тестирует получение несуществующей сущности."""
        found_user = await user_repository.get_by_id("nonexistent-id")

        assert found_user is None

    @pytest.mark.asyncio
    async def test_get_all(self, user_repository, sample_user):
        """Тестирует получение всех сущностей."""
        await user_repository.create(sample_user)

        users = await user_repository.get_all()

        assert len(users) == 1
        assert users[0].id == sample_user.id

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, user_repository, sample_user):
        """Тестирует пагинацию при получении всех сущностей."""
        # Create multiple users
        for i in range(5):
            user = User(
                id=f"user-{i}",
                email=f"test{i}@example.com",
                hashed_password="hashed",
                full_name=f"Test User {i}",
                is_active=True,
                role="student",
                created_at=datetime.now(UTC),
            )
            await user_repository.create(user)

        # Test limit
        users = await user_repository.get_all(limit=2, offset=0)
        assert len(users) == 2

        # Test offset
        users = await user_repository.get_all(limit=2, offset=2)
        assert len(users) == 2

    @pytest.mark.asyncio
    async def test_update_entity(self, user_repository, sample_user):
        """Тестирует обновление сущности."""
        await user_repository.create(sample_user)

        sample_user.full_name = "Updated Name"
        updated_user = await user_repository.update(sample_user)

        assert updated_user.full_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_entity(self, user_repository, sample_user):
        """Тестирует удаление сущности."""
        await user_repository.create(sample_user)

        result = await user_repository.delete(sample_user.id)

        assert result is True

        found_user = await user_repository.get_by_id(sample_user.id)
        assert found_user is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_entity(self, user_repository):
        """Тестирует удаление несуществующей сущности."""
        result = await user_repository.delete("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, user_repository, sample_user):
        """Тестирует проверку существования сущности."""
        await user_repository.create(sample_user)

        assert await user_repository.exists(sample_user.id) is True
        assert await user_repository.exists("nonexistent-id") is False

    @pytest.mark.asyncio
    async def test_count(self, user_repository):
        """Тестирует подсчет сущностей."""
        count = await user_repository.count()

        assert count == 0

        # Create users
        for i in range(3):
            user = User(
                id=f"user-{i}",
                email=f"test{i}@example.com",
                hashed_password="hashed",
                full_name=f"Test User {i}",
                is_active=True,
                role="student",
                created_at=datetime.now(UTC),
            )
            await user_repository.create(user)

        count = await user_repository.count()

        assert count == 3


# ========== UserRepository Tests ==========


@pytest.mark.unit
class TestUserRepository:
    """Тесты для репозитория пользователей."""

    @pytest.mark.asyncio
    async def test_get_by_email(self, user_repository, sample_user):
        """Тестирует получение пользователя по email."""
        await user_repository.create(sample_user)

        found_user = await user_repository.get_by_email(sample_user.email)

        assert found_user is not None
        assert found_user.email == sample_user.email
        assert found_user.id == sample_user.id

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repository):
        """Тестирует получение несуществующего пользователя по email."""
        found_user = await user_repository.get_by_email("nonexistent@example.com")

        assert found_user is None

    @pytest.mark.asyncio
    async def test_get_active_users(self, user_repository):
        """Тестирует получение активных пользователей."""
        # Create active user
        active_user = User(
            id="active-user",
            email="active@example.com",
            hashed_password="hashed",
            full_name="Active User",
            is_active=True,
            role="student",
            created_at=datetime.now(UTC),
        )
        await user_repository.create(active_user)

        # Create inactive user
        inactive_user = User(
            id="inactive-user",
            email="inactive@example.com",
            hashed_password="hashed",
            full_name="Inactive User",
            is_active=False,
            role="student",
            created_at=datetime.now(UTC),
        )
        await user_repository.create(inactive_user)

        active_users = await user_repository.get_active_users()

        assert len(active_users) == 1
        assert active_users[0].id == "active-user"

    @pytest.mark.asyncio
    async def test_get_by_role(self, user_repository):
        """Тестирует получение пользователей по роли."""
        # Create students
        for i in range(2):
            user = User(
                id=f"student-{i}",
                email=f"student{i}@example.com",
                hashed_password="hashed",
                full_name=f"Student {i}",
                is_active=True,
                role="student",
                created_at=datetime.now(UTC),
            )
            await user_repository.create(user)

        # Create supervisor
        supervisor = User(
            id="supervisor-1",
            email="supervisor@example.com",
            hashed_password="hashed",
            full_name="Supervisor",
            is_active=True,
            role="supervisor",
            created_at=datetime.now(UTC),
        )
        await user_repository.create(supervisor)

        students = await user_repository.get_by_role("student")

        assert len(students) == 2
        for student in students:
            assert student.role == "student"

    @pytest.mark.asyncio
    async def test_set_active_status(self, user_repository, sample_user):
        """Тестирует установку статуса активности."""
        await user_repository.create(sample_user)

        result = await user_repository.set_active_status(sample_user.id, False)

        assert result is True

        updated_user = await user_repository.get_by_id(sample_user.id)
        assert updated_user is not None
        assert updated_user.is_active is False


# ========== DocumentRepository Tests ==========


@pytest.mark.unit
class TestDocumentRepository:
    """Тесты для репозитория документов."""

    @pytest.mark.asyncio
    async def test_create_document(self, document_repository, sample_document):
        """Тестирует создание документа."""
        created_doc = await document_repository.create(sample_document)

        assert created_doc.id == sample_document.id
        assert created_doc.user_id == sample_document.user_id

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, document_repository, sample_document):
        """Тестирует получение документов пользователя."""
        await document_repository.create(sample_document)

        docs = await document_repository.get_by_user_id(sample_document.user_id)

        assert len(docs) == 1
        assert docs[0].id == sample_document.id

    @pytest.mark.asyncio
    async def test_get_by_user_id_not_found(self, document_repository):
        """Тестирует получение документов несуществующего пользователя."""
        docs = await document_repository.get_by_user_id("nonexistent-user")

        assert len(docs) == 0

    @pytest.mark.asyncio
    async def test_get_by_file_type(self, document_repository, sample_document):
        """Тестирует получение документов по типу файла."""
        await document_repository.create(sample_document)

        docs = await document_repository.get_by_file_type("txt")

        assert len(docs) == 1
        assert docs[0].file_type == "txt"


# ========== AnalysisRepository Tests ==========


@pytest.mark.unit
class TestAnalysisRepository:
    """Тесты для репозитория анализов."""

    @pytest.mark.asyncio
    async def test_create_analysis(self, analysis_repository, sample_analysis):
        """Тестирует создание анализа."""
        created_analysis = await analysis_repository.create(sample_analysis)

        assert created_analysis.id == sample_analysis.id
        assert created_analysis.document_id == sample_analysis.document_id

    @pytest.mark.asyncio
    async def test_get_by_document_id(self, analysis_repository, sample_analysis):
        """Тестирует получение анализов документа."""
        await analysis_repository.create(sample_analysis)

        analyses = await analysis_repository.get_by_document_id(sample_analysis.document_id)

        assert len(analyses) == 1
        assert analyses[0].id == sample_analysis.id

    @pytest.mark.asyncio
    async def test_get_latest_by_document_id(self, analysis_repository):
        """Тестирует получение последнего анализа документа."""
        # Create multiple analyses
        for i in range(3):
            analysis = Analysis(
                id=f"analysis-{i}",
                document_id="doc-123",
                status=AnalysisStatus.COMPLETED,
                overall_score=7.0 + i,
            )
            await analysis_repository.create(analysis)

        latest = await analysis_repository.get_latest_by_document_id("doc-123")

        assert latest is not None
        assert latest.overall_score == 9.0  # Highest score

    @pytest.mark.asyncio
    async def test_update_status(self, analysis_repository, sample_analysis):
        """Тестирует обновление статуса анализа."""
        await analysis_repository.create(sample_analysis)

        await analysis_repository.update_status(sample_analysis.id, AnalysisStatus.FAILED)

        updated = await analysis_repository.get_by_id(sample_analysis.id)
        assert updated is not None
        assert updated.status == AnalysisStatus.FAILED

    @pytest.mark.asyncio
    async def test_update_result(self, analysis_repository, sample_analysis):
        """Тестирует обновление результата анализа."""
        await analysis_repository.create(sample_analysis)

        results = {"structure": {"score": 8.0}}
        await analysis_repository.update_result(sample_analysis.id, 8.0, results)

        updated = await analysis_repository.get_by_id(sample_analysis.id)
        assert updated is not None
        assert updated.overall_score == 8.0
        assert updated.results == results


# ========== ReportRepository Tests ==========


@pytest.mark.unit
class TestReportRepository:
    """Тесты для репозитория отчетов."""

    @pytest.mark.asyncio
    async def test_create_report(self, report_repository, sample_report):
        """Тестирует создание отчета."""
        created_report = await report_repository.create(sample_report)

        assert created_report.id == sample_report.id
        assert created_report.analysis_id == sample_report.analysis_id

    @pytest.mark.asyncio
    async def test_get_by_analysis_id(self, report_repository, sample_report):
        """Тестирует получение отчета по ID анализа."""
        await report_repository.create(sample_report)

        report = await report_repository.get_by_analysis_id(sample_report.analysis_id)

        assert report is not None
        assert report.id == sample_report.id


# ========== HistoryRepository Tests ==========


@pytest.mark.unit
class TestHistoryRepository:
    """Тесты для репозитория истории."""

    @pytest.mark.asyncio
    async def test_create_history(self, history_repository):
        """Тестирует создание записи истории."""
        history = History(
            id="history-123",
            document_id="doc-123",
            version_number=1,
            analysis_id="analysis-123",
        )
        created = await history_repository.create(history)

        assert created.id == history.id
        assert created.version_number == 1

    @pytest.mark.asyncio
    async def test_get_by_document_id(self, history_repository):
        """Тестирует получение истории документа."""
        # Create multiple versions
        for i in range(3):
            history = History(
                id=f"history-{i}",
                document_id="doc-123",
                version_number=i + 1,
                analysis_id=f"analysis-{i}",
            )
            await history_repository.create(history)

        histories = await history_repository.get_by_document_id("doc-123")

        assert len(histories) == 3

    @pytest.mark.asyncio
    async def test_get_by_version(self, history_repository):
        """Тестирует получение версии по номеру."""
        history = History(
            id="history-123",
            document_id="doc-123",
            version_number=2,
            analysis_id="analysis-123",
        )
        await history_repository.create(history)

        found = await history_repository.get_by_version("doc-123", 2)

        assert found is not None
        assert found.id == "history-123"

    @pytest.mark.asyncio
    async def test_get_latest_version(self, history_repository):
        """Тестирует получение последней версии."""
        # Create multiple versions
        for i in range(3):
            history = History(
                id=f"history-{i}",
                document_id="doc-123",
                version_number=i + 1,
                analysis_id=f"analysis-{i}",
            )
            await history_repository.create(history)

        latest = await history_repository.get_latest_version("doc-123")

        assert latest is not None
        assert latest.version_number == 3

    @pytest.mark.asyncio
    async def test_get_versions_range(self, history_repository):
        """Тестирует получение диапазона версий."""
        # Create versions
        for i in range(5):
            history = History(
                id=f"history-{i}",
                document_id="doc-123",
                version_number=i + 1,
                analysis_id=f"analysis-{i}",
            )
            await history_repository.create(history)

        # Get range 2-4
        versions = await history_repository.get_versions_range("doc-123", 2, 4)

        assert len(versions) == 3
        version_numbers = [v.version_number for v in versions]
        assert 2 in version_numbers
        assert 3 in version_numbers
        assert 4 in version_numbers
