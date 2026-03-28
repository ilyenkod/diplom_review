"""
Конфигурация логирования приложения.

Определяет настройки для форматирования и обработчиков логов.
"""

import json
import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import get_settings


class StructuredFormatter(logging.Formatter):
    """Форматировщик для структурированного логирования в JSON формате."""

    def __init__(self) -> None:
        """Инициализирует форматировщик."""
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога.

        Args:
            record: Запись лога.

        Returns:
            Отформатированная JSON строка.
        """
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Добавляем дополнительные поля из extra
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "asctime",
                "user_id",
                "request_id",
            }:
                log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, default=self._json_serializer)

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Сериализатор для нестандартных типов.

        Args:
            obj: Объект для сериализации.

        Returns:
            Сериализованное значение.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} is not JSON serializable")


class ColoredFormatter(logging.Formatter):
    """Форматировщик с цветами для консольного вывода."""

    # ANSI color codes
    COLORS: dict[str, str] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self) -> None:
        """Инициализирует форматировщик."""
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        super().__init__(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога с цветами.

        Args:
            record: Запись лога.

        Returns:
            Отформатированная строка с цветами.
        """
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        formatted = super().format(record)
        record.levelname = levelname  # Restore original levelname
        return formatted


def get_log_level() -> int:
    """Возвращает уровень логирования из настроек.

    Returns:
        Уровень логирования (logging.DEBUG, logging.INFO, и т.д.).
    """
    level_name = get_settings().app.log_level.upper()
    return getattr(logging, level_name, logging.INFO)


def get_log_file_path() -> Path:
    """Возвращает путь к файлу логов.

    Returns:
        Путь к директории логов.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir / "app.log"


def get_logging_config() -> dict[str, Any]:
    """Возвращает конфигурацию логирования.

    Returns:
        Словарь конфигурации для logging.config.dictConfig.
    """
    log_level = get_log_level()
    log_file_path = get_log_file_path()

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "app.infrastructure.logging.config.ColoredFormatter",
            },
            "structured": {
                "()": "app.infrastructure.logging.config.StructuredFormatter",
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "structured",
                "filename": str(log_file_path),
                "maxBytes": 10 * 1024 * 1024,  # 10 MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "composites": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console", "file"],
                "level": logging.WARNING,
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"],
        },
    }


def configure_logging() -> None:
    """Настраивает логирование приложения."""
    logging_config = get_logging_config()
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с указанным именем.

    Args:
        name: Имя логгера.

    Returns:
        Экземпляр логгера.
    """
    return logging.getLogger(name)
