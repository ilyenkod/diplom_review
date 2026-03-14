"""
Initial schema migration.

Создает все необходимые таблицы для системы проверки дипломных работ:
- users: пользователи системы
- documents: загруженные документы
- analyses: результаты анализа
- reports: сгенерированные отчеты
- history: история версий документов
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================
    # Таблица users
    # ============================================================
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.String(),
            nullable=False,
            comment="Уникальный идентификатор пользователя (UUID)",
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
            comment="Email пользователя (уникальный)",
        ),
        sa.Column(
            "hashed_password", sa.String(length=255), nullable=False, comment="Хешированный пароль"
        ),
        sa.Column(
            "full_name", sa.String(length=255), nullable=False, comment="Полное имя пользователя"
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, comment="Флаг активности пользователя"
        ),
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
            comment="Роль пользователя (student, admin, supervisor)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Время создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Время последнего обновления",
        ),
        sa.CheckConstraint("role IN ('student', 'admin', 'supervisor')", name="check_user_role"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        comment="Пользователи системы (студенты, админы, руководители)",
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # ============================================================
    # Таблица documents
    # ============================================================
    op.create_table(
        "documents",
        sa.Column(
            "id", sa.String(), nullable=False, comment="Уникальный идентификатор документа (UUID)"
        ),
        sa.Column("user_id", sa.String(), nullable=False, comment="ID владельца документа"),
        sa.Column(
            "filename",
            sa.String(length=255),
            nullable=False,
            comment="Сгенерированное имя файла (UUID-based)",
        ),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False,
            comment="Оригинальное имя файла при загрузке",
        ),
        sa.Column(
            "file_path",
            sa.String(length=500),
            nullable=True,
            comment="Путь к файлу в локальном хранилище",
        ),
        sa.Column(
            "s3_key", sa.String(length=500), nullable=True, comment="Ключ объекта в S3 хранилище"
        ),
        sa.Column("file_size", sa.BigInteger(), nullable=False, comment="Размер файла в байтах"),
        sa.Column(
            "file_type", sa.String(length=10), nullable=False, comment="Тип файла (docx, pdf, txt)"
        ),
        sa.Column("content", sa.Text(), nullable=True, comment="Извлеченный текст из документа"),
        sa.Column(
            "metadata",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Дополнительные метаданные",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Время создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Время последнего обновления",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "(file_path IS NOT NULL AND s3_key IS NULL) OR (file_path IS NULL AND s3_key IS NOT NULL)",
            name="document_storage_constraint",
        ),
        sa.CheckConstraint("file_type IN ('docx', 'pdf', 'txt')", name="check_document_file_type"),
        sa.PrimaryKeyConstraint("id"),
        comment="Загруженные дипломные работы",
    )
    op.create_index("idx_documents_user_id", "documents", ["user_id"])
    op.create_index("idx_documents_file_type", "documents", ["file_type"])
    op.create_index("idx_documents_created_at", "documents", [sa.text("created_at DESC")])

    # ============================================================
    # Таблица analyses
    # ============================================================
    op.create_table(
        "analyses",
        sa.Column(
            "id", sa.String(), nullable=False, comment="Уникальный идентификатор анализа (UUID)"
        ),
        sa.Column(
            "document_id", sa.String(), nullable=False, comment="ID анализируемого документа"
        ),
        sa.Column("status", sa.String(length=50), nullable=False, comment="Статус анализа"),
        sa.Column(
            "overall_score",
            sa.Numeric(precision=3, scale=1),
            nullable=True,
            comment="Общая оценка (0.0 - 10.0)",
        ),
        sa.Column(
            "results",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Результаты анализа",
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=True, comment="Время начала анализа"
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Время завершения анализа",
        ),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Сообщение об ошибке"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Время создания записи",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Время последнего обновления",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="check_analysis_status",
        ),
        sa.CheckConstraint(
            "overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 10)",
            name="check_overall_score_range",
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Результаты анализа документов",
    )
    op.create_index("idx_analyses_document_id", "analyses", ["document_id"])
    op.create_index("idx_analyses_status", "analyses", ["status"])
    op.create_index("idx_analyses_overall_score", "analyses", ["overall_score"])
    op.create_index("idx_analyses_created_at", "analyses", [sa.text("created_at DESC")])

    # ============================================================
    # Таблица reports
    # ============================================================
    op.create_table(
        "reports",
        sa.Column(
            "id", sa.String(), nullable=False, comment="Уникальный идентификатор отчета (UUID)"
        ),
        sa.Column("analysis_id", sa.String(), nullable=False, comment="ID связанного анализа"),
        sa.Column("overall_assessment", sa.Text(), nullable=True, comment="Общая оценка текстом"),
        sa.Column(
            "recommendations",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
            comment="Рекомендации",
        ),
        sa.Column(
            "supervisor_comments",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
            comment="Комментарии руководителя",
        ),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), nullable=False, comment="Время генерации"
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        comment="Сгенерированные отчеты",
    )
    op.create_index("idx_reports_analysis_id", "reports", ["analysis_id"])

    # ============================================================
    # Таблица history
    # ============================================================
    op.create_table(
        "history",
        sa.Column(
            "id", sa.String(), nullable=False, comment="Уникальный идентификатор записи (UUID)"
        ),
        sa.Column("document_id", sa.String(), nullable=False, comment="ID документа"),
        sa.Column("version_number", sa.Integer(), nullable=False, comment="Номер версии"),
        sa.Column("analysis_id", sa.String(), nullable=False, comment="ID анализа"),
        sa.Column(
            "changes_summary",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Сводка изменений",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, comment="Время создания"
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.CheckConstraint("version_number > 0", name="check_version_number_positive"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number", name="unique_document_version"),
        comment="История версий документов",
    )
    op.create_index("idx_history_document_id", "history", ["document_id"])
    op.create_index("idx_history_version_number", "history", ["document_id", "version_number"])
    op.create_index("idx_history_created_at", "history", [sa.text("created_at DESC")])


def downgrade() -> None:
    # Удаляем в обратном порядке из-за внешних ключей
    op.drop_table("history")
    op.drop_table("reports")
    op.drop_table("analyses")
    op.drop_table("documents")
    op.drop_table("users")
