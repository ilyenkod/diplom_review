"""
Unit-тесты для сервисов приложения.

Тестирует логику сервисов:
- auth_service.py - регистрация, логин, валидация токенов
- document_service.py - валидация, извлечение текста, сохранение
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import get_settings
from app.core.const import FileFormats
from app.core.domain import Document, User
from app.core.exceptions import (
    DocumentValidationError,
    DocumentProcessingError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidFileTypeError,
    UserAlreadyExistsError,
    ValidationError,
)
from app.core.services.auth_service import AuthService, TokenPair
from app.core.services.document_service import DocumentService

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
