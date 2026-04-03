"""Эндпоинты отчетов.

Предоставляет API для получения и скачивания отчетов по анализу.
"""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Report
from app.core.exceptions import AnalysisNotFoundError, ReportNotFoundError
from app.core.services.report_service import ReportService
from app.infrastructure.api.deps import (
    get_current_user,
    get_db,
    get_llm_client,
)
from app.infrastructure.api.schemas.report import ReportDetailResponse
from app.infrastructure.logging import get_logger

if TYPE_CHECKING:
    from app.core.domain import User

router = APIRouter(prefix="/reports", tags=["reports"])
logger = get_logger("api.v1.reports")


def get_report_service(
    db: AsyncSession = Depends(get_db),
    llm_client: Any = Depends(get_llm_client),
) -> ReportService:
    """Возвращает сервис отчетов.

    Args:
        db: Сессия базы данных.
        llm_client: Клиент LLM.

    Returns:
        Экземпляр ReportService.
    """
    from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
    from app.infrastructure.database.repositories.report_repo import ReportRepository

    logger_value = get_logger("services.report")
    report_repo = ReportRepository(db)
    analysis_repo = AnalysisRepository(db)

    return ReportService(
        report_repo=report_repo,
        analysis_repo=analysis_repo,
        llm_client=llm_client,
        logger=logger_value,
    )


