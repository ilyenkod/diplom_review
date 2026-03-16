"""
Базовый репозиторий c общими CRUD операциями.

Реализует базовый интерфейс репозитория для работы c SQLAlchemy Core.
"""

from typing import Any, Generic, TypeVar, cast

from sqlalchemy import Select, Table, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import class_mapper

from app.core.interfaces.database import BaseRepository as BaseRepositoryInterface

T = TypeVar("T")


class BaseRepository(BaseRepositoryInterface[T], Generic[T]):  # noqa: UP046, type: ignore[type-var]
    """Базовый репозиторий c общими CRUD операциями."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        """Инициализирует репозиторий.

        Args:
            session: Сессия базы данных.
            model: Класс модели SQLAlchemy Core.
        """
        self._session = session
        self._model = model

    @property
    def _table(self) -> Table:
        """Возвращает таблицу модели."""
        mapper = class_mapper(self._model)
        return cast(Table, mapper.persist_selectable)

    async def create(self, entity: T) -> T:
        """Создает новую сущность.

        Args:
            entity: Сущность для создания.

        Returns:
            Созданная сущность.
        """
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def get_by_id(self, entity_id: str) -> T | None:
        """Возвращает сущность по ID.

        Args:
            entity_id: Идентификатор сущности.

        Returns:
            Сущность или None если не найдена.
        """
        stmt = select(self._model).where(self._table.c.id == entity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Возвращает список сущностей c пагинацией.

        Args:
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список сущностей.
        """
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, entity: T) -> T:
        """Обновляет существующую сущность.

        Args:
            entity: Сущность для обновления.

        Returns:
            Обновленная сущность.
        """
        entity_dict = {
            k: v for k, v in entity.__dict__.items() if not k.startswith("_") and not callable(v)
        }
        entity_id = entity_dict.pop("id", None)
        if entity_id:
            await self._session.execute(
                update(self._table).where(self._table.c.id == entity_id).values(**entity_dict)
            )
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        """Удаляет сущность по ID.

        Args:
            entity_id: Идентификатор сущности.

        Returns:
            True если удалено, False если не найдено.
        """
        from sqlalchemy.engine import CursorResult

        stmt = delete(self._table).where(self._table.c.id == entity_id)
        result = await self._session.execute(stmt)
        await self._session.flush()
        result_cast = cast(CursorResult[Any], result)
        return result_cast.rowcount > 0

    async def exists(self, entity_id: str) -> bool:
        """Проверяет существование сущности по ID.

        Args:
            entity_id: Идентификатор сущности.

        Returns:
            True если сущность существует.
        """
        stmt = select(func.count()).select_from(self._table).where(self._table.c.id == entity_id)
        result = await self._session.execute(stmt)
        count = result.scalar()
        return (count or 0) > 0

    async def count(self) -> int:
        """Возвращает количество сущностей.

        Returns:
            Количество сущностей.
        """
        stmt = select(func.count()).select_from(self._table)
        result = await self._session.execute(stmt)
        count = result.scalar()
        return count or 0

    def _build_base_query(self) -> Select[tuple[T]]:
        """Создает базовый запрос.

        Returns:
            Базовый SELECT запрос.
        """
        return select(self._model)

    def _apply_pagination(
        self, stmt: Select[tuple[T]], limit: int, offset: int
    ) -> Select[tuple[T]]:
        """Применяет пагинацию к запросу.

        Args:
            stmt: Запрос SQLAlchemy.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Запрос c пагинацией.
        """
        return stmt.limit(limit).offset(offset)

    def _apply_order_by(
        self, stmt: Select[tuple[T]], column: str, desc: bool = False
    ) -> Select[tuple[T]]:
        """Применяет сортировку к запросу.

        Args:
            stmt: Запрос SQLAlchemy.
            column: Имя колонки для сортировки.
            desc: Сортировать по убыванию.

        Returns:
            Запрос c сортировкой.
        """
        col = self._table.c[column]
        return stmt.order_by(col.desc() if desc else col)
