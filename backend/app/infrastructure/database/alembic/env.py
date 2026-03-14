"""
Конфигурация Alembic для миграций базы данных.

Этот модуль настраивает окружение Alembic и предоставляет
контекст выполнения миграций.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Импортируем Base и таблицы (mapper регистрируется автоматически при импорте)
from app.infrastructure.database.table import Base

# Импортируем конфигурацию приложения (будет создана позже)
# from app.config import settings

# ============================================================
# Настройка логирования
# ============================================================
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ============================================================
# Метаданные для автоматической генерации миграций
# ============================================================
target_metadata = Base.metadata


# ============================================================
# Функция для получения URL базы данных
# ============================================================
def get_database_url() -> str:
    """
    Возвращает URL для подключения к базе данных.

    Приоритет:
    1. Переменная окружения DATABASE_URL
    2. Значение из секции sqlalchemy в alembic.ini
    3. Default значение для разработки
    """
    import os

    # Получаем URL из переменной окружения или из конфигурации Alembic
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # Значение из alembic.ini
    return config.get_main_option("sqlalchemy.url")


# ============================================================
# Функция run_migrations_offline
# ============================================================
def run_migrations_offline() -> None:
    """
    Запускает миграции в 'offline' режиме.

    В этом режиме не требуется подключение к базе данных.
    Миграции генерируются как SQL скрипт.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# Функция do_run_migrations (для async режима)
# ============================================================
def do_run_migrations(connection: Connection) -> None:
    """Выполняет миграции с использованием заданного соединения."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# Функция run_migrations_online
# ============================================================
async def run_async_migrations() -> None:
    """
    Запускает миграции в 'online' режиме (async).

    В этом режиме требуется подключение к базе данных.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# ============================================================
# Точка входа для запуска миграций
# ============================================================
def run_migrations_online() -> None:
    """Запускает миграции в синхронном режиме."""
    run_migrations_offline()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
