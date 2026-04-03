"""Эндпоинты истории версий документов.

Предоставляет API для работы с историей проверок и сравнения версий.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DocumentNotFoundError, VersionNotFoundError
from app.core.services.comparison_service import ComparisonService, VersionComparison
from app.core.services.history_service import HistoryService
from app.infrastructure.api.deps import get_current_user, get_db
from app.infrastructure.api.schemas.history import (
    HistoryDetail,
    HistoryListResponse,
    VersionComparisonRequest,
    VersionListResponse,
)
from app.infrastructure.api.schemas.history import (
    VersionComparison as VersionComparisonSchema,
)
from app.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from app.core.domain import User

router = APIRouter(prefix="/history", tags=["history"])
logger = get_logger("api.v1.history")


def get_history_service(
    db: AsyncSession = Depends(get_db),
) -> HistoryService:
    """Возвращает сервис истории.

    Args:
        db: Сессия базы данных.

    Returns:
        Экземпляр HistoryService.
    """
    from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
    from app.infrastructure.database.repositories.document_repo import DocumentRepository
    from app.infrastructure.database.repositories.history_repo import HistoryRepository

    logger_value = get_logger("services.history")
    history_repo = HistoryRepository(db)
    analysis_repo = AnalysisRepository(db)
    document_repo = DocumentRepository(db)

    return HistoryService(
        history_repo=history_repo,
        analysis_repo=analysis_repo,
        document_repo=document_repo,
        logger=logger_value,
    )


def get_comparison_service(
    db: AsyncSession = Depends(get_db),
) -> ComparisonService:
    """Возвращает сервис сравнения версий.

    Args:
        db: Сессия базы данных.

    Returns:
        Экземпляр ComparisonService.
    """
    from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
    from app.infrastructure.database.repositories.document_repo import DocumentRepository
    from app.infrastructure.database.repositories.history_repo import HistoryRepository

    logger_value = get_logger("services.comparison")
    history_repo = HistoryRepository(db)
    analysis_repo = AnalysisRepository(db)
    document_repo = DocumentRepository(db)

    return ComparisonService(
        history_repo=history_repo,
        analysis_repo=analysis_repo,
        document_repo=document_repo,
        logger=logger_value,
    )


@router.get(
    "/",
    response_model=list[HistoryListResponse],
    summary="История проверок пользователя",
    description="Возвращает историю проверок документов текущего пользователя.",
)
async def get_user_history(
    document_id: str | None = Query(default=None, description="Фильтр по ID документа"),
    limit: int = Query(default=100, ge=1, le=100, description="Максимальное количество записей"),
    offset: int = Query(default=0, ge=0, description="Смещение"),
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    history_service: HistoryService = Depends(get_history_service),
) -> list[HistoryListResponse]:
    """Получает историю проверок пользователя.

    Args:
        document_id: Опциональный фильтр по ID документа.
        limit: Максимальное количество записей.
        offset: Смещение.
        current_user: Текущий пользователь.
        db: Сессия базы данных.
        history_service: Сервис истории.

    Returns:
        Список записей истории.

    Raises:
        HTTPException: Если документ не найден (если указан document_id).
    """
    # Если указан document_id, возвращаем историю только этого документа
    if document_id:
        try:
            history_records = await history_service.get_document_history(
                document_id=document_id,
                limit=limit,
                offset=offset,
            )
        except DocumentNotFoundError as e:
            logger.warning(
                "History retrieval failed: document not found",
                extra={"document_id": document_id, "user_id": current_user.id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
    else:
        # Если document_id не указан, получаем все документы пользователя и их историю
        from app.infrastructure.database.repositories.document_repo import DocumentRepository

        document_repo = DocumentRepository(db)
        documents = await document_repo.get_by_user_id(
            user_id=current_user.id, limit=limit, offset=offset
        )

        # Получаем историю для каждого документа
        history_records: list[Any] = []
        for document in documents:
            try:
                doc_history = await history_service.get_document_history(
                    document_id=document.id, limit=10, offset=0
                )
                history_records.extend(doc_history)
            except DocumentNotFoundError:
                pass

    # Формируем ответ
    result: list[HistoryListResponse] = []

    for record in history_records:
        # Получаем анализ для оценки
        analysis = await history_service._analysis_repo.get_by_id(record.analysis_id)

        versions: list[VersionListResponse] = []
        versions.append(
            VersionListResponse(
                version_number=record.version_number,
                created_at=record.created_at or datetime.utcnow(),
                overall_score=analysis.overall_score if analysis else None,
            )
        )

        result.append(
            HistoryListResponse(
                document_id=record.document_id,
                versions=versions,
                total_versions=len(versions),
            )
        )

    logger.info(
        "History retrieved",
        extra={
            "user_id": current_user.id,
            "document_id": document_id,
            "count": len(result),
        },
    )

    return result


@router.get(
    "/{document_id}/versions",
    response_model=list[HistoryDetail],
    summary="Версии документа",
    description="Возвращает все версии указанного документа.",
)
async def get_document_versions(
    document_id: str,
    limit: int = Query(default=100, ge=1, le=100, description="Максимальное количество версий"),
    offset: int = Query(default=0, ge=0, description="Смещение"),
    current_user: "User" = Depends(get_current_user),
    history_service: HistoryService = Depends(get_history_service),
) -> list[HistoryDetail]:
    """Получает версии документа.

    Args:
        document_id: ID документа.
        limit: Максимальное количество версий.
        offset: Смещение.
        current_user: Текущий пользователь.
        history_service: Сервис истории.

    Returns:
        Список версий документа.

    Raises:
        HTTPException: Если документ не найден.
    """
    try:
        history_records = await history_service.get_document_history(
            document_id=document_id,
            limit=limit,
            offset=offset,
        )

        result: list[HistoryDetail] = []

        for record in history_records:
            # Получаем анализ для оценки
            analysis = await history_service._analysis_repo.get_by_id(record.analysis_id)

            # Формируем детали
            overall_score_diff: float | None = None
            criteria_changes: dict[str, float] = {}

            if record.changes_summary:
                overall_score_diff = record.changes_summary.get("overall_score_diff")
                criteria_changes = record.changes_summary.get("criteria_changes", {})

            result.append(
                HistoryDetail(
                    id=record.id,
                    document_id=record.document_id,
                    version_number=record.version_number,
                    analysis_id=record.analysis_id,
                    changes_summary=record.changes_summary,
                    created_at=record.created_at or datetime.utcnow(),
                    overall_score=analysis.overall_score if analysis else None,
                    overall_score_diff=overall_score_diff,
                    criteria_changes=criteria_changes,
                    summary=record.changes_summary.get("summary")
                    if record.changes_summary
                    else None,
                )
            )

        logger.info(
            "Document versions retrieved",
            extra={
                "document_id": document_id,
                "user_id": current_user.id,
                "count": len(result),
            },
        )

        return result

    except DocumentNotFoundError as e:
        logger.warning(
            "Document versions retrieval failed: document not found",
            extra={"document_id": document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/compare",
    response_model=VersionComparisonSchema,
    summary="Сравнение версий документа",
    description="Сравнивает две версии документа и возвращает разницу в оценках.",
)
async def compare_versions(
    request: VersionComparisonRequest,
    current_user: "User" = Depends(get_current_user),
    comparison_service: ComparisonService = Depends(get_comparison_service),
) -> VersionComparisonSchema:
    """Сравнивает две версии документа.

    Args:
        request: Запрос на сравнение с номерами версий.
        current_user: Текущий пользователь.
        comparison_service: Сервис сравнения.

    Returns:
        Результат сравнения версий.

    Raises:
        HTTPException: Если документ или версии не найдены.
    """
    try:
        comparison: VersionComparison = await comparison_service.compare_versions(
            document_id=request.document_id,
            previous_version=request.version_from,
            current_version=request.version_to,
        )

        # Преобразуем в схему API
        # Формируем списки улучшенных/ухудшившихся критериев
        improved: list[str] = []
        degraded: list[str] = []
        unchanged: list[str] = []
        criteria_diff_dict: dict[str, float] = {}

        for comp in comparison.criteria_comparisons:
            if comp.difference is not None:
                criteria_diff_dict[comp.criterion_name] = comp.difference
            if comp.trend == "improved":
                improved.append(f"{comp.criterion_name}: {comp.difference:+.1f}")
            elif comp.trend == "worsened":
                degraded.append(f"{comp.criterion_name}: {comp.difference:+.1f}")
            else:
                unchanged.append(comp.criterion_name)

        result = VersionComparisonSchema(
            document_id=comparison.document_id,
            version_from=comparison.previous_version,
            version_to=comparison.current_version,
            overall_score_diff=comparison.overall_score_diff or 0.0,
            criteria_diff=criteria_diff_dict,
            improved=improved,
            degraded=degraded,
            unchanged=unchanged,
            summary=comparison.summary,
        )

        logger.info(
            "Versions compared",
            extra={
                "document_id": request.document_id,
                "version_from": request.version_from,
                "version_to": request.version_to,
                "user_id": current_user.id,
            },
        )

        return result

    except DocumentNotFoundError as e:
        logger.warning(
            "Version comparison failed: document not found",
            extra={"document_id": request.document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except VersionNotFoundError as e:
        logger.warning(
            "Version comparison failed: version not found",
            extra={
                "document_id": request.document_id,
                "version_from": request.version_from,
                "version_to": request.version_to,
                "user_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ValueError as e:
        logger.error(
            "Version comparison failed",
            extra={
                "document_id": request.document_id,
                "error": str(e),
                "user_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
