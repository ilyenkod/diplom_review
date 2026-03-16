"""
Репозиторий истории версий.

Реализует интерфейс HistoryRepository для работы c историей версий в БД.
"""

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import History
from app.core.interfaces.database import HistoryRepository as HistoryRepositoryInterface
from app.infrastructure.database.repositories.base import BaseRepository


class HistoryRepository(BaseRepository[History], HistoryRepositoryInterface):
    """Репозиторий истории версий."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий истории версий.

        Args:
            session: Сессия базы данных.
        """
        super().__init__(session, History)

    async def get_by_document_id(
        self, document_id: str, limit: int = 100, offset: int = 0
    ) -> list[History]:
        """Возвращает историю версий документа.

        Args:
            document_id: ID документа.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список записей истории документа.
        """
        from sqlalchemy import select

        stmt = (
            select(History)
            .where(self._table.c.document_id == document_id)
            .order_by(self._table.c.version_number.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_version(self, document_id: str, version_number: int) -> History | None:
        """Возвращает версию документа по номеру.

        Args:
            document_id: ID документа.
            version_number: Номер версии.

        Returns:
            Запись истории или None если не найдена.
        """
        from sqlalchemy import select

        stmt = select(History).where(
            and_(
                self._table.c.document_id == document_id,
                self._table.c.version_number == version_number,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_version(self, document_id: str) -> History | None:
        """Возвращает последнюю версию документа.

        Args:
            document_id: ID документа.

        Returns:
            Запись истории c последней версией или None если не найдена.
        """
        from sqlalchemy import select

        stmt = (
            select(History)
            .where(self._table.c.document_id == document_id)
            .order_by(self._table.c.version_number.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_versions_range(
        self, document_id: str, start_version: int, end_version: int
    ) -> list[History]:
        """Возвращает диапазон версий документа.

        Args:
            document_id: ID документа.
            start_version: Начальный номер версии.
            end_version: Конечный номер версии.

        Returns:
            Список записей истории в указанном диапазоне.
        """
        from sqlalchemy import select

        stmt = (
            select(History)
            .where(
                and_(
                    self._table.c.document_id == document_id,
                    self._table.c.version_number >= start_version,
                    self._table.c.version_number <= end_version,
                )
            )
            .order_by(self._table.c.version_number)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
