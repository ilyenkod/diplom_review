"""
Клиент Redis для работы с кэшем.

Реализует интерфейс CacheClient с использованием redis-py.
"""

from datetime import timedelta
from typing import Any

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.config import settings
from app.core.interfaces.cache import CacheClient
from app.infrastructure.logging import AppLogger


class RedisCacheClient(CacheClient):
    """Клиент Redis для кэширования."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует клиент Redis.

        Args:
            logger: Логгер приложения.
        """
        self._logger = logger
        self._pool: ConnectionPool | None = None
        self._client: Redis[bytes] | None = None

    async def connect(self) -> None:
        """Подключается к Redis."""
        self._pool = ConnectionPool.from_url(
            settings.redis.url,
            max_connections=settings.redis.max_connections,
            decode_responses=settings.redis.decode_responses,
        )
        self._client = Redis(connection_pool=self._pool)
        self._logger.info("Connected to Redis")

    async def disconnect(self) -> None:
        """Отключается от Redis."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Any | None:
        """Возвращает значение по ключу.

        Args:
            key: Ключ.

        Returns:
            Значение или None если ключ не найден.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        value = await self._client.get(key)
        return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | timedelta | None = None,
    ) -> bool:
        """Устанавливает значение по ключу с опциональным TTL.

        Args:
            key: Ключ.
            value: Значение.
            ttl: Время жизни в секундах или timedelta.

        Returns:
            True если успешно, иначе False.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        if ttl is not None:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            result = await self._client.setex(key, ttl, value)
        else:
            result = await self._client.set(key, value)

        return bool(result)

    async def delete(self, key: str) -> bool:
        """Удаляет значение по ключу.

        Args:
            key: Ключ.

        Returns:
            True если ключ существовал и был удален, иначе False.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        result = await self._client.delete(key)
        return bool(result)

    async def exists(self, key: str) -> bool:
        """Проверяет существование ключа.

        Args:
            key: Ключ.

        Returns:
            True если ключ существует, иначе False.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        result = await self._client.exists(key)
        return bool(result)

    async def expire(self, key: str, ttl: int | timedelta) -> bool:
        """Устанавливает TTL для существующего ключа.

        Args:
            key: Ключ.
            ttl: Время жизни в секундах или timedelta.

        Returns:
            True если успешно, иначе False.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        if isinstance(ttl, timedelta):
            ttl = int(ttl.total_seconds())

        result = await self._client.expire(key, ttl)
        return bool(result)

    async def ttl(self, key: str) -> int:
        """Возвращает время жизни ключа в секундах.

        Args:
            key: Ключ.

        Returns:
            Время жизни в секундах. -1 если нет TTL, -2 если ключ не существует.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        return await self._client.ttl(key)

    async def keys(self, pattern: str = "*") -> list[str]:
        """Возвращает список ключей по шаблону.

        Args:
            pattern: Шаблон для поиска ключей.

        Returns:
            Список ключей.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        keys = await self._client.keys(pattern)
        return [key.decode() if isinstance(key, bytes) else key for key in keys]

    async def clear(self) -> bool:
        """Очищает весь кэш.

        Returns:
            True если успешно, иначе False.
        """
        if not self._client:
            msg = "Redis client is not connected"
            raise RuntimeError(msg)

        result = await self._client.flushdb()
        return bool(result)

    async def ping(self) -> bool:
        """Проверяет доступность кэша.

        Returns:
            True если кэш доступен, иначе False.
        """
        if not self._client:
            return False

        try:
            result = await self._client.ping()
            return bool(result)
        except Exception:
            return False
