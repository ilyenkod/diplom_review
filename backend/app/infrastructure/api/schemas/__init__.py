"""Pydantic схемы для API."""

from app.infrastructure.api.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisReanalyzeRequest,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusEnum,
    AnalysisStatusResponse,
)
from app.infrastructure.api.schemas.common import (
    ErrorResponse,
    HealthCheckResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    SuccessResponse,
    ValidationErrorDetail,
    ValidationErrorResponse,
)
from app.infrastructure.api.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdate,
    DocumentUpload,
    FileTypeEnum,
)
from app.infrastructure.api.schemas.history import (
    HistoryDetail,
    HistoryItem,
    HistoryListResponse,
    VersionComparison,
    VersionComparisonRequest,
    VersionListResponse,
)
from app.infrastructure.api.schemas.report import (
    AssessmentLevel,
    OverallAssessment,
    ReportDetailResponse,
    ReportDownloadResponse,
    ReportGenerateRequest,
    ReportResponse,
)
from app.infrastructure.api.schemas.user import (
    LoginRequest,
    RegisterRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserRoleEnum,
    UserUpdate,
)

__all__ = [  # noqa: RUF022
    # Common
    "ErrorResponse",
    "HealthCheckResponse",
    "PaginationMeta",
    "PaginationParams",
    "PaginatedResponse",
    "SuccessResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    # User
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "TokenResponse",
    "TokenRefreshRequest",
    "LoginRequest",
    "RegisterRequest",
    "UserRoleEnum",
    # Document
    "DocumentUpload",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentUpdate",
    "FileTypeEnum",
    # Analysis
    "AnalysisRequest",
    "AnalysisResponse",
    "AnalysisDetailResponse",
    "AnalysisStatusResponse",
    "AnalysisReanalyzeRequest",
    "AnalysisStatusEnum",
    # Report
    "ReportResponse",
    "ReportDetailResponse",
    "ReportGenerateRequest",
    "ReportDownloadResponse",
    "OverallAssessment",
    "AssessmentLevel",
    # History
    "HistoryItem",
    "HistoryDetail",
    "VersionComparison",
    "VersionComparisonRequest",
    "HistoryListResponse",
    "VersionListResponse",
]
