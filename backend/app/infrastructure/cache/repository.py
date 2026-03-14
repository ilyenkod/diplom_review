"""
Репозиторий кэша для бизнес-логики.

Реализует интерфейс CacheRepository для работы с кэшем.
"""

from typing import Any

from app.core.interfaces.cache import CacheClient, CacheRepository
from app.infrastructure.logging import AppLogger


class RedisCacheRepository(CacheRepository):
    """Репозиторий кэша на основе Redis."""

    def __init__(self, client: CacheClient, logger: AppLogger) -> None:
        """Инициализирует репозиторий кэша.

        Args:
            client: Клиент кэша.
            logger: Логгер приложения.
        """
        self._client = client
        self._logger = logger

    async def get_user(self, user_id: str) -> Any | None:
        """Возвращает кэшированного пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Кэшированный пользователь или None.
        """
        key = f"user:{user_id}"
        return await self._client.get(key)

    async def set_user(self, user_id: str, user: Any, ttl: int = 3600) -> bool:
        """Кэширует пользователя.

        Args:
            user_id: ID пользователя.
            user: Данные пользователя.
            ttl: Время жизни в секундах.

        Returns:
            True если успешно, иначе False.
        """
        key = f"user:{user_id}"
        return await self._client.set(key, user, ttl)

    async def delete_user(self, user_id: str) -> bool:
        """Удаляет кэшированного пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            True если пользователь существовал и был удален, иначе False.
        """
        key = f"user:{user_id}"
        return await self._client.delete(key)

    async def get_document(self, document_id: str) -> Any | None:
        """Возвращает кэшированный документ.

        Args:
            document_id: ID документа.

        Returns:
            Кэшированный документ или None.
        """
        key = f"document:{document_id}"
        return await self._client.get(key)

    async def set_document(self, document_id: str, document: Any, ttl: int = 3600) -> bool:
        """Кэширует документ.

        Args:
            document_id: ID документа.
            document: Данные документа.
            ttl: Время жизни в секундах.

        Returns:
            True если успешно, иначе False.
        """
        key = f"document:{document_id}"
        return await self._client.set(key, document, ttl)

    async def delete_document(self, document_id: str) -> bool:
        """Удаляет кэшированный документ.

        Args:
            document_id: ID документа.

        Returns:
            True если документ существовал и был удален, иначе False.
        """
        key = f"document:{document_id}"
        return await self._client.delete(key)

    async def get_analysis(self, analysis_id: str) -> Any | None:
        """Возвращает кэшированный анализ.

        Args:
            analysis_id: ID анализа.

        Returns:
            Кэшированный анализ или None.
        """
        key = f"analysis:{analysis_id}"
        return await self._client.get(key)

    async def set_analysis(self, analysis_id: str, analysis: Any, ttl: int = 7200) -> bool:
        """Кэширует анализ.

        Args:
            analysis_id: ID анализа.
            analysis: Данные анализа.
            ttl: Время жизни в секундах.

        Returns:
            True если успешно, иначе False.
        """
        key = f"analysis:{analysis_id}"
        return await self._client.set(key, analysis, ttl)

    async def delete_analysis(self, analysis_id: str) -> bool:
        """Удаляет кэшированный анализ.

        Args:
            analysis_id: ID анализа.

        Returns:
            True если анализ существовал и был удален, иначе False.
        """
        key = f"analysis:{analysis_id}"
        return await self._client.delete(key)

    async def get_report(self, analysis_id: str) -> Any | None:
        """Возвращает кэшированный отчет.

        Args:
            analysis_id: ID анализа.

        Returns:
            Кэшированный отчет или None.
        """
        key = f"report:{analysis_id}"
        return await self._client.get(key)

    async def set_report(self, analysis_id: str, report: Any, ttl: int = 3600) -> bool:
        """Кэширует отчет.

        Args:
            analysis_id: ID анализа.
            report: Данные отчета.
            ttl: Время жизни в секундах.

        Returns:
            True если успешно, иначе False.
        """
        key = f"report:{analysis_id}"
        return await self._client.set(key, report, ttl)

    async def delete_report(self, analysis_id: str) -> bool:
        """Удаляет кэшированный отчет.

        Args:
            analysis_id: ID анализа.

        Returns:
            True если отчет существовал и был удален, иначе False.
        """
        key = f"report:{analysis_id}"
        return await self._client.delete(key)

    async def invalidate_user_cache(self, user_id: str) -> bool:
        """Инвалидирует весь кэш пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            True если успешно, иначе False.
        """
        # Удаляем кэш пользователя
        user_key = f"user:{user_id}"
        await self._client.delete(user_key)

        # Находим и удаляем все документы пользователя
        document_keys = await self._client.keys("document:*")
        for key in document_keys:
            await self._client.delete(key)

        return True

    async def invalidate_document_cache(self, document_id: str) -> bool:
        """Инвалидирует кэш документа.

        Args:
            document_id: ID документа.

        Returns:
            True если успешно, иначе False.
        """
        document_key = f"document:{document_id}"
        await self._client.delete(document_key)

        # Инвалидируем связанные анализы и отчеты
        analysis_keys = await self._client.keys("analysis:*")
        for key in analysis_keys:
            await self._client.delete(key)

        report_keys = await self._client.keys("report:*")
        for key in report_keys:
            await self._client.delete(key)

        return True
