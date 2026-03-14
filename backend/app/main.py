"""
Точка входа приложения.

Инициализирует FastAPI приложение:
- Создаёт и запускает все композиты через AppComposite
- Настраивает graceful shutdown
- Возвращает готовое FastAPI приложение для запуска через uvicorn
"""

import asyncio
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from composites.app_composite import AppComposite


# Глобальный композит приложения
app_composite: AppComposite | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Управление жизненным циклом приложения.

    Startup:
    - Инициализация всех компонентов (initialize)
    - Запуск подключений к внешним сервисам (start)

    Shutdown:
    - Корректное завершение работы компонентов (shutdown)
    """
    global app_composite

    try:
        # Startup phase
        # ====================

        # Создаём корневой композит приложения
        app_composite = AppComposite()

        # Инициализируем все компоненты (создание зависимостей)
        await app_composite.initialize()

        # Запускаем компоненты (подключение к внешним сервисам)
        await app_composite.start()

        # Получаем FastAPI приложение из API композита
        # (app_composite.api_composite.app обновит переданное приложение)
        if app_composite.api_composite and app_composite.api_composite.app:
            # Копируем состояние из созданного приложения
            app.routes = app_composite.api_composite.app.routes
            app.include_router = app_composite.api_composite.app.include_router
            app.middleware = app_composite.api_composite.app.middleware

        yield

    finally:
        # Shutdown phase
        # ====================

        if app_composite is not None:
            # Корректно завершаем работу всех компонентов
            await app_composite.shutdown()


# Создаём FastAPI приложение с lifespan manager
app = FastAPI(
    title="Diplom Review API",
    description="API для автоматизированной проверки дипломных работ с использованием ИИ",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


def create_app() -> FastAPI:
    """
    Фабричная функция для создания приложения.

    Используется для:
    - Тестирования
    - Запуска через uvicorn
    - Разных конфигураций окружения

    Returns:
        FastAPI: Настроенное приложение
    """
    return app


# Глобальные переменные для graceful shutdown через сигналы
_shutdown_event = asyncio.Event()


async def signal_handler() -> None:
    """Обработчик сигналов для graceful shutdown."""
    _shutdown_event.set()


def setup_signal_handlers() -> None:
    """Настраивает обработчики сигналов для graceful shutdown."""
    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(signal_handler()))
    except NotImplementedError:
        # Сигналы могут не поддерживаться в некоторых окружениях
        pass


async def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Запускает сервер с graceful shutdown.

    Args:
        host: Хост для прослушивания
        port: Порт для прослушивания
    """
    import uvicorn

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
    )

    server = uvicorn.Server(config)

    setup_signal_handlers()

    # Запускаем сервер и ждём сигнала завершения
    server_task = asyncio.create_task(server.serve())

    # Ждём сигнала shutdown
    await _shutdown_event.wait()

    # Graceful shutdown
    server.should_exit = True
    await server_task


if __name__ == "__main__":
    """
    Запуск приложения напрямую через python.

    Пример:
        python -m app.main

    Или для отладки:
        python -m app.main --host localhost --port 8000
    """
    import argparse

    parser = argparse.ArgumentParser(description="Запуск Diplom Review API")
    parser.add_argument("--host", default="0.0.0.0", help="Хост для прослушивания")
    parser.add_argument("--port", type=int, default=8000, help="Порт для прослушивания")

    args = parser.parse_args()

    try:
        asyncio.run(run_server(host=args.host, port=args.port))
    except KeyboardInterrupt:
        pass
