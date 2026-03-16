"""Эндпоинты аутентификации.

Будет реализовано в фазе 8.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Заглушка для проверки здоровья."""
    return {"status": "ok", "message": "Auth router (stub)"}
