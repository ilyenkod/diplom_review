"""
Кастомные исключения приложения.

Определяет иерархию исключений для разных слоев приложения.
Следует принципам Domain-Driven Design: исключения в domain layer.
"""


class BaseApplicationError(Exception):
    """Базовый класс исключений приложения."""

    message: str

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


# ========== Domain Exceptions ==========


class DomainError(BaseApplicationError):
    """Базовый класс исключений domain layer."""

    pass


class ValidationError(DomainError):
    """Ошибка валидации данных."""

    field: str | None = None

    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


class NotFoundError(DomainError):
    """Ресурс не найден."""

    resource: str | None = None

    def __init__(self, message: str, resource: str | None = None) -> None:
        self.resource = resource
        super().__init__(message)


class ConflictError(DomainError):
    """Конфликт данных (например, дубликат)."""

    pass


class BusinessLogicError(DomainError):
    """Ошибка бизнес-логики."""

    pass


class UnauthorizedError(DomainError):
    """Ошибка авторизации (пользователь не аутентифицирован)."""

    pass


class ForbiddenError(DomainError):
    """Ошибка доступа (пользователь не имеет прав)."""

    pass


# ========== User Exceptions ==========


class UserError(DomainError):
    """Базовый класс исключений пользователя."""

    pass


class UserNotFoundError(UserError):
    """Пользователь не найден."""

    def __init__(self, user_id: str) -> None:
        super().__init__(f"User with id {user_id} not found")


class UserAlreadyExistsError(UserError):
    """Пользователь уже существует."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User with email {email} already exists")


class InvalidPasswordError(UserError):
    """Неверный пароль."""

    def __init__(self) -> None:
        super().__init__("Invalid password")


class InactiveUserError(UserError):
    """Пользователь неактивен."""

    def __init__(self) -> None:
        super().__init__("User account is inactive")


class InvalidCredentialsError(UserError):
    """Неверные учетные данные."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


# ========== Document Exceptions ==========


class DocumentError(DomainError):
    """Базовый класс исключений документа."""

    pass


class DocumentNotFoundError(DocumentError):
    """Документ не найден."""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document with id {document_id} not found")


class DocumentValidationError(DocumentError):
    """Ошибка валидации документа."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field


class InvalidFileTypeError(DocumentValidationError):
    """Неверный тип файла."""

    def __init__(self, file_type: str, allowed_types: list[str]) -> None:
        super().__init__(
            f"Invalid file type: {file_type}. Allowed types: {', '.join(allowed_types)}",
            field="file_type",
        )


class FileSizeExceededError(DocumentValidationError):
    """Размер файла превышен."""

    def __init__(self, size: int, max_size: int) -> None:
        super().__init__(
            f"File size {size} bytes exceeds maximum allowed size {max_size} bytes",
            field="file_size",
        )


class DocumentProcessingError(DocumentError):
    """Ошибка обработки документа."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Document processing error: {message}")


# ========== Analysis Exceptions ==========


class AnalysisError(DomainError):
    """Базовый класс исключений анализа."""

    pass


class AnalysisNotFoundError(AnalysisError):
    """Анализ не найден."""

    def __init__(self, analysis_id: str) -> None:
        super().__init__(f"Analysis with id {analysis_id} not found")


class AnalysisAlreadyRunningError(AnalysisError):
    """Анализ уже выполняется."""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Analysis for document {document_id} is already running")


class AnalysisFailedError(AnalysisError):
    """Анализ завершился с ошибкой."""

    def __init__(self, error_message: str) -> None:
        super().__init__(f"Analysis failed: {error_message}")


class AnalyzerError(AnalysisError):
    """Ошибка анализатора."""

    analyzer_name: str | None = None

    def __init__(self, message: str, analyzer_name: str | None = None) -> None:
        self.analyzer_name = analyzer_name
        super().__init__(message)


# ========== LLM Exceptions ==========


class LLMError(DomainError):
    """Базовый класс исключений LLM."""

    pass


class LLMConnectionError(LLMError):
    """Ошибка соединения с LLM."""

    def __init__(self, provider: str) -> None:
        super().__init__(f"Failed to connect to LLM provider: {provider}")


class LLMTimeoutError(LLMError):
    """Таймаут запроса к LLM."""

    def __init__(self) -> None:
        super().__init__("LLM request timed out")


class LLMResponseError(LLMError):
    """Ошибка ответа LLM."""

    def __init__(self, message: str) -> None:
        super().__init__(f"LLM response error: {message}")


class LLMQuotaExceededError(LLMError):
    """Превышен лимит запросов к LLM."""

    def __init__(self) -> None:
        super().__init__("LLM quota exceeded")


class InvalidLLMResponseError(LLMError):
    """Неверный формат ответа LLM."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Invalid LLM response: {message}")


# ========== Storage Exceptions ==========


class StorageError(DomainError):
    """Базовый класс исключений хранилища."""

    pass


class FileNotFoundError(StorageError):
    """Файл не найден в хранилище."""

    def __init__(self, key: str) -> None:
        super().__init__(f"File not found in storage: {key}")


class StorageConnectionError(StorageError):
    """Ошибка соединения с хранилищем."""

    def __init__(self, storage_type: str) -> None:
        super().__init__(f"Failed to connect to storage: {storage_type}")


class StorageQuotaExceededError(StorageError):
    """Превышен лимит хранилища."""

    def __init__(self) -> None:
        super().__init__("Storage quota exceeded")


class InvalidStorageKeyError(StorageError):
    """Неверный ключ хранилища."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Invalid storage key: {key}")


# ========== Cache Exceptions ==========


class CacheError(DomainError):
    """Базовый класс исключений кэша."""

    pass


class CacheConnectionError(CacheError):
    """Ошибка соединения с кэшем."""

    def __init__(self) -> None:
        super().__init__("Failed to connect to cache")


class CacheKeyNotFoundError(CacheError):
    """Ключ не найден в кэше."""

    def __init__(self, key: str) -> None:
        super().__init__(f"Cache key not found: {key}")


class CacheSerializationError(CacheError):
    """Ошибка сериализации данных для кэша."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Cache serialization error: {message}")


# ========== Report Exceptions ==========


class ReportError(DomainError):
    """Базовый класс исключений отчетов."""

    pass


class ReportNotFoundError(ReportError):
    """Отчет не найден."""

    def __init__(self, report_id: str) -> None:
        super().__init__(f"Report with id {report_id} not found")


class ReportGenerationError(ReportError):
    """Ошибка генерации отчета."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Report generation error: {message}")


# ========== History Exceptions ==========


class HistoryError(DomainError):
    """Базовый класс исключений истории."""

    pass


class HistoryNotFoundError(HistoryError):
    """Запись истории не найдена."""

    def __init__(self, history_id: str) -> None:
        super().__init__(f"History record with id {history_id} not found")


class VersionNotFoundError(HistoryError):
    """Версия документа не найдена."""

    def __init__(self, document_id: str, version: int) -> None:
        super().__init__(f"Version {version} for document {document_id} not found")
