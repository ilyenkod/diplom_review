"""Эндпоинты анализа документов.

Предоставляет API для запуска анализа, получения статуса и результатов анализа.
"""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Analysis
from app.core.exceptions import (
    AnalysisAlreadyRunningError,
    AnalysisFailedError,
    AnalysisNotFoundError,
    AnalyzerError,
    DocumentNotFoundError,
)
from app.core.services.analysis_service import AnalysisService
from app.infrastructure.api.deps import (
    get_cache,
    get_current_user,
    get_db,
    get_llm_client,
)
from app.infrastructure.api.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisReanalyzeRequest,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusEnum,
    AnalysisStatusResponse,
)
from app.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from app.core.domain import User

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = get_logger("api.v1.analysis")


def get_analysis_service(
    db: AsyncSession = Depends(get_db),
    cache: Any = Depends(get_cache),
    llm_client: Any = Depends(get_llm_client),
) -> AnalysisService:
    """Возвращает сервис анализа.

    Args:
        db: Сессия базы данных.
        cache: Клиент кэша.
        llm_client: Клиент LLM.

    Returns:
        Экземпляр AnalysisService.
    """
    from app.core.services.analysis_service import AnalysisConfig
    from app.infrastructure.cache.repository import RedisCacheRepository
    from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
    from app.infrastructure.database.repositories.document_repo import DocumentRepository

    logger_value = get_logger("services.analysis")
    analysis_repo = AnalysisRepository(db)
    document_repo = DocumentRepository(db)
    cache_repo = RedisCacheRepository(cache, logger_value)

    return AnalysisService(
        analysis_repo=analysis_repo,
        document_repo=document_repo,
        cache_repo=cache_repo,
        llm_client=llm_client,
        logger=logger_value,
        config=AnalysisConfig(),
    )


@router.post(
    "/start",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Запуск анализа документа",
    description="Запускает анализ указанного документа.",
)
async def start_analysis(
    request: AnalysisRequest,
    current_user: "User" = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> Analysis:
    """Запускает анализ документа.

    Args:
        request: Запрос на анализ с ID документа и опциями.
        current_user: Текущий пользователь.
        analysis_service: Сервис анализа.

    Returns:
        Созданная запись анализа.

    Raises:
        HTTPException: Если документ не найден или анализ уже выполняется.
    """
    try:
        analysis = await analysis_service.start_analysis(request.document_id)
        logger.info(
            "Analysis started",
            extra={
                "analysis_id": analysis.id,
                "document_id": request.document_id,
                "user_id": current_user.id,
            },
        )
        return analysis
    except DocumentNotFoundError as e:
        logger.warning(
            "Analysis start failed: document not found",
            extra={"document_id": request.document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except AnalysisAlreadyRunningError as e:
        logger.warning(
            "Analysis start failed: analysis already running",
            extra={"document_id": request.document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisStatusResponse,
    summary="Получение статуса анализа",
    description="Возвращает текущий статус анализа.",
)
async def get_analysis_status(
    analysis_id: str,
    current_user: "User" = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisStatusResponse:
    """Получает статус анализа.

    Args:
        analysis_id: ID анализа.
        current_user: Текущий пользователь.
        analysis_service: Сервис анализа.

    Returns:
        Статус анализа с прогрессом.

    Raises:
        HTTPException: Если анализ не найден.
    """
    try:
        analysis = await analysis_service.get_analysis(analysis_id)

        # Вычисляем прогресс на основе статуса
        progress = 0.0
        if analysis.is_processing:
            progress = 50.0
        elif analysis.is_completed or analysis.is_failed:
            progress = 100.0

        logger.info(
            "Analysis status retrieved",
            extra={
                "analysis_id": analysis_id,
                "status": analysis.status,
                "user_id": current_user.id,
            },
        )

        return AnalysisStatusResponse(
            id=analysis.id,
            status=AnalysisStatusEnum(analysis.status),
            progress=progress,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
        )
    except AnalysisNotFoundError as e:
        logger.warning(
            "Analysis status failed: analysis not found",
            extra={"analysis_id": analysis_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/{analysis_id}",
    response_model=AnalysisDetailResponse,
    summary="Получение результата анализа",
    description="Возвращает полный результат анализа.",
)
async def get_analysis(
    analysis_id: str,
    current_user: "User" = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisDetailResponse:
    """Получает результат анализа.

    Args:
        analysis_id: ID анализа.
        current_user: Текущий пользователь.
        analysis_service: Сервис анализа.

    Returns:
        Детальный результат анализа.

    Raises:
        HTTPException: Если анализ не найден.
    """
    try:
        analysis = await analysis_service.get_analysis(analysis_id)

        # Формируем оценки по критериям
        criteria_scores: dict[str, float] = {}
        recommendations: list[str] = []

        if analysis.results:
            for criterion, result_data in analysis.results.items():
                if isinstance(result_data, dict) and "score" in result_data:
                    criteria_scores[criterion] = float(result_data["score"])
                    if "recommendations" in result_data:
                        recs = result_data["recommendations"]
                        if isinstance(recs, list):
                            recommendations.extend(recs)

        logger.info(
            "Analysis retrieved",
            extra={
                "analysis_id": analysis_id,
                "status": analysis.status,
                "user_id": current_user.id,
            },
        )

        return AnalysisDetailResponse(
            id=analysis.id,
            document_id=analysis.document_id,
            status=AnalysisStatusEnum(analysis.status),
            overall_score=analysis.overall_score,
            results=analysis.results,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message,
            created_at=analysis.created_at or analysis.created_at,
            updated_at=analysis.updated_at,
            duration=analysis.duration,
            criteria_scores=criteria_scores,
            recommendations=recommendations,
        )
    except AnalysisNotFoundError as e:
        logger.warning(
            "Analysis retrieval failed: analysis not found",
            extra={"analysis_id": analysis_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.post(
    "/{analysis_id}/reanalyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Повторный анализ документа",
    description="Запускает повторный анализ документа.",
)
async def reanalyze_document(
    analysis_id: str,
    request: AnalysisReanalyzeRequest | None = None,
    current_user: "User" = Depends(get_current_user),
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> Analysis:
    """Запускает повторный анализ документа.

    Args:
        analysis_id: ID предыдущего анализа.
        request: Опциональные параметры повторного анализа.
        current_user: Текущий пользователь.
        analysis_service: Сервис анализа.

    Returns:
        Новая запись анализа.

    Raises:
        HTTPException: Если документ не найден или анализ невозможен.
    """
    try:
        # Получаем предыдущий анализ для извлечения document_id
        previous_analysis = await analysis_service.get_analysis(analysis_id)
        document_id = previous_analysis.document_id if request is None else request.document_id

        # Запускаем повторный анализ
        analysis = await analysis_service.reanalyze_document(document_id)

        logger.info(
            "Document reanalyzed",
            extra={
                "new_analysis_id": analysis.id,
                "previous_analysis_id": analysis_id,
                "document_id": document_id,
                "user_id": current_user.id,
            },
        )

        return analysis
    except AnalysisNotFoundError as e:
        logger.warning(
            "Reanalysis failed: analysis not found",
            extra={"analysis_id": analysis_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except DocumentNotFoundError as e:
        logger.warning(
            "Reanalysis failed: document not found",
            extra={
                "analysis_id": analysis_id,
                "document_id": document_id,
                "user_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except (AnalysisFailedError, AnalyzerError) as e:
        logger.error(
            "Reanalysis failed",
            extra={
                "analysis_id": analysis_id,
                "error": str(e),
                "user_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
