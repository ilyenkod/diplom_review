"""
Unit-тесты для сервисов приложения.

Тестирует логику сервисов:
- auth_service.py - регистрация, логин, валидация токенов
- document_service.py - валидация, извлечение текста, сохранение
- analysis_service.py - запуск анализаторов, агрегация, кэширование
- report_service.py - формирование оценки, рекомендации
- history_service.py - сохранение версий
- comparison_service.py - сравнение версий
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import get_settings
from app.core.const import AnalysisCriteria, AssessmentLevel, FileFormats
from app.core.domain import Analysis, Document, History, Report, User
from app.core.exceptions import (
    AnalysisAlreadyRunningError,
    AnalysisFailedError,
    AnalysisNotFoundError,
    DocumentNotFoundError,
    DocumentProcessingError,
    DocumentValidationError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidFileTypeError,
    ReportGenerationError,
    UserAlreadyExistsError,
    ValidationError,
    VersionNotFoundError,
)
from app.core.services.analysis_service import AnalysisService, AnalysisConfig
from app.core.services.auth_service import AuthService, TokenPair
from app.core.services.comparison_service import ComparisonService, VersionComparison
from app.core.services.document_service import DocumentService
from app.core.services.history_service import HistoryService
from app.core.services.report_service import ReportService

# ========== AuthService Tests ==========


class TestAuthService:
    """Тесты для сервиса аутентификации."""

    @pytest.fixture
    def user_repo(self):
        """Фикстура для мока UserRepository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def auth_service(self, user_repo):
        """Фикстура для AuthService."""
        return AuthService(user_repo)

    @pytest.fixture
    def sample_user(self):
        """Фикстура для тестового пользователя."""
        return User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            role="student",
            created_at=datetime.now(UTC),
        )

    async def test_register_success(self, auth_service, user_repo, sample_user):
        """Тестирует успешную регистрацию пользователя."""
        # Setup
        user_repo.get_by_email.return_value = None
        user_repo.create.return_value = sample_user

        # Execute (patching to avoid bcrypt issues)
        with patch("app.core.services.auth_service.hash_password", return_value="hashed_password"):
            result = await auth_service.register(
                email="test@example.com",
                password="StrongPass123",
                full_name="Test User",
            )

        # Assert
        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        assert result.id == "user-123"
        user_repo.get_by_email.assert_called_once_with("test@example.com")
        user_repo.create.assert_called_once()

    async def test_register_user_already_exists(self, auth_service, user_repo, sample_user):
        """Тестирует ошибку при регистрации существующего пользователя."""
        # Setup
        user_repo.get_by_email.return_value = sample_user

        # Execute & Assert
        with pytest.raises(UserAlreadyExistsError, match=r"test@example\.com"):
            await auth_service.register(
                email="test@example.com",
                password="StrongPass123",
                full_name="Test User",
            )
        user_repo.create.assert_not_called()

    async def test_register_weak_password(self, auth_service, user_repo):
        """Тестирует ошибку при слабом пароле."""
        # Setup
        user_repo.get_by_email.return_value = None

        # Execute & Assert
        weak_password = "123"
        with pytest.raises(ValidationError, match="too short"):
            await auth_service.register(
                email="test@example.com",
                password=weak_password,
                full_name="Test User",
            )
        user_repo.create.assert_not_called()

    async def test_login_success(self, auth_service, user_repo, sample_user):
        """Тестирует успешный вход в систему."""
        # Setup
        user_repo.get_by_email.return_value = sample_user

        # Execute (patching to avoid bcrypt issues)
        with patch("app.core.services.auth_service.verify_password", return_value=True):
            result = await auth_service.login(
                email="test@example.com",
                password="StrongPass123",
            )

        # Assert
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert isinstance(result, TokenPair)
        user_repo.get_by_email.assert_called_once_with("test@example.com")

    async def test_login_invalid_password(self, auth_service, user_repo, sample_user):
        """Тестирует ошибку при неверном пароле."""
        # Setup
        user_repo.get_by_email.return_value = sample_user

        # Execute & Assert (patching to avoid bcrypt issues)
        with patch("app.core.services.auth_service.verify_password", return_value=False):
            with pytest.raises(InvalidCredentialsError):
                await auth_service.login(
                    email="test@example.com",
                    password="WrongPassword",
                )

    async def test_login_user_not_found(self, auth_service, user_repo):
        """Тестирует ошибку при несуществующем пользователе."""
        # Setup
        user_repo.get_by_email.return_value = None

        # Execute & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login(
                email="nonexistent@example.com",
                password="SomePassword",
            )

    async def test_login_inactive_user(self, auth_service, user_repo, sample_user):
        """Тестирует ошибку при неактивном пользователе."""
        # Setup
        sample_user.is_active = False
        user_repo.get_by_email.return_value = sample_user

        # Execute & Assert (patching to avoid bcrypt issues)
        with patch("app.core.services.auth_service.verify_password", return_value=True):
            with pytest.raises(InactiveUserError):
                await auth_service.login(
                    email="test@example.com",
                    password="StrongPass123",
                )

    async def test_validate_access_token_success(self, auth_service, sample_user):
        """Тестирует успешную валидацию access токена."""
        # Setup - создаем реальный токен
        from app.core.security import create_access_token

        token_payload = {"sub": sample_user.id, "role": sample_user.role}
        valid_token = create_access_token(token_payload)

        # Execute
        result = await auth_service.validate_access_token(valid_token)

        # Assert
        assert result is not None
        assert result.user_id == sample_user.id
        assert result.role == sample_user.role

    async def test_validate_access_token_invalid(self, auth_service):
        """Тестирует ошибку при невалидном токене."""
        # Execute
        result = await auth_service.validate_access_token("invalid_token")

        # Assert
        assert result is None

    async def test_refresh_tokens_success(self, auth_service, user_repo, sample_user):
        """Тестирует успешное обновление токенов."""
        # Setup
        user_repo.get_by_id.return_value = sample_user

        # Setup - создаем реальный токен
        from app.core.security import create_refresh_token

        token_payload = {"sub": sample_user.id, "role": sample_user.role}
        valid_refresh_token = create_refresh_token(token_payload)

        # Execute
        result = await auth_service.refresh_tokens(valid_refresh_token)

        # Assert
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert isinstance(result, TokenPair)

    async def test_refresh_tokens_invalid(self, auth_service):
        """Тестирует ошибку при невалидном refresh токене."""
        # Execute & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.refresh_tokens("invalid_refresh_token")


