"""Middleware для FastAPI."""

from app.infrastructure.middleware.cors import setup_cors
from app.infrastructure.middleware.request_logging import setup_request_logging

__all__ = ["setup_cors", "setup_request_logging"]
