"""
Сервис истории версий документов.

Управляет сохранением версий документов и работой с историей проверок.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.const import AnalysisCriteria
from app.core.domain import History
from app.core.exceptions import DocumentNotFoundError, HistoryNotFoundError, VersionNotFoundError
from app.core.interfaces.database import AnalysisRepository, DocumentRepository, HistoryRepository
from app.infrastructure.logging import AppLogger


@dataclass
class VersionInfo:
    """Информация о версии документа."""

    version_number: int
    analysis_id: str
    overall_score: float | None
    created_at: datetime
    changes_summary: dict[str, Any]


class HistoryService:
    """Сервис для работы с историей версий документов."""

    def __init__(
        self,
        history_repo: HistoryRepository,
        analysis_repo: AnalysisRepository,
        document_repo: DocumentRepository,
        logger: AppLogger,
    ) -> None:
        """Инициализирует сервис истории.

        Args:
            history_repo: Репозиторий истории версий.
            analysis_repo: Репозиторий анализов.
            document_repo: Репозиторий документов.
            logger: Логгер приложения.
        """
        self._history_repo = history_repo
        self._analysis_repo = analysis_repo
        self._document_repo = document_repo
        self._logger = logger

    async def save_version(
        self,
        document_id: str,
        analysis_id: str,
        changes_summary: dict[str, Any] | None = None,
    ) -> History:
        """Сохраняет версию документа с результатами анализа.

        Args:
            document_id: ID документа.
            analysis_id: ID анализа.
            changes_summary: Сводка изменений относительно предыдущей версии.

        Returns:
            Созданная запись истории версий.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        # Проверяем существование анализа
        analysis = await self._analysis_repo.get_by_id(analysis_id)
        if analysis is None:
            raise DocumentNotFoundError(document_id)

        if not analysis.is_completed:
            raise ValueError("Analysis must be completed to save version")

        # Определяем номер версии
        latest_version = await self._history_repo.get_latest_version(document_id)
        version_number = (latest_version.version_number + 1) if latest_version else 1

        # Если не передана сводка изменений, вычисляем её
        if changes_summary is None:
            changes_summary = await self._compute_changes(document_id, analysis_id)

        # Создаем запись истории
        history = History(
            id=self._generate_id(),
            document_id=document_id,
            version_number=version_number,
            analysis_id=analysis_id,
            changes_summary=changes_summary,
        )

        created_history = await self._history_repo.create(history)

        self._logger.info(
            "Version saved",
            extra={
                "history_id": created_history.id,
                "document_id": document_id,
                "version_number": version_number,
                "analysis_id": analysis_id,
            },
        )

        return created_history

    async def get_document_history(
        self,
        document_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[History]:
        """Возвращает историю версий документа.

        Args:
            document_id: ID документа.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список записей истории версий документа.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        return await self._history_repo.get_by_document_id(document_id, limit, offset)

    async def get_version(
        self,
        document_id: str,
        version_number: int,
    ) -> History:
        """Возвращает конкретную версию документа.

        Args:
            document_id: ID документа.
            version_number: Номер версии.

        Returns:
            Запись истории версий.

        Raises:
            DocumentNotFoundError: Если документ не найден.
            VersionNotFoundError: Если версия не найдена.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        history = await self._history_repo.get_by_version(document_id, version_number)
        if history is None:
            raise VersionNotFoundError(document_id, version_number)

        return history

    async def get_latest_version(self, document_id: str) -> History | None:
        """Возвращает последнюю версию документа.

        Args:
            document_id: ID документа.

        Returns:
            Последняя версия или None если версий нет.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        return await self._history_repo.get_latest_version(document_id)

    async def get_versions_range(
        self,
        document_id: str,
        start_version: int,
        end_version: int,
    ) -> list[History]:
        """Возвращает диапазон версий документа.

        Args:
            document_id: ID документа.
            start_version: Начальный номер версии.
            end_version: Конечный номер версии.

        Returns:
            Список записей истории в указанном диапазоне.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        if start_version > end_version:
            start_version, end_version = end_version, start_version

        return await self._history_repo.get_versions_range(document_id, start_version, end_version)

    async def get_version_info(
        self,
        document_id: str,
        version_number: int,
    ) -> VersionInfo:
        """Возвращает детальную информацию о версии.

        Args:
            document_id: ID документа.
            version_number: Номер версии.

        Returns:
            Информация о версии.

        Raises:
            DocumentNotFoundError: Если документ не найден.
            VersionNotFoundError: Если версия не найдена.
        """
        history = await self.get_version(document_id, version_number)
        analysis = await self._analysis_repo.get_by_id(history.analysis_id)

        if analysis is None:
            raise HistoryNotFoundError(history.id)

        return VersionInfo(
            version_number=history.version_number,
            analysis_id=history.analysis_id,
            overall_score=analysis.overall_score,
            created_at=history.created_at or datetime.utcnow(),
            changes_summary=history.changes_summary,
        )

    async def _compute_changes(
        self,
        document_id: str,
        analysis_id: str,
    ) -> dict[str, Any]:
        """Вычисляет изменения относительно предыдущей версии.

        Args:
            document_id: ID документа.
            analysis_id: ID нового анализа.

        Returns:
            Сводка изменений.
        """
        # Получаем текущий анализ
        current_analysis = await self._analysis_repo.get_by_id(analysis_id)
        if current_analysis is None or not current_analysis.is_completed:
            return {"summary": "Analysis not completed"}

        # Получаем предыдущую версию
        previous_version = await self._history_repo.get_latest_version(document_id)

        if previous_version is None:
            return {
                "summary": "Первая версия документа",
                "overall_score_diff": None,
                "criteria_changes": None,
            }

        # Получаем предыдущий анализ
        previous_analysis = await self._analysis_repo.get_by_id(previous_version.analysis_id)
        if previous_analysis is None or not previous_analysis.is_completed:
            return {
                "summary": "Предыдущая версия не завершена",
                "overall_score_diff": None,
                "criteria_changes": None,
            }

        # Вычисляем разницу в общей оценке
        overall_score_diff: float | None = None
        if (
            current_analysis.overall_score is not None
            and previous_analysis.overall_score is not None
        ):
            overall_score_diff = current_analysis.overall_score - previous_analysis.overall_score

        # Вычисляем изменения по критериям
        criteria_changes: dict[str, float] = {}
        if current_analysis.results and previous_analysis.results:
            for criterion in AnalysisCriteria.ALL:
                current_result = current_analysis.results.get(criterion)
                previous_result = previous_analysis.results.get(criterion)

                if (
                    isinstance(current_result, dict)
                    and isinstance(previous_result, dict)
                    and "score" in current_result
                    and "score" in previous_result
                ):
                    current_score = float(current_result["score"])
                    previous_score = float(previous_result["score"])
                    criteria_changes[criterion] = current_score - previous_score

        # Формируем текстовую сводку
        summary = self._build_changes_summary(overall_score_diff, criteria_changes)

        return {
            "summary": summary,
            "overall_score_diff": overall_score_diff,
            "criteria_changes": criteria_changes,
        }

    def _build_changes_summary(
        self,
        overall_score_diff: float | None,
        criteria_changes: dict[str, float],
    ) -> str:
        """Строит текстовую сводку изменений.

        Args:
            overall_score_diff: Изменение общей оценки.
            criteria_changes: Изменения по критериям.

        Returns:
            Текстовая сводка изменений.
        """
        parts: list[str] = []

        # Общая оценка
        if overall_score_diff is not None:
            if overall_score_diff > 0.5:
                parts.append(f"Общая оценка улучшилась на {overall_score_diff:+.1f}")
            elif overall_score_diff < -0.5:
                parts.append(f"Общая оценка снизилась на {overall_score_diff:+.1f}")
            else:
                parts.append("Общая оценка существенно не изменилась")

        # Изменения по критериям
        improvements: list[str] = []
        deteriorations: list[str] = []

        for criterion, diff in criteria_changes.items():
            criterion_name = AnalysisCriteria.DESCRIPTIONS.get(criterion, criterion)
            if diff > 0.5:
                improvements.append(f"{criterion_name} (+{diff:.1f})")
            elif diff < -0.5:
                deteriorations.append(f"{criterion_name} ({diff:.1f})")

        if improvements:
            parts.append(f"Улучшено: {', '.join(improvements)}")
        if deteriorations:
            parts.append(f"Ухудшено: {', '.join(deteriorations)}")

        return ". ".join(parts) if parts else "Изменений не обнаружено"

    async def delete_history(
        self,
        document_id: str,
        version_number: int | None = None,
    ) -> bool:
        """Удаляет запись истории.

        Args:
            document_id: ID документа.
            version_number: Номер версии для удаления. Если None, удаляется вся история.

        Returns:
            True если удалено успешно.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        if version_number is not None:
            history = await self._history_repo.get_by_version(document_id, version_number)
            if history is not None:
                await self._history_repo.delete(history.id)
                self._logger.info(
                    "History record deleted",
                    extra={"document_id": document_id, "version_number": version_number},
                )
                return True
            return False
        else:
            # Удаляем всю историю документа
            histories = await self._history_repo.get_by_document_id(document_id)
            for history in histories:
                await self._history_repo.delete(history.id)

            self._logger.info(
                "All history deleted",
                extra={"document_id": document_id, "count": len(histories)},
            )
            return len(histories) > 0

    def _generate_id(self) -> str:
        """Генерирует уникальный ID.

        Returns:
            Уникальный ID.
        """
        import uuid

        return str(uuid.uuid4())
