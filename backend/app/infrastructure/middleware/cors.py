"""CORS middleware для FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI, allow_origins: list[str] | None = None) -> None:
    """Настраивает CORS для приложения.

    Args:
        app: Экземпляр FastAPI.
        allow_origins: Список разрешенных origins. None разрешает все в development.
    """
    if allow_origins is None:
        # В development разрешаем все origins  # noqa: RUF003
        allow_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Length", "Content-Range"],
        max_age=600,
    )
