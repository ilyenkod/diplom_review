"""V1 API Router."""

from fastapi import APIRouter

from app.infrastructure.api.v1 import analysis, auth, documents, history, reports
from app.infrastructure.logging import get_logger

router = APIRouter(prefix="/api/v1", tags=["v1"])
logger = get_logger("api.v1.router")


def include_subrouters() -> None:
    """Подключает подроутеры к v1 роутеру.

    Заглушки для фазы 5, полная реализация будет в фазах 8 и 10.
    """
    logger.info("Including subrouters (stubs for phase 5)")
    router.include_router(auth.router, prefix="/auth", tags=["auth"])
    router.include_router(documents.router, prefix="/documents", tags=["documents"])
    router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
    router.include_router(reports.router, prefix="/reports", tags=["reports"])
    router.include_router(history.router, prefix="/history", tags=["history"])


def setup_routes() -> None:
    """Настраивает роуты v1."""
    include_subrouters()

    @router.get("/health", status_code=200)
    async def health_check() -> dict[str, str]:
        """Проверка здоровья API."""
        return {"status": "ok", "message": "API v1 is running"}


# Настраиваем роуты при импорте
setup_routes()
