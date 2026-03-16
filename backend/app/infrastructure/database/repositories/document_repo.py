"""
Репозиторий документов.

Реализует интерфейс DocumentRepository для работы c документами в БД.
"""

from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Document
from app.core.interfaces.database import DocumentRepository as DocumentRepositoryInterface
from app.infrastructure.database.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document], DocumentRepositoryInterface):
    """Репозиторий документов."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий документов.

        Args:
            session: Сессия базы данных.
        """
        super().__init__(session, Document)

    async def get_by_user_id(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> list[Document]:
        """Возвращает документы пользователя.

        Args:
            user_id: ID пользователя.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список документов пользователя.
        """
        stmt = select(Document).where(self._table.c.user_id == user_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_file_type(
        self, file_type: str, limit: int = 100, offset: int = 0
    ) -> list[Document]:
        """Возвращает документы указанного типа.

        Args:
            file_type: Тип файла.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список документов указанного типа.
        """
        stmt = (
            select(Document).where(self._table.c.file_type == file_type).limit(limit).offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_content(self, document_id: str, content: str) -> bool:
        """Обновляет содержимое документа.

        Args:
            document_id: ID документа.
            content: Новое содержимое.

        Returns:
            True если обновлено, False если не найдено.
        """
        stmt = update(self._table).where(self._table.c.id == document_id).values(content=content)
        result = await self._session.execute(stmt)
        await self._session.flush()
        result_cast = cast(CursorResult[Any], result)
        return result_cast.rowcount > 0

    async def get_by_filename(self, user_id: str, filename: str) -> Document | None:
        """Возвращает документ по имени файла пользователя.

        Args:
            user_id: ID пользователя.
            filename: Имя файла.

        Returns:
            Документ или None если не найден.
        """
        stmt = select(Document).where(
            self._table.c.user_id == user_id, self._table.c.filename == filename
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
