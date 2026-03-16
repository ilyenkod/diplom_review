"""Эндпоинты отчетов.

Будет реализовано в фазе 10.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Заглушка для проверки здоровья."""
    return {"status": "ok", "message": "Reports router (stub)"}
