"""Эндпоинты документов.

Будет реализовано в фазе 8.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Заглушка для проверки здоровья."""
    return {"status": "ok", "message": "Documents router (stub)"}