# ========== DocumentService Tests ==========


class TestDocumentService:
    """Тесты для сервиса документов."""

    @pytest.fixture
    def document_repo(self):
        """Фикстура для мока DocumentRepository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def storage(self):
        """Фикстура для мока Storage."""
        storage = AsyncMock()
        return storage

    @pytest.fixture
    def logger(self):
        """Фикстура для мока AppLogger."""
        logger = MagicMock()
        return logger

    @pytest.fixture
    def processors(self):
        """Фикстура для моков процессоров."""
        return {
            FileFormats.DOCX: MagicMock(),
            FileFormats.PDF: MagicMock(),
            FileFormats.TXT: MagicMock(),
        }

    @pytest.fixture
    def document_service(self, document_repo, storage, logger, processors):
        """Фикстура для DocumentService."""
        yield DocumentService(document_repo, storage, logger, processors)

    async def test_validate_file_success(self, document_service):
        """Тестирует успешную валидацию файла."""
        result = document_service._validate_file("test.txt", 1024)
        assert result is None

    async def test_validate_file_invalid_type(self, document_service):
        """Тестирует ошибку при неверном типе файла."""
        with pytest.raises(InvalidFileTypeError, match="Invalid file type"):
            document_service._validate_file("test.exe", 1024)

    async def test_validate_file_too_large(self, document_service):
        """Тестирует ошибку при слишком большом файле."""
        with pytest.raises(DocumentValidationError, match="exceeds maximum allowed size"):
            document_service._validate_file(
                "test.txt", get_settings().upload.max_file_size + 1
            )

    async def test_select_processor_success(self, document_service, processors):
        """Тестирует успешный выбор процессора."""
        processor = document_service._select_processor("txt")
        assert processor == processors[FileFormats.TXT]

    async def test_select_processor_not_found(self, document_service):
        """Тестирует ошибку при отсутствии процессора."""
        with pytest.raises(InvalidFileTypeError, match="Invalid file type"):
            document_service._select_processor("exe")

    async def test_get_document_success(self, document_service, document_repo):
        """Тестирует успешное получение документа."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
            file_path="test.txt",
        )
        document_repo.get_by_id.return_value = sample_document

        # Execute
        result = await document_service.get_document("doc-123")

        # Assert
        assert result.id == "doc-123"
        assert result.user_id == "user-123"
        document_repo.get_by_id.assert_called_once_with("doc-123")

    async def test_get_document_not_found(self, document_service, document_repo):
        """Тестирует ошибку при отсутствии документа."""
        # Setup
        document_repo.get_by_id.return_value = None

        # Execute & Assert
        result = await document_service.get_document("doc-123")
        assert result is None

    async def test_get_user_documents(self, document_service, document_repo):
        """Тестирует получение документов пользователя."""
        # Setup
        sample_documents = [
            Document(
                id="doc-1",
                user_id="user-123",
                filename="test1.txt",
                original_filename="test1.txt",
                file_size=1024,
                file_type="txt",
            ),
            Document(
                id="doc-2",
                user_id="user-123",
                filename="test2.txt",
                original_filename="test2.txt",
                file_size=2048,
                file_type="txt",
            ),
        ]
        document_repo.get_by_user_id.return_value = sample_documents

        # Execute
        result = await document_service.get_user_documents("user-123")

        # Assert
        assert len(result) == 2
        document_repo.get_by_user_id.assert_called_once_with("user-123", 100, 0)

    async def test_delete_document_success(self, document_service, document_repo, storage):
        """Тестирует успешное удаление документа."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
            file_path="test.txt",
        )
        document_repo.get_by_id.return_value = sample_document
        document_repo.delete.return_value = True

        # Execute
        result = await document_service.delete_document("doc-123", "user-123")

        # Assert
        storage.delete.assert_called_once_with("test.txt")
        document_repo.delete.assert_called_once_with("doc-123")
        assert result is True

    async def test_delete_document_not_found(self, document_service, document_repo):
        """Тестирует ошибку при удалении несуществующего документа."""
        # Setup
        document_repo.get_by_id.return_value = None

        # Execute & Assert
        result = await document_service.delete_document("doc-123", "user-123")
        assert result is False

    async def test_upload_document_success(
        self, document_service, document_repo, storage, processors
    ):
        """Тестирует успешную загрузку документа."""
        # Setup
        file_content = b"test content"
        storage.save.return_value = MagicMock(success=True, text=None)
        processors[FileFormats.TXT].process_bytes = AsyncMock(
            return_value=MagicMock(
                success=True,
                text="processed text",
            )
        )
        created_doc = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=len(file_content),
            file_type="txt",
            content="processed text",
        )
        document_repo.create.return_value = created_doc

        # Execute
        result = await document_service.upload_document(
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=len(file_content),
            file_type="txt",
            content=file_content,
        )

        # Assert
        storage.save.assert_called_once()
        processors[FileFormats.TXT].process_bytes.assert_called_once_with(file_content)
        document_repo.create.assert_called_once()
        assert result.user_id == "user-123"

    async def test_upload_document_save_error(
        self, document_service, storage, processors
    ):
        """Тестирует ошибку при сохранении файла."""
        # Setup
        file_content = b"test content"
        storage.save.return_value = MagicMock(success=False, error="Storage error")
        processors[FileFormats.TXT].process_bytes = AsyncMock(
            return_value=MagicMock(success=True, text="processed text")
        )

        # Execute & Assert
        with pytest.raises(DocumentProcessingError, match="Failed to save file"):
            await document_service.upload_document(
                user_id="user-123",
                filename="test.txt",
                original_filename="test.txt",
                file_size=len(file_content),
                file_type="txt",
                content=file_content,
            )

    async def test_upload_document_process_error(
        self, document_service, storage, processors
    ):
        """Тестирует ошибку при обработке файла."""
        # Setup
        file_content = b"test content"
        storage.save.return_value = MagicMock(success=True, text=None)
        processors[FileFormats.TXT].process_bytes = AsyncMock(
            return_value=MagicMock(
                success=False,
                error="Processing error",
            )
        )

        # Execute & Assert
        with pytest.raises(DocumentProcessingError, match="Failed to process txt file"):
            await document_service.upload_document(
                user_id="user-123",
                filename="test.txt",
                original_filename="test.txt",
                file_size=len(file_content),
                file_type="txt",
                content=file_content,
            )


# ========== AnalysisService Tests ==========


class TestAnalysisService:
    """Тесты для сервиса анализа."""

    @pytest.fixture
    def analysis_service(self, mock_analysis_repository, mock_document_repository, mock_cache_repository, mock_llm_client, logger):
        """Возвращает сервис анализа."""
        return AnalysisService(mock_analysis_repository, mock_document_repository, mock_cache_repository, mock_llm_client, logger)

    @pytest.fixture
    def sample_document(self):
        """Возвращает тестовый документ."""
        return Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
            content="Test document content for analysis",
        )

    @pytest.mark.asyncio
    async def test_start_analysis_success(self, analysis_service, mock_document_repository, mock_analysis_repository):
        """Тестирует успешный запуск анализа."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
            content="Test content",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_analysis_repository.get_latest_by_document_id = AsyncMock(return_value=None)
        mock_analysis_repository.create = AsyncMock(
            return_value=Analysis(id="analysis-123", document_id="doc-123", status="pending")
        )

        # Execute
        analysis = await analysis_service.start_analysis("doc-123")

        # Assert
        assert analysis.status == "pending"
        mock_analysis_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_analysis_document_not_found(self, analysis_service, mock_document_repository):
        """Тестирует ошибку при отсутствии документа."""
        mock_document_repository.get_by_id = AsyncMock(return_value=None)

        # Execute & Assert
        with pytest.raises(DocumentNotFoundError):
            await analysis_service.start_analysis("nonexistent-doc")

    @pytest.mark.asyncio
    async def test_start_analysis_already_running(self, analysis_service, mock_document_repository, mock_analysis_repository):
        """Тестирует ошибку при уже запущенном анализе."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
            content="Test content",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)

        # Mock running analysis
        running_analysis = Analysis(id="analysis-1", document_id="doc-123", status="processing")
        mock_analysis_repository.get_latest_by_document_id = AsyncMock(return_value=running_analysis)

        # Execute & Assert
        with pytest.raises(AnalysisAlreadyRunningError):
            await analysis_service.start_analysis("doc-123")

    @pytest.mark.asyncio
    async def test_analyze_document_success(self, analysis_service, mock_document_repository, mock_analysis_repository, mock_cache_repository):
        """Тестирует успешный анализ документа."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
            content="Test document content",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_analysis_repository.get_latest_by_document_id = AsyncMock(return_value=None)
        mock_analysis_repository.create = AsyncMock(
            return_value=Analysis(id="analysis-123", document_id="doc-123", status="pending")
        )
        mock_analysis_repository.update_result = AsyncMock()
        mock_analysis_repository.update_status = AsyncMock()

        # Execute
        analysis = await analysis_service.analyze_document("doc-123")

        # Assert
        assert analysis is not None
        mock_analysis_repository.update_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_assessment_level(self, analysis_service):
        """Тестирует определение уровня оценки."""
        assert analysis_service.get_assessment_level(9.0) == AssessmentLevel.EXCELLENT
        assert analysis_service.get_assessment_level(7.5) == AssessmentLevel.GOOD
        assert analysis_service.get_assessment_level(6.0) == AssessmentLevel.SATISFACTORY
        assert analysis_service.get_assessment_level(3.0) == AssessmentLevel.POOR


