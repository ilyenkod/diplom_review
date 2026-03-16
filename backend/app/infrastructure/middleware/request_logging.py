"""Request logging middleware для FastAPI."""

import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования запросов и ответов."""

    def __init__(self, app: FastAPI) -> None:
        """Инициализирует middleware.

        Args:
            app: Экземпляр FastAPI.
        """
        super().__init__(app)
        from app.infrastructure.logging import get_logger

        self._logger = get_logger("api.request")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос и логирует его.

        Args:
            request: Запрос.
            call_next: Следующий middleware или endpoint.

        Returns:
            Ответ.
        """
        # Генерируем request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Запоминаем время начала
        start_time = time.time()

        # Логируем запрос
        self._logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
                "client_host": request.client.host if request.client else None,
            },
        )

        # Вызываем следующий middleware или endpoint
        try:
            response = await call_next(request)
        except Exception as e:
            # Логируем ошибку
            duration = time.time() - start_time
            self._logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration * 1000, 2),
                    "error_type": type(e).__name__,
                },
            )
            raise

        # Вычисляем длительность
        duration = time.time() - start_time

        # Добавляем request ID в заголовки ответа
        response.headers["X-Request-ID"] = request_id

        # Логируем ответ
        self._logger.info(
            f"Request completed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        return response


def setup_request_logging(app: FastAPI) -> None:
    """Настраивает логирование запросов для приложения.

    Args:
        app: Экземпляр FastAPI.
    """
    app.add_middleware(RequestLoggingMiddleware)
