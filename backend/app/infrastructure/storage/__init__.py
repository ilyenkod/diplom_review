"""Storage infrastructure."""

from app.infrastructure.storage.local_storage import FileSystemStorage
from app.infrastructure.storage.s3_storage import S3StorageImpl

__all__ = ["FileSystemStorage", "S3StorageImpl"]