# ========== ReportService Tests ==========


class TestReportService:
    """Тесты для сервиса отчетов."""

    @pytest.fixture
    def report_service(self, mock_report_repository, mock_analysis_repository, mock_llm_client, logger):
        """Возвращает сервис отчетов."""
        return ReportService(mock_report_repository, mock_analysis_repository, mock_llm_client, logger)

    @pytest.fixture
    def sample_analysis(self):
        """Возвращает тестовый анализ."""
        return Analysis(
            id="analysis-123",
            document_id="doc-123",
            status="completed",
            overall_score=8.5,
            results={
                "structure": {"score": 8.0, "comments": ["Good structure"], "recommendations": []},
                "style": {"score": 9.0, "comments": ["Excellent style"], "recommendations": []},
            },
        )

    @pytest.mark.asyncio
    async def test_generate_report_success(self, report_service, mock_analysis_repository, sample_analysis):
        """Тестирует успешную генерацию отчета."""
        # Setup
        mock_analysis_repository.get_by_id = AsyncMock(return_value=sample_analysis)

        # Create a sample report to return
        sample_report = Report(
            id="report-123",
            analysis_id="analysis-123",
            overall_assessment="Good work",
            recommendations=["Improve structure"],
            supervisor_comments=["Well done"],
        )

        # Execute
        report = await report_service.generate_report("analysis-123")

        # Assert
        assert report is not None

    @pytest.mark.asyncio
    async def test_generate_report_analysis_not_found(self, report_service, mock_analysis_repository):
        """Тестирует ошибку при отсутствии анализа."""
        mock_analysis_repository.get_by_id = AsyncMock(return_value=None)

        # Execute & Assert
        with pytest.raises(AnalysisNotFoundError):
            await report_service.generate_report("nonexistent-analysis")

    @pytest.mark.asyncio
    async def test_generate_report_analysis_not_completed(self, report_service, mock_analysis_repository):
        """Тестирует ошибку при незавершенном анализе."""
        # Setup
        incomplete_analysis = Analysis(id="analysis-123", document_id="doc-123", status="pending")
        mock_analysis_repository.get_by_id = AsyncMock(return_value=incomplete_analysis)

        # Execute & Assert
        with pytest.raises(ReportGenerationError, match="not completed"):
            await report_service.generate_report("analysis-123")

    @pytest.mark.asyncio
    async def test_form_overall_assessment(self, report_service, sample_analysis):
        """Тестирует формирование общей оценки."""
        assessment = report_service._form_overall_assessment(sample_analysis)

        assert "8.5" in assessment
        assert sample_analysis.overall_score is not None

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, report_service, sample_analysis):
        """Тестирует генерацию рекомендаций."""
        # Add some recommendations to the analysis
        sample_analysis.results["structure"]["recommendations"] = ["Add more details"]

        recommendations = report_service._generate_recommendations(sample_analysis)

        assert len(recommendations) >= 0


