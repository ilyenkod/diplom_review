"""
Репозиторий отчетов.

Реализует интерфейс ReportRepository для работы c отчетами в БД.
"""

from typing import cast

from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import class_mapper

from app.core.domain import Analysis, Document, Report
from app.core.interfaces.database import ReportRepository as ReportRepositoryInterface
from app.infrastructure.database.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report], ReportRepositoryInterface):
    """Репозиторий отчетов."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий отчетов.

        Args:
            session: Сессия базы данных.
        """
        super().__init__(session, Report)

    async def get_by_analysis_id(self, analysis_id: str) -> Report | None:
        """Возвращает отчет по ID анализа.

        Args:
            analysis_id: ID анализа.

        Returns:
            Отчет или None если не найден.
        """
        stmt = select(Report).where(self._table.c.analysis_id == analysis_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_user(
        self, user_id: str, limit: int = 100, offset: int = 0
    ) -> list[Report]:
        """Возвращает отчеты пользователя.

        Args:
            user_id: ID пользователя.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список отчетов пользователя.
        """
        # Need to join through Analysis -> Document to get user_id
        analysis_table = cast(
            "Table", class_mapper(Analysis).persist_selectable
        )
        document_table = cast(
            "Table", class_mapper(Document).persist_selectable
        )

        stmt = (
            select(Report)
            .select_from(Report)
            .join(analysis_table, Report.analysis_id == analysis_table.c.id)  # type: ignore
            .join(document_table, analysis_table.c.document_id == document_table.c.id)
            .where(document_table.c.user_id == user_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
