"""
Базовый композит для композиции зависимостей.

Определяет интерфейс для инициализации, запуска и остановки компонентов.
Следует паттерну Composition Root.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseComposite(ABC):
    """Базовый класс композита для управления жизненным циклом компонентов."""

    _initialized: bool = False
    _started: bool = False
    _dependencies: dict[str, Any]

    def __init__(self) -> None:
        """Инициализирует композит."""
        self._dependencies = {}

    @abstractmethod
    async def initialize(self) -> None:
        """Инициализирует зависимости композита."""
        raise NotImplementedError

    @abstractmethod
    async def start(self) -> None:
        """Запускает компоненты композита."""
        raise NotImplementedError

    @abstractmethod
    async def shutdown(self) -> None:
        """Корректно останавливает компоненты композита."""
        raise NotImplementedError

    @property
    def dependencies(self) -> dict[str, Any]:
        """Возвращает словарь зависимостей композита."""
        return self._dependencies

    def get_dependency(self, name: str) -> Any:
        """Возвращает зависимость по имени.

        Args:
            name: Имя зависимости.

        Returns:
            Зависимость.

        Raises:
            KeyError: Если зависимость не найдена.
        """
        return self._dependencies[name]

    def set_dependency(self, name: str, dependency: Any) -> None:
        """Устанавливает зависимость по имени.

        Args:
            name: Имя зависимости.
            dependency: Зависимость для установки.
        """
        self._dependencies[name] = dependency

    def has_dependency(self, name: str) -> bool:
        """Проверяет наличие зависимости.

        Args:
            name: Имя зависимости.

        Returns:
            True если зависимость существует, иначе False.
        """
        return name in self._dependencies

    @property
    def initialized(self) -> bool:
        """Возвращает True если композит инициализирован."""
        return self._initialized

    @property
    def started(self) -> bool:
        """Возвращает True если композит запущен."""
        return self._started

    async def _ensure_initialized(self) -> None:
        """Убеждается, что композит инициализирован."""
        if not self._initialized:
            msg = f"{self.__class__.__name__} is not initialized"
            raise RuntimeError(msg)

    async def _ensure_started(self) -> None:
        """Убеждается, что композит запущен."""
        if not self._started:
            msg = f"{self.__class__.__name__} is not started"
            raise RuntimeError(msg)

    async def __aenter__(self) -> "BaseComposite":
        """Вход в контекстный менеджер."""
        await self.initialize()
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Выход из контекстного менеджера."""
        await self.shutdown()


class CompositeDependencyError(RuntimeError):
    """Ошибка зависимостей композита."""

    pass
