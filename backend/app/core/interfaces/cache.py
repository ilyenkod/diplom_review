"""
Интерфейсы для работы с кэшем.

Определяет контракты для кэширования данных.
Следует принципу Dependency Inversion: бизнес-логика зависит от абстракций.
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any


class CacheClient(ABC):
    """Базовый интерфейс клиента кэша."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Возвращает значение по ключу."""
        raise NotImplementedError

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | timedelta | None = None,
    ) -> bool:
        """Устанавливает значение по ключу с опциональным TTL."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Удаляет значение по ключу."""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Проверяет существование ключа."""
        raise NotImplementedError

    @abstractmethod
    async def expire(self, key: str, ttl: int | timedelta) -> bool:
        """Устанавливает TTL для существующего ключа."""
        raise NotImplementedError

    @abstractmethod
    async def ttl(self, key: str) -> int:
        """Возвращает время жизни ключа в секундах. -1 если нет TTL, -2 если ключ не существует."""
        raise NotImplementedError

    @abstractmethod
    async def keys(self, pattern: str = "*") -> list[str]:
        """Возвращает список ключей по шаблону."""
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> bool:
        """Очищает весь кэш."""
        raise NotImplementedError

    @abstractmethod
    async def ping(self) -> bool:
        """Проверяет доступность кэша."""
        raise NotImplementedError


class CacheRepository(ABC):
    """Интерфейс репозитория кэша для бизнес-логики."""

    @abstractmethod
    async def get_user(self, user_id: str) -> Any | None:
        """Возвращает кэшированного пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def set_user(self, user_id: str, user: Any, ttl: int = 3600) -> bool:
        """Кэширует пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Удаляет кэшированного пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def get_document(self, document_id: str) -> Any | None:
        """Возвращает кэшированный документ."""
        raise NotImplementedError

    @abstractmethod
    async def set_document(
        self,
        document_id: str,
        document: Any,
        ttl: int = 3600,
    ) -> bool:
        """Кэширует документ."""
        raise NotImplementedError

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Удаляет кэшированный документ."""
        raise NotImplementedError

    @abstractmethod
    async def get_analysis(self, analysis_id: str) -> Any | None:
        """Возвращает кэшированный анализ."""
        raise NotImplementedError

    @abstractmethod
    async def set_analysis(
        self,
        analysis_id: str,
        analysis: Any,
        ttl: int = 7200,
    ) -> bool:
        """Кэширует анализ."""
        raise NotImplementedError

    @abstractmethod
    async def delete_analysis(self, analysis_id: str) -> bool:
        """Удаляет кэшированный анализ."""
        raise NotImplementedError

    @abstractmethod
    async def get_report(self, analysis_id: str) -> Any | None:
        """Возвращает кэшированный отчет."""
        raise NotImplementedError

    @abstractmethod
    async def set_report(
        self,
        analysis_id: str,
        report: Any,
        ttl: int = 3600,
    ) -> bool:
        """Кэширует отчет."""
        raise NotImplementedError

    @abstractmethod
    async def delete_report(self, analysis_id: str) -> bool:
        """Удаляет кэшированный отчет."""
        raise NotImplementedError

    @abstractmethod
    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Инвалидирует весь кэш пользователя."""
        raise NotImplementedError

    @abstractmethod
    async def invalidate_document_cache(self, document_id: str) -> bool:
        """Инвалидирует кэш документа."""
        raise NotImplementedError
