"""
Интерфейсы репозиториев.

Определяет контракты для работы с хранилищем данных.
Следует принципу Dependency Inversion: бизнес-логика зависит от абстракций.
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import Select

from app.core.domain.analysis import Analysis
from app.core.domain.document import Document
from app.core.domain.history import History
from app.core.domain.report import Report
from app.core.domain.user import User

T = TypeVar("T", User, Document, Analysis, Report, History)


class BaseRepository(ABC, Generic[T]):  # type: ignore[misc]
    """Базовый интерфейс репозитория."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Создает новую сущность."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> T | None:
        """Возвращает сущность по ID."""
        raise NotImplementedError

    @abstractmethod
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[T]:
        """Возвращает список сущностей с пагинацией."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Обновляет существующую сущность."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Удаляет сущность по ID. Возвращает True если удалено."""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, entity_id: str) -> bool:
        """Проверяет существование сущности по ID."""
        raise NotImplementedError

    @abstractmethod
    async def count(self) -> int:
        """Возвращает количество сущностей."""
        raise NotImplementedError


class UserRepository(BaseRepository[User]):
    """Интерфейс репозитория пользователей."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email."""
        raise NotImplementedError

    @abstractmethod
    async def get_active_users(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Возвращает список активных пользователей."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_role(
        self,
        role: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """Возвращает пользователей с указанной ролью."""
        raise NotImplementedError

    @abstractmethod
    async def set_active_status(self, user_id: str, is_active: bool) -> bool:
        """Устанавливает статус активности пользователя."""
        raise NotImplementedError


class DocumentRepository(BaseRepository[Document]):
    """Интерфейс репозитория документов."""

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """Возвращает документы пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_file_type(
        self,
        file_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """Возвращает документы указанного типа."""
        raise NotImplementedError

    @abstractmethod
    async def update_content(self, document_id: str, content: str) -> bool:
        """Обновляет содержимое документа."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_filename(self, user_id: str, filename: str) -> Document | None:
        """Возвращает документ по имени файла пользователя."""
        raise NotImplementedError


class AnalysisRepository(BaseRepository[Analysis]):
    """Интерфейс репозитория анализов."""

    @abstractmethod
    async def get_by_document_id(
        self,
        document_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Analysis]:
        """Возвращает анализы документа."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Analysis]:
        """Возвращает анализы с указанным статусом."""
        raise NotImplementedError

    @abstractmethod
    async def update_status(self, analysis_id: str, status: str) -> bool:
        """Обновляет статус анализа."""
        raise NotImplementedError

    @abstractmethod
    async def update_result(
        self,
        analysis_id: str,
        overall_score: float,
        results: dict[str, Any],
    ) -> bool:
        """Обновляет результат анализа."""
        raise NotImplementedError

    @abstractmethod
    async def get_latest_by_document_id(self, document_id: str) -> Analysis | None:
        """Возвращает последний анализ документа."""
        raise NotImplementedError


class ReportRepository(BaseRepository[Report]):
    """Интерфейс репозитория отчетов."""

    @abstractmethod
    async def get_by_analysis_id(self, analysis_id: str) -> Report | None:
        """Возвращает отчет по ID анализа."""
        raise NotImplementedError

    @abstractmethod
    async def get_all_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Report]:
        """Возвращает отчеты пользователя."""
        raise NotImplementedError


class HistoryRepository(BaseRepository[History]):
    """Интерфейс репозитория истории версий."""

    @abstractmethod
    async def get_by_document_id(
        self,
        document_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[History]:
        """Возвращает историю версий документа."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_version(
        self,
        document_id: str,
        version_number: int,
    ) -> History | None:
        """Возвращает версию документа по номеру."""
        raise NotImplementedError

    @abstractmethod
    async def get_latest_version(self, document_id: str) -> History | None:
        """Возвращает последнюю версию документа."""
        raise NotImplementedError

    @abstractmethod
    async def get_versions_range(
        self,
        document_id: str,
        start_version: int,
        end_version: int,
    ) -> list[History]:
        """Возвращает диапазон версий документа."""
        raise NotImplementedError


class QueryBuilder(ABC):
    """Интерфейс для построения SQL запросов."""

    @abstractmethod
    def build_select(self, model: type[T]) -> Select[tuple[T]]:
        """Создает базовый SELECT запрос."""
        raise NotImplementedError

    @abstractmethod
    def build_select_with_filter(
        self,
        model: type[T],
        filters: dict[str, Any],
    ) -> Select[tuple[T]]:
        """Создает SELECT запрос с фильтрами."""
        raise NotImplementedError

    @abstractmethod
    def build_select_with_pagination(
        self,
        model: type[T],
        limit: int,
        offset: int,
    ) -> Select[tuple[T]]:
        """Создает SELECT запрос с пагинацией."""
        raise NotImplementedError

    @abstractmethod
    def build_select_with_order(
        self,
        model: type[T],
        order_by: str,
        desc: bool = False,
    ) -> Select[tuple[T]]:
        """Создает SELECT запрос с сортировкой."""
        raise NotImplementedError


class SessionManager(ABC):
    """Интерфейс для управления сессиями базы данных."""

    @abstractmethod
    async def get_session(self) -> Any:
        """Возвращает сессию базы данных."""
        raise NotImplementedError

    @abstractmethod
    async def close_session(self) -> None:
        """Закрывает сессию базы данных."""
        raise NotImplementedError
