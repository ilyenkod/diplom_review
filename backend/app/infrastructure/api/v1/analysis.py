"""Эндпоинты анализа документов.

Будет реализовано в фазе 10.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Заглушка для проверки здоровья."""
    return {"status": "ok", "message": "Analysis router (stub)"}
