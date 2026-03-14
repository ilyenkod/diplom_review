"""
Реализация логгера для приложения.

Предоставляет удобный интерфейс для логирования с контекстом.
"""

import logging
from typing import Any


class AppLogger:
    """Логгер приложения с поддержкой контекста."""

    def __init__(self, name: str) -> None:
        """Инициализирует логгер.

        Args:
            name: Имя логгера.
        """
        self._logger = logging.getLogger(name)
        self._context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        """Устанавливает контекст для логирования.

        Args:
            **kwargs: Контекстные данные (user_id, request_id, и т.д.).
        """
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Очищает контекст логирования."""
        self._context.clear()

    def _add_context(self, extra: dict[str, Any] | None) -> dict[str, Any]:
        """Добавляет контекст к extra параметру.

        Args:
            extra: Дополнительные параметры для лога.

        Returns:
            Обновленный словарь extra.
        """
        if extra is None:
            extra = {}
        extra.update(self._context)
        return extra

    def debug(
        self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Логирует DEBUG сообщение.

        Args:
            msg: Сообщение.
            *args: Аргументы для форматирования сообщения.
            extra: Дополнительные параметры.
            **kwargs: Дополнительные параметры для логгера.
        """
        self._logger.debug(msg, *args, extra=self._add_context(extra), **kwargs)

    def info(
        self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Логирует INFO сообщение.

        Args:
            msg: Сообщение.
            *args: Аргументы для форматирования сообщения.
            extra: Дополнительные параметры.
            **kwargs: Дополнительные параметры для логгера.
        """
        self._logger.info(msg, *args, extra=self._add_context(extra), **kwargs)

    def warning(
        self, msg: str, *args: Any, extra: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Логирует WARNING сообщение.

        Args:
            msg: Сообщение.
            *args: Аргументы для форматирования сообщения.
            extra: Дополнительные параметры.
            **kwargs: Дополнительные параметры для логгера.
        """
        self._logger.warning(msg, *args, extra=self._add_context(extra), **kwargs)

    def error(
        self,
        msg: str,
        *args: Any,
        exc_info: bool | None = None,
        extra: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Логирует ERROR сообщение.

        Args:
            msg: Сообщение.
            *args: Аргументы для форматирования сообщения.
            exc_info: Информация об исключении.
            extra: Дополнительные параметры.
            **kwargs: Дополнительные параметры для логгера.
        """
        self._logger.error(msg, *args, exc_info=exc_info, extra=self._add_context(extra), **kwargs)

    def critical(
        self,
        msg: str,
        *args: Any,
        exc_info: bool | None = None,
        extra: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Логирует CRITICAL сообщение.

        Args:
            msg: Сообщение.
            *args: Аргументы для форматирования сообщения.
            exc_info: Информация об исключении.
            extra: Дополнительные параметры.
            **kwargs: Дополнительные параметры для логгера.
        """
        self._logger.critical(
            msg, *args, exc_info=exc_info, extra=self._add_context(extra), **kwargs
        )

    def exception(
        self,
        msg: str,
        *args: Any,
        extra: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Логирует EXCEPTION сообщение с информацией об исключении.

        Args:
            msg: Сообщение.
            *args: Аргументы для форматирования сообщения.
            extra: Дополнительные параметры.
            **kwargs: Дополнительные параметры для логгера.
        """
        self._logger.exception(msg, *args, extra=self._add_context(extra), **kwargs)


def get_logger(name: str) -> AppLogger:
    """Возвращает логгер приложения с указанным именем.

    Args:
        name: Имя логгера.

    Returns:
        Экземпляр AppLogger.
    """
    return AppLogger(name)
