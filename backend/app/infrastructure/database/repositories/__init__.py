"""
Репозитории базы данных.

Экспортирует все репозитории для работы c базой данных.
"""

from .analysis_repo import AnalysisRepository
from .base import BaseRepository
from .document_repo import DocumentRepository
from .history_repo import HistoryRepository
from .report_repo import ReportRepository
from .user_repo import UserRepository

__all__ = [
    "AnalysisRepository",
    "BaseRepository",
    "DocumentRepository",
    "HistoryRepository",
    "ReportRepository",
    "UserRepository",
]
