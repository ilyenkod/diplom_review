"""
S3 хранилище файлов.

Реализует интерфейс S3Storage для работы с S3 совместимым хранилищем.
"""

import asyncio
from datetime import datetime
from io import BytesIO
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings
from app.core.interfaces.storage import FileMetadata, S3Storage, StorageResult
from app.infrastructure.logging import AppLogger


class S3StorageImpl(S3Storage):
    """Реализация S3 хранилища."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует S3 хранилище.

        Args:
            logger: Логгер приложения.
        """
        self._logger = logger
        self._bucket_name = settings.storage.s3_bucket_name
        self._region = settings.storage.s3_region

        # Инициализация S3 клиента
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.storage.s3_endpoint_url,
            aws_access_key_id=settings.storage.s3_access_key,
            aws_secret_access_key=settings.storage.s3_secret_key,
            region_name=self._region,
            config=Config(signature_version="s3v4"),
        )

        self._logger.info(
            "S3 storage initialized",
            extra={
                "bucket": self._bucket_name,
                "region": self._region,
                "endpoint": settings.storage.s3_endpoint_url,
            },
        )

    async def save(
        self,
        key: str,
        content: bytes | BytesIO,
        content_type: str,
    ) -> StorageResult:
        """Сохраняет файл по ключу.

        Args:
            key: Ключ файла.
            content: Содержимое файла.
            content_type: MIME тип.

        Returns:
            Результат сохранения.
        """
        try:
            await asyncio.to_thread(
                self._save_sync,
                key,
                content,
                content_type,
            )

            metadata = FileMetadata(
                filename=key.split("/")[-1],
                size=len(content) if isinstance(content, bytes) else content.getbuffer().nbytes,
                content_type=content_type,
                created_at=datetime.now(),
                storage_type="s3",
                storage_key=key,
            )

            self._logger.info(
                "File saved to S3",
                extra={"key": key, "size": metadata.size, "content_type": content_type},
            )

            return StorageResult(
                success=True,
                key=key,
                metadata=metadata,
            )

        except Exception as e:
            self._logger.error(
                "Failed to save file to S3",
                extra={"key": key, "error": str(e)},
            )
            return StorageResult(
                success=False,
                key=key,
                metadata=FileMetadata(
                    filename=key.split("/")[-1],
                    size=0,
                    content_type=content_type,
                    created_at=datetime.now(),
                    storage_type="s3",
                ),
                error=str(e),
            )

    def _save_sync(
        self,
        key: str,
        content: bytes | BytesIO,
        content_type: str,
    ) -> None:
        """Синхронное сохранение файла.

        Args:
            key: Ключ файла.
            content: Содержимое файла.
            content_type: MIME тип.
        """
        if isinstance(content, bytes):
            content_bytes = BytesIO(content)
        else:
            content_bytes = content
            content_bytes.seek(0)

        self._client.upload_fileobj(
            content_bytes,
            self._bucket_name,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    async def get(self, key: str) -> bytes | None:
        """Загружает файл по ключу.

        Args:
            key: Ключ файла.

        Returns:
            Содержимое файла или None если файл не найден.
        """
        try:
            return await asyncio.to_thread(self._get_sync, key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            self._logger.error("Failed to get file from S3", extra={"key": key, "error": str(e)})
            return None

    def _get_sync(self, key: str) -> bytes:
        """Синхронное получение файла.

        Args:
            key: Ключ файла.

        Returns:
            Содержимое файла.
        """
        response = self._client.get_object(Bucket=self._bucket_name, Key=key)
        return response["Body"].read()  # type: ignore[no-any-return]

    async def delete(self, key: str) -> bool:
        """Удаляет файл по ключу.

        Args:
            key: Ключ файла.

        Returns:
            True если файл был удален, иначе False.
        """
        try:
            await asyncio.to_thread(self._delete_sync, key)
            self._logger.info("File deleted from S3", extra={"key": key})
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            self._logger.error("Failed to delete file from S3", extra={"key": key, "error": str(e)})
            return False

    def _delete_sync(self, key: str) -> None:
        """Синхронное удаление файла.

        Args:
            key: Ключ файла.
        """
        self._client.delete_object(Bucket=self._bucket_name, Key=key)

    async def exists(self, key: str) -> bool:
        """Проверяет существование файла.

        Args:
            key: Ключ файла.

        Returns:
            True если файл существует, иначе False.
        """
        try:
            await asyncio.to_thread(self._exists_sync, key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            self._logger.error(
                "Failed to check file existence in S3",
                extra={"key": key, "error": str(e)},
            )
            return False

    def _exists_sync(self, key: str) -> None:
        """Синхронная проверка существования файла.

        Args:
            key: Ключ файла.

        Raises:
            ClientError: Если файл не существует.
        """
        self._client.head_object(Bucket=self._bucket_name, Key=key)

    async def get_metadata(self, key: str) -> FileMetadata | None:
        """Возвращает метаданные файла.

        Args:
            key: Ключ файла.

        Returns:
            Метаданные файла или None если файл не найден.
        """
        try:
            return await asyncio.to_thread(self._get_metadata_sync, key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            self._logger.error(
                "Failed to get file metadata from S3",
                extra={"key": key, "error": str(e)},
            )
            return None

    def _get_metadata_sync(self, key: str) -> FileMetadata:
        """Синхронное получение метаданных.

        Args:
            key: Ключ файла.

        Returns:
            Метаданные файла.
        """
        response = self._client.head_object(Bucket=self._bucket_name, Key=key)
        last_modified = response.get("LastModified")

        return FileMetadata(
            filename=key.split("/")[-1],
            size=response.get("ContentLength", 0),
            content_type=response.get("ContentType", "application/octet-stream"),
            created_at=last_modified or datetime.now(),
            updated_at=last_modified,
            storage_type="s3",
            storage_key=key,
        )

    async def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """Возвращает URL для доступа к файлу.

        Args:
            key: Ключ файла.
            expires_in: Время жизни URL в секундах.

        Returns:
            Presigned URL или None в случае ошибки.
        """
        return await self.generate_presigned_url(key, expires_in=expires_in, method="get_object")

    async def list_files(self, prefix: str = "") -> list[str]:
        """Возвращает список файлов по префиксу.

        Args:
            prefix: Префикс для поиска.

        Returns:
            Список ключей файлов.
        """
        try:
            return await asyncio.to_thread(self._list_files_sync, prefix)
        except Exception as e:
            self._logger.error(
                "Failed to list files in S3",
                extra={"prefix": prefix, "error": str(e)},
            )
            return []

    def _list_files_sync(self, prefix: str) -> list[str]:
        """Синхронное получение списка файлов.

        Args:
            prefix: Префикс для поиска.

        Returns:
            Список ключей файлов.
        """
        response = self._client.list_objects_v2(
            Bucket=self._bucket_name,
            Prefix=prefix,
        )
        contents = response.get("Contents", [])
        return [obj["Key"] for obj in contents if "Key" in obj]

    async def copy(self, source_key: str, dest_key: str) -> bool:
        """Копирует файл.

        Args:
            source_key: Исходный ключ.
            dest_key: Ключ назначения.

        Returns:
            True если успешно, иначе False.
        """
        try:
            await asyncio.to_thread(
                self._copy_sync,
                source_key,
                dest_key,
            )
            self._logger.info(
                "File copied in S3",
                extra={"source": source_key, "dest": dest_key},
            )
            return True
        except Exception as e:
            self._logger.error(
                "Failed to copy file in S3",
                extra={"source": source_key, "dest": dest_key, "error": str(e)},
            )
            return False

    def _copy_sync(self, source_key: str, dest_key: str) -> None:
        """Синхронное копирование файла.

        Args:
            source_key: Исходный ключ.
            dest_key: Ключ назначения.
        """
        self._client.copy_object(
            CopySource={"Bucket": self._bucket_name, "Key": source_key},
            Bucket=self._bucket_name,
            Key=dest_key,
        )

    async def move(self, source_key: str, dest_key: str) -> bool:
        """Перемещает файл.

        Args:
            source_key: Исходный ключ.
            dest_key: Ключ назначения.

        Returns:
            True если успешно, иначе False.
        """
        try:
            if await self.copy(source_key, dest_key):
                await self.delete(source_key)
                self._logger.info(
                    "File moved in S3",
                    extra={"source": source_key, "dest": dest_key},
                )
                return True
            return False
        except Exception as e:
            self._logger.error(
                "Failed to move file in S3",
                extra={"source": source_key, "dest": dest_key, "error": str(e)},
            )
            return False

    async def clear(self) -> bool:
        """Очищает хранилище.

        Returns:
            True если успешно, иначе False.
        """
        try:
            all_files = await self.list_files()
            for key in all_files:
                await self.delete(key)
            self._logger.info("S3 storage cleared", extra={"files_deleted": len(all_files)})
            return True
        except Exception as e:
            self._logger.error("Failed to clear S3 storage", extra={"error": str(e)})
            return False

    async def upload_fileobj(
        self,
        key: str,
        file_obj: BytesIO,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> StorageResult:
        """Загружает файловый объект в S3.

        Args:
            key: Ключ файла.
            file_obj: Файловый объект.
            content_type: MIME тип.
            metadata: Дополнительные метаданные.

        Returns:
            Результат загрузки.
        """
        try:
            await asyncio.to_thread(
                self._upload_fileobj_sync,
                key,
                file_obj,
                content_type,
                metadata,
            )

            file_metadata = FileMetadata(
                filename=key.split("/")[-1],
                size=file_obj.getbuffer().nbytes,
                content_type=content_type,
                created_at=datetime.now(),
                storage_type="s3",
                storage_key=key,
            )

            self._logger.info(
                "File object uploaded to S3",
                extra={
                    "key": key,
                    "size": file_metadata.size,
                    "content_type": content_type,
                },
            )

            return StorageResult(
                success=True,
                key=key,
                metadata=file_metadata,
            )

        except Exception as e:
            self._logger.error(
                "Failed to upload file object to S3",
                extra={"key": key, "error": str(e)},
            )
            return StorageResult(
                success=False,
                key=key,
                metadata=FileMetadata(
                    filename=key.split("/")[-1],
                    size=0,
                    content_type=content_type,
                    created_at=datetime.now(),
                    storage_type="s3",
                ),
                error=str(e),
            )

    def _upload_fileobj_sync(
        self,
        key: str,
        file_obj: BytesIO,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Синхронная загрузка файлового объекта.

        Args:
            key: Ключ файла.
            file_obj: Файловый объект.
            content_type: MIME тип.
            metadata: Дополнительные метаданные.
        """
        file_obj.seek(0)
        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}  # type: ignore[assignment]

        self._client.upload_fileobj(
            file_obj,
            self._bucket_name,
            key,
            ExtraArgs=extra_args,
        )

    async def download_fileobj(self, key: str) -> BytesIO | None:
        """Загружает файловый объект из S3.

        Args:
            key: Ключ файла.

        Returns:
            Файловый объект или None если файл не найден.
        """
        try:
            return await asyncio.to_thread(self._download_fileobj_sync, key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            self._logger.error(
                "Failed to download file object from S3",
                extra={"key": key, "error": str(e)},
            )
            return None

    def _download_fileobj_sync(self, key: str) -> BytesIO:
        """Синхронная загрузка файлового объекта.

        Args:
            key: Ключ файла.

        Returns:
            Файловый объект.
        """
        file_obj = BytesIO()
        self._client.download_fileobj(self._bucket_name, key, file_obj)
        file_obj.seek(0)
        return file_obj

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str | None:
        """Генерирует presigned URL для доступа к файлу.

        Args:
            key: Ключ файла.
            expires_in: Время жизни URL в секундах.
            method: Метод (get_object, put_object, etc.).

        Returns:
            Presigned URL или None в случае ошибки.
        """
        try:
            return await asyncio.to_thread(
                self._generate_presigned_url_sync,
                key,
                expires_in,
                method,
            )
        except Exception as e:
            self._logger.error(
                "Failed to generate presigned URL",
                extra={"key": key, "error": str(e)},
            )
            return None

    def _generate_presigned_url_sync(
        self,
        key: str,
        expires_in: int,
        method: str,
    ) -> str:
        """Синхронная генерация presigned URL.

        Args:
            key: Ключ файла.
            expires_in: Время жизни URL в секундах.
            method: Метод (get_object, put_object, etc.).

        Returns:
            Presigned URL.
        """
        return self._client.generate_presigned_url(  # type: ignore[no-any-return]
            ClientMethod=method,
            Params={"Bucket": self._bucket_name, "Key": key},
            ExpiresIn=expires_in,
        )

    async def head_object(self, key: str) -> dict[str, Any] | None:
        """Получает метаданные объекта без загрузки содержимого.

        Args:
            key: Ключ файла.

        Returns:
            Словарь метаданных или None если файл не найден.
        """
        try:
            return await asyncio.to_thread(self._head_object_sync, key)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            self._logger.error(
                "Failed to head object in S3",
                extra={"key": key, "error": str(e)},
            )
            return None

    def _head_object_sync(self, key: str) -> dict[str, Any]:
        """Синхронное получение метаданных объекта.

        Args:
            key: Ключ файла.

        Returns:
            Словарь метаданных.
        """
        response = self._client.head_object(Bucket=self._bucket_name, Key=key)
        return dict(response)

    def get_bucket_name(self) -> str:
        """Возвращает имя бакета.

        Returns:
            Имя бакета.
        """
        return self._bucket_name

    def get_region(self) -> str:
        """Возвращает регион.

        Returns:
            Регион.
        """
        return self._region
