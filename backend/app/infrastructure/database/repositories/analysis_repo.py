"""
Репозиторий анализов.

Реализует интерфейс AnalysisRepository для работы c анализами в БД.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Analysis
from app.core.interfaces.database import AnalysisRepository as AnalysisRepositoryInterface
from app.infrastructure.database.repositories.base import BaseRepository


class AnalysisRepository(BaseRepository[Analysis], AnalysisRepositoryInterface):
    """Репозиторий анализов."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий анализов.

        Args:
            session: Сессия базы данных.
        """
        super().__init__(session, Analysis)

    async def get_by_document_id(
        self, document_id: str, limit: int = 100, offset: int = 0
    ) -> list[Analysis]:
        """Возвращает анализы документа.

        Args:
            document_id: ID документа.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список анализов документа.
        """
        stmt = (
            select(Analysis)
            .where(self._table.c.document_id == document_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[Analysis]:
        """Возвращает анализы c указанным статусом.

        Args:
            status: Статус анализа.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список анализов c указанным статусом.
        """
        stmt = select(Analysis).where(self._table.c.status == status).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(self, analysis_id: str, status: str) -> bool:
        """Обновляет статус анализа.

        Args:
            analysis_id: ID анализа.
            status: Новый статус.

        Returns:
            True если обновлено, False если не найдено.
        """
        analysis = await self._session.get(Analysis, analysis_id)
        if analysis is None:
            return False
        analysis.status = status
        await self._session.flush()
        return True

    async def update_result(
        self, analysis_id: str, overall_score: float, results: dict[str, Any]
    ) -> bool:
        """Обновляет результат анализа.

        Args:
            analysis_id: ID анализа.
            overall_score: Общая оценка.
            results: Результаты анализа по критериям.

        Returns:
            True если обновлено, False если не найдено.
        """
        analysis = await self._session.get(Analysis, analysis_id)
        if analysis is None:
            return False
        analysis.overall_score = overall_score
        analysis.results = results
        await self._session.flush()
        return True

    async def get_latest_by_document_id(self, document_id: str) -> Analysis | None:
        """Возвращает последний анализ документа.

        Args:
            document_id: ID документа.

        Returns:
            Последний анализ или None если не найден.
        """
        stmt = (
            select(Analysis)
            .where(self._table.c.document_id == document_id)
            .order_by(self._table.c.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