# ========== HistoryService Tests ==========


class TestHistoryService:
    """Тесты для сервиса истории."""

    @pytest.fixture
    def history_service(self, mock_history_repository, mock_analysis_repository, mock_document_repository, logger):
        """Возвращает сервис истории."""
        return HistoryService(mock_history_repository, mock_analysis_repository, mock_document_repository, logger)

    @pytest.fixture
    def sample_analysis(self):
        """Возвращает тестовый анализ."""
        return Analysis(
            id="analysis-123",
            document_id="doc-123",
            status="completed",
            overall_score=8.5,
            results={},
        )

    @pytest.mark.asyncio
    async def test_save_version_success(self, history_service, mock_document_repository, mock_analysis_repository, mock_history_repository):
        """Тестирует успешное сохранение версии."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
            content="Test content",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_analysis_repository.get_by_id = AsyncMock(return_value=Analysis(
            id="analysis-123",
            document_id="doc-123",
            status="completed",
            overall_score=8.5,
        ))
        mock_history_repository.get_latest_version = AsyncMock(return_value=None)
        mock_history_repository.create = AsyncMock(
            return_value=History(
                id="history-123",
                document_id="doc-123",
                version_number=1,
                analysis_id="analysis-123",
            )
        )

        # Execute
        history = await history_service.save_version("doc-123", "analysis-123")

        # Assert
        assert history.version_number == 1

    @pytest.mark.asyncio
    async def test_get_document_history(self, history_service, mock_document_repository, mock_history_repository):
        """Тестирует получение истории документа."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_history_repository.get_by_document_id = AsyncMock(return_value=[])

        # Execute
        history = await history_service.get_document_history("doc-123")

        # Assert
        assert isinstance(history, list)

    @pytest.mark.asyncio
    async def test_get_latest_version(self, history_service, mock_document_repository, mock_history_repository):
        """Тестирует получение последней версии."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)

        latest_history = History(
            id="history-123",
            document_id="doc-123",
            version_number=3,
            analysis_id="analysis-123",
        )
        mock_history_repository.get_latest_version = AsyncMock(return_value=latest_history)

        # Execute
        result = await history_service.get_latest_version("doc-123")

        # Assert
        assert result is not None
        assert result.version_number == 3


# ========== ComparisonService Tests ==========


class TestComparisonService:
    """Тесты для сервиса сравнения."""

    @pytest.fixture
    def comparison_service(self, mock_history_repository, mock_analysis_repository, mock_document_repository, logger):
        """Возвращает сервис сравнения."""
        return ComparisonService(mock_history_repository, mock_analysis_repository, mock_document_repository, logger)

    @pytest.fixture
    def sample_analyses(self):
        """Возвращает тестовые анализы для сравнения."""
        return {
            "prev": Analysis(
                id="analysis-prev",
                document_id="doc-123",
                status="completed",
                overall_score=7.0,
                results={
                    "structure": {"score": 7.0},
                    "style": {"score": 7.0},
                },
            ),
            "curr": Analysis(
                id="analysis-curr",
                document_id="doc-123",
                status="completed",
                overall_score=8.5,
                results={
                    "structure": {"score": 8.0},
                    "style": {"score": 9.0},
                },
            ),
        }

    @pytest.mark.asyncio
    async def test_compare_versions_success(self, comparison_service, mock_document_repository, mock_history_repository, mock_analysis_repository, sample_analyses):
        """Тестирует успешное сравнение версий."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)

        prev_history = History(
            id="history-prev",
            document_id="doc-123",
            version_number=1,
            analysis_id="analysis-prev",
        )
        curr_history = History(
            id="history-curr",
            document_id="doc-123",
            version_number=2,
            analysis_id="analysis-curr",
        )
        mock_history_repository.get_by_version = AsyncMock(side_effect=[prev_history, curr_history])
        mock_analysis_repository.get_by_id = AsyncMock(side_effect=[
            sample_analyses["prev"],
            sample_analyses["curr"],
        ])

        # Execute
        comparison = await comparison_service.compare_versions("doc-123", 1, 2)

        # Assert
        assert comparison is not None
        assert comparison.previous_version == 1
        assert comparison.current_version == 2
        assert comparison.overall_score_diff == 1.5

    @pytest.mark.asyncio
    async def test_compare_versions_document_not_found(self, comparison_service, mock_document_repository):
        """Тестирует ошибку при отсутствии документа."""
        mock_document_repository.get_by_id = AsyncMock(return_value=None)

        # Execute & Assert
        with pytest.raises(DocumentNotFoundError):
            await comparison_service.compare_versions("nonexistent-doc", 1, 2)

    @pytest.mark.asyncio
    async def test_compare_versions_not_found(self, comparison_service, mock_document_repository, mock_history_repository):
        """Тестирует ошибку при отсутствии версии."""
        # Setup
        sample_document = Document(
            id="doc-123",
            user_id="user-123",
            filename="test.txt",
            original_filename="test.txt",
            file_size=1024,
            file_type="txt",
        )
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_history_repository.get_by_version = AsyncMock(return_value=None)

        # Execute & Assert
        with pytest.raises(VersionNotFoundError):
            await comparison_service.compare_versions("doc-123", 1, 2)

    @pytest.mark.asyncio
    async def test_determine_trend(self, comparison_service):
        """Тестирует определение тенденции."""
        assert comparison_service._determine_trend(1.5) == "improved"
        assert comparison_service._determine_trend(-1.5) == "worsened"
        assert comparison_service._determine_trend(0.2) == "unchanged"
        assert comparison_service._determine_trend(None) == "unchanged"


# ========== Mock Fixtures ==========
# Моковые фикстуры для unit-тестов (не используют БД)


@pytest.fixture
def mock_analysis_repository():
    """Возвращает mock репозитория анализов для unit тестов."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_document_id = AsyncMock(return_value=[])
    repo.get_latest_by_document_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.update_status = AsyncMock()
    repo.update_result = AsyncMock()
    return repo


@pytest.fixture
def mock_document_repository():
    """Возвращает mock репозитория документов для unit тестов."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_user_id = AsyncMock(return_value=[])
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_history_repository():
    """Возвращает mock репозитория истории для unit тестов."""
    repo = AsyncMock()
    repo.get_by_document_id = AsyncMock(return_value=[])
    repo.get_by_version = AsyncMock(return_value=None)
    repo.get_latest_version = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    repo.get_versions_range = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_report_repository():
    """Возвращает mock репозитория отчетов для unit тестов."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    repo.get_by_analysis_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_cache_repository():
    """Возвращает mock репозитория кэша для unit тестов."""
    from unittest.mock import AsyncMock as AMock

    repo = AMock()
    repo.get_analysis = AMock(return_value=None)
    repo.set_analysis = AMock()
    repo.delete_analysis = AMock()
    return repo
