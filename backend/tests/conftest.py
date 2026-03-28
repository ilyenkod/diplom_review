"""
Конфигурация для тестов.

Настраивает pytest и предоставляет фикстуры для тестов.
"""

import os
import sys
from pathlib import Path

# Set up environment variables for testing BEFORE importing app modules
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_OPENAI_API_KEY", "test-key-for-testing")
os.environ.setdefault("LLM_ANTHROPIC_API_KEY", "test-key-for-testing")
os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

# Add backend to path if needed
backend_path = Path(__file__).parent.parent / "app"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def logger():
    """Возвращает логгер для тестов."""
    from app.infrastructure.logging import get_logger

    return get_logger("test")