@router.get(
    "/{analysis_id}",
    response_model=ReportDetailResponse,
    summary="Получение отчета по анализу",
    description="Возвращает отчет по указанному анализу.",
)
async def get_report(
    analysis_id: str,
    generate: bool = Query(default=False, description="Сгенерировать отчет, если он не существует"),
    current_user: "User" = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> ReportDetailResponse:
    """Получает отчет по анализу.

    Args:
        analysis_id: ID анализа.
        generate: Флаг генерации отчета, если не существует.
        current_user: Текущий пользователь.
        report_service: Сервис отчетов.

    Returns:
        Отчет по анализу.

    Raises:
        HTTPException: Если анализ не найден или ошибка генерации отчета.
    """
    try:
        # Сначала пробуем получить существующий отчет
        report = await report_service.get_report_by_analysis(analysis_id)

        if report is None:
            if not generate:
                logger.info(
                    "Report not found, generation not requested",
                    extra={"analysis_id": analysis_id, "user_id": current_user.id},
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found. Set generate=true to create a new report.",
                )

            # Генерируем новый отчет
            report = await report_service.generate_report(analysis_id)
            logger.info(
                "Report generated",
                extra={
                    "report_id": report.id,
                    "analysis_id": analysis_id,
                    "user_id": current_user.id,
                },
            )

        # Формируем детальный ответ
        analysis = await report_service._analysis_repo.get_by_id(analysis_id)

        criteria_scores: dict[str, float] = {}
        analysis_results: dict[str, Any] = {}

        if analysis and analysis.results:
            analysis_results = analysis.results
            for criterion, result_data in analysis.results.items():
                if isinstance(result_data, dict) and "score" in result_data:
                    criteria_scores[criterion] = float(result_data["score"])

        overall_score = analysis.overall_score if analysis else 0.0 or 0.0

        # Определяем сильные и слабые стороны
        strengths: list[str] = []
        weaknesses: list[str] = []

        if analysis and analysis.results:
            for criterion, result_data in analysis.results.items():
                if isinstance(result_data, dict):
                    score = result_data.get("score", 0.0)
                    criterion_name = criterion

                    if score >= 7.0:
                        strengths.append(criterion_name)
                    elif score < 5.0:
                        weaknesses.append(criterion_name)

        logger.info(
            "Report retrieved",
            extra={
                "report_id": report.id,
                "analysis_id": analysis_id,
                "user_id": current_user.id,
            },
        )

        return ReportDetailResponse(
            id=report.id,
            analysis_id=report.analysis_id,
            overall_assessment=report.overall_assessment,
            recommendations=report.recommendations,
            supervisor_comments=report.supervisor_comments,
            generated_at=report.generated_at,
            analysis_results=analysis_results,
            criteria_scores=criteria_scores,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
        )
    except AnalysisNotFoundError as e:
        logger.warning(
            "Report retrieval failed: analysis not found",
            extra={"analysis_id": analysis_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except ReportNotFoundError as e:
        logger.warning(
            "Report not found",
            extra={"analysis_id": analysis_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@router.get(
    "/{analysis_id}/pdf",
    summary="Скачивание PDF отчета",
    description="Возвращает отчет в формате PDF.",
)
async def download_report_pdf(
    analysis_id: str,
    current_user: "User" = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> Response:
    """Скачивает отчет в формате PDF.

    Args:
        analysis_id: ID анализа.
        current_user: Текущий пользователь.
        report_service: Сервис отчетов.

    Returns:
        PDF файл отчета.

    Raises:
        HTTPException: Если отчет не найден или ошибка генерации.
    """
    try:
        # Получаем или генерируем отчет
        report = await report_service.get_report_by_analysis(analysis_id)
        if report is None:
            report = await report_service.generate_report(analysis_id)

        # Генерируем PDF контент
        pdf_content = _generate_pdf_content(report)

        logger.info(
            "PDF report downloaded",
            extra={
                "report_id": report.id,
                "analysis_id": analysis_id,
                "user_id": current_user.id,
            },
        )

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="report_{analysis_id}.pdf"',
            },
        )
    except AnalysisNotFoundError as e:
        logger.warning(
            "PDF report download failed: analysis not found",
            extra={"analysis_id": analysis_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "PDF report generation failed",
            extra={
                "analysis_id": analysis_id,
                "error": str(e),
                "user_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF report",
        ) from e


@router.get(
    "/{analysis_id}/docx",
    summary="Скачивание DOCX отчета",
    description="Возвращает отчет в формате DOCX.",
)
async def download_report_docx(
    analysis_id: str,
    current_user: "User" = Depends(get_current_user),
    report_service: ReportService = Depends(get_report_service),
) -> Response:
    """Скачивает отчет в формате DOCX.

    Args:
        analysis_id: ID анализа.
        current_user: Текущий пользователь.
        report_service: Сервис отчетов.

    Returns:
        DOCX файл отчета.

    Raises:
        HTTPException: Если отчет не найден или ошибка генерации.
    """
    try:
        # Получаем или генерируем отчет
        report = await report_service.get_report_by_analysis(analysis_id)
        if report is None:
            report = await report_service.generate_report(analysis_id)

        # Генерируем DOCX контент
        docx_content = _generate_docx_content(report)

        logger.info(
            "DOCX report downloaded",
            extra={
                "report_id": report.id,
                "analysis_id": analysis_id,
                "user_id": current_user.id,
            },
        )

        return Response(
            content=docx_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="report_{analysis_id}.docx"',
            },
        )
    except AnalysisNotFoundError as e:
        logger.warning(
            "DOCX report download failed: analysis not found",
            extra={"analysis_id": analysis_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "DOCX report generation failed",
            extra={
                "analysis_id": analysis_id,
                "error": str(e),
                "user_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate DOCX report",
        ) from e


def _generate_pdf_content(report: Report) -> bytes:
    """Генерирует PDF контент из отчета.

    Args:
        report: Отчет.

    Returns:
        PDF контент в байтах.
    """
    # Формируем простой PDF (текстовый формат)
    lines: list[str] = [
        "Отчет по анализу документа",
        "=" * 50,
        "",
        f"ID отчета: {report.id}",
        f"ID анализа: {report.analysis_id}",
        "",
        "Общая оценка:",
        report.overall_assessment or "Не указана",
        "",
        "Рекомендации:",
    ]

    if report.recommendations:
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
    else:
        lines.append("-")

    lines.extend(
        [
            "",
            "Комментарии руководителя:",
        ]
    )

    if report.supervisor_comments:
        for i, comment in enumerate(report.supervisor_comments, 1):
            lines.append(f"{i}. {comment}")
    else:
        lines.append("-")

    if report.generated_at:
        lines.append(f"\nСгенерировано: {report.generated_at.isoformat()}")

    content = "\n".join(lines)
    return content.encode("utf-8")


def _generate_docx_content(report: Report) -> bytes:
    """Генерирует DOCX контент из отчета.

    Args:
        report: Отчет.

    Returns:
        DOCX контент в байтах.
    """
    # Формируем простой текстовый контент (упрощенная версия DOCX)
    lines: list[str] = [
        "ОТЧЕТ ПО АНАЛИЗУ ДОКУМЕНТА",
        "=" * 60,
        "",
        f"ID отчета: {report.id}",
        f"ID анализа: {report.analysis_id}",
        "",
        "ОБЩАЯ ОЦЕНКА",
        "-" * 40,
        report.overall_assessment or "Не указана",
        "",
        "РЕКОМЕНДАЦИИ",
        "-" * 40,
    ]

    if report.recommendations:
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
    else:
        lines.append("-")

    lines.extend(
        [
            "",
            "КОММЕНТАРИИ РУКОВОДИТЕЛЯ",
            "-" * 40,
        ]
    )

    if report.supervisor_comments:
        for i, comment in enumerate(report.supervisor_comments, 1):
            lines.append(f"{i}. {comment}")
    else:
        lines.append("-")

    if report.generated_at:
        lines.append(f"\nСгенерировано: {report.generated_at.isoformat()}")

    content = "\n".join(lines)
    return content.encode("utf-8")
