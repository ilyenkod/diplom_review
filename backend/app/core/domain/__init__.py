"""
Domain сущности приложения.

Содержит бизнес-логику предметной области, не зависящую от способа хранения.
"""

from .analysis import Analysis, AnalysisStatus
from .document import Document, FileType
from .history import History
from .report import Report
from .user import User, UserRole

__all__ = [
    # Сущности
    "User",
    "Document",
    "Analysis",
    "Report",
    "History",
    # Enums
    "UserRole",
    "FileType",
    "AnalysisStatus",
]
