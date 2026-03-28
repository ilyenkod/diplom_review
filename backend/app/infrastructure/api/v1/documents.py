"""Эндпоинты документов.

Предоставляет API для загрузки, получения, списка и удаления документов.
"""

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import Document
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    FileSizeExceededError,
    InvalidFileTypeError,
)
from app.core.services.document_service import DocumentService
from app.infrastructure.api.deps import get_current_user, get_db
from app.infrastructure.api.deps_composites import (
    get_logger,
    get_processors,
    get_storage,
)
from app.infrastructure.api.schemas.document import DocumentListResponse, DocumentResponse

if TYPE_CHECKING:
    from app.core.domain import User

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(
    db: AsyncSession = Depends(get_db),
    storage: Any = Depends(get_storage),
    processors: dict[str, Any] = Depends(get_processors),
) -> DocumentService:
    """Возвращает сервис документов.

    Args:
        db: Сессия базы данных.
        storage: Хранилище файлов.
        processors: Словарь процессоров.

    Returns:
        Экземпляр DocumentService.
    """
    from app.infrastructure.database.repositories.document_repo import DocumentRepository

    logger_value = get_logger("api.v1.documents")
    document_repo = DocumentRepository(db)
    return DocumentService(document_repo, storage, logger_value, processors)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузка документа",
    description="Загружает новый документ и извлекает из него текст.",
)
async def upload_document(
    file: UploadFile = File(..., description="Файл документа (docx, pdf, txt)"),
    current_user: "User" = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    """Загружает документ и извлекает текст.

    Args:
        file: Загружаемый файл.
        current_user: Текущий пользователь.
        document_service: Сервис документов.

    Returns:
        Созданный документ.

    Raises:
        HTTPException: Если неверный тип файла или превышен размер файла.
    """
    # Читаем содержимое файла
    content = await file.read()
    file_size = len(content)

    # Получаем тип файла из расширения
    original_filename = file.filename or "unknown"
    extension = original_filename.lower().split(".")[-1] if "." in original_filename else ""

    try:
        document = await document_service.upload_document(
            user_id=current_user.id,
            filename=original_filename,
            original_filename=original_filename,
            file_size=file_size,
            file_type=extension,
            content=content,
        )
        get_logger("api.v1.documents").info(
            "Document uploaded successfully",
            extra={
                "document_id": document.id,
                "user_id": current_user.id,
                "filename": original_filename,
                "file_size": file_size,
            },
        )
        return document
    except InvalidFileTypeError as e:
        get_logger("api.v1.documents").warning(
            "Document upload failed: invalid file type",
            extra={
                "user_id": current_user.id,
                "filename": original_filename,
                "extension": extension,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except FileSizeExceededError as e:
        get_logger("api.v1.documents").warning(
            "Document upload failed: file size exceeded",
            extra={
                "user_id": current_user.id,
                "filename": original_filename,
                "file_size": file_size,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        ) from e
    except DocumentProcessingError as e:
        get_logger("api.v1.documents").error(
            "Document upload failed: processing error",
            extra={
                "user_id": current_user.id,
                "filename": original_filename,
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Получение документа",
    description="Возвращает документ по ID.",
)
async def get_document(
    document_id: str,
    current_user: "User" = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    """Получает документ по ID.

    Args:
        document_id: ID документа.
        current_user: Текущий пользователь.
        document_service: Сервис документов.

    Returns:
        Документ.

    Raises:
        HTTPException: Если документ не найден.
    """
    document = await document_service.get_document(document_id)

    if document is None:
        get_logger("api.v1.documents").warning(
            "Document not found",
            extra={"document_id": document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Проверяем, что документ принадлежит пользователю
    if document.user_id != current_user.id:
        get_logger("api.v1.documents").warning(
            "User attempted to access document from another user",
            extra={"document_id": document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return document


@router.get(
    "/",
    response_model=list[DocumentListResponse],
    summary="Список документов пользователя",
    description="Возвращает список документов текущего пользователя.",
)
async def list_documents(
    limit: int = 100,
    offset: int = 0,
    current_user: "User" = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> list[Document]:
    """Получает список документов пользователя.

    Args:
        limit: Максимальное количество документов.
        offset: Смещение.
        current_user: Текущий пользователь.
        document_service: Сервис документов.

    Returns:
        Список документов.
    """
    # Валидируем лимиты
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    if offset < 0:
        offset = 0

    documents = await document_service.get_user_documents(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )

    get_logger("api.v1.documents").info(
        "Documents listed",
        extra={"user_id": current_user.id, "count": len(documents)},
    )

    return documents


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление документа",
    description="Удаляет документ по ID.",
)
async def delete_document(
    document_id: str,
    current_user: "User" = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> None:
    """Удаляет документ по ID.

    Args:
        document_id: ID документа.
        current_user: Текущий пользователь.
        document_service: Сервис документов.

    Raises:
        HTTPException: Если документ не найден или недоступен.
    """
    try:
        result = await document_service.delete_document(
            document_id=document_id,
            user_id=current_user.id,
        )

        if not result:
            get_logger("api.v1.documents").warning(
                "Document not found for deletion",
                extra={"document_id": document_id, "user_id": current_user.id},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )

        get_logger("api.v1.documents").info(
            "Document deleted successfully",
            extra={"document_id": document_id, "user_id": current_user.id},
        )
    except DocumentNotFoundError as e:
        get_logger("api.v1.documents").warning(
            "Document not found for deletion",
            extra={"document_id": document_id, "user_id": current_user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
