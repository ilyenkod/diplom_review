"""
Domain сущности приложения.

Содержит бизнес-логику предметной области, не зависящую от способа хранения.
"""

from .user import User, UserRole
from .document import Document, FileType
from .analysis import Analysis, AnalysisStatus
from .report import Report
from .history import History

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
