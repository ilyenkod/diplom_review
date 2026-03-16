"""Эндпоинты истории версий.

Будет реализовано в фазе 10.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Заглушка для проверки здоровья."""
    return {"status": "ok", "message": "History router (stub)"}
