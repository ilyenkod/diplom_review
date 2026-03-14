"""
Константы приложения.

Определяет критерии оценки, форматы файлов и другие константы.
"""

from typing import Final

# ========== File Formats ==========


class FileFormats:
    """Поддерживаемые форматы файлов."""

    DOCX: Final = "docx"
    PDF: Final = "pdf"
    TXT: Final = "txt"

    ALLOWED: Final = {DOCX, PDF, TXT}

    MIME_TYPES: Final = {
        DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        PDF: "application/pdf",
        TXT: "text/plain",
    }

    EXTENSIONS: Final = {
        DOCX: ".docx",
        PDF: ".pdf",
        TXT: ".txt",
    }


# ========== Analysis Criteria ==========


class AnalysisCriteria:
    """Критерии анализа дипломных работ."""

    STRUCTURE: Final = "structure"
    PURPOSE: Final = "purpose"
    RELEVANCE: Final = "relevance"
    CONCLUSIONS: Final = "conclusions"
    LOGIC: Final = "logic"
    STYLE: Final = "style"
    CITATIONS: Final = "citations"
    GOST: Final = "gost"

    ALL: Final = {
        STRUCTURE,
        PURPOSE,
        RELEVANCE,
        CONCLUSIONS,
        LOGIC,
        STYLE,
        CITATIONS,
        GOST,
    }

    # Описание критериев
    DESCRIPTIONS: Final = {
        STRUCTURE: "Наличие и правильность структуры работы",
        PURPOSE: "Соответствие цели и задач содержанию работы",
        RELEVANCE: "Актуальность темы исследования",
        CONCLUSIONS: "Наличие и корректность выводов",
        LOGIC: "Логическая связность и последовательность изложения",
        STYLE: "Научный стиль изложения",
        CITATIONS: "Правильность цитирования и оформления ссылок",
        GOST: "Соответствие стандартам оформления",
    }

    # Максимальный балл по каждому критерию
    MAX_SCORES: Final = {
        STRUCTURE: 10.0,
        PURPOSE: 10.0,
        RELEVANCE: 10.0,
        CONCLUSIONS: 10.0,
        LOGIC: 10.0,
        STYLE: 10.0,
        CITATIONS: 10.0,
        GOST: 10.0,
    }

    # Веса критериев для общей оценки
    WEIGHTS: Final = {
        STRUCTURE: 1.0,
        PURPOSE: 1.2,
        RELEVANCE: 1.1,
        CONCLUSIONS: 1.2,
        LOGIC: 1.1,
        STYLE: 0.9,
        CITATIONS: 1.0,
        GOST: 0.8,
    }


# ========== Assessment Levels ==========


class AssessmentLevel:
    """Уровни оценки работы."""

    EXCELLENT: Final = "excellent"
    GOOD: Final = "good"
    SATISFACTORY: Final = "satisfactory"
    POOR: Final = "poor"

    SCORE_RANGES: Final = {
        EXCELLENT: (8.5, 10.0),
        GOOD: (7.0, 8.5),
        SATISFACTORY: (5.5, 7.0),
        POOR: (0.0, 5.5),
    }

    LABELS: Final = {
        EXCELLENT: "Отлично",
        GOOD: "Хорошо",
        SATISFACTORY: "Удовлетворительно",
        POOR: "Неудовлетворительно",
    }

    DESCRIPTIONS: Final = {
        EXCELLENT: "Высококачественная работа, соответствующая всем требованиям",
        GOOD: "Хорошая работа с незначительными замечаниями",
        SATISFACTORY: "Работа с существенными недостатками, требует доработки",
        POOR: "Низкое качество работы, требует существенной переработки",
    }


# ========== Document Structure Requirements ==========


class DocumentStructure:
    """Требования к структуре документа."""

    REQUIRED_SECTIONS: Final = [
        "введение",
        "основная часть",
        "заключение",
    ]

    OPTIONAL_SECTIONS: Final = [
        "аннотация",
        "содержание",
        "список литературы",
        "приложения",
    ]

    MIN_WORD_COUNT: Final = 10000  # Минимальное количество слов
    MAX_WORD_COUNT: Final = 100000  # Максимальное количество слов

    INTRO_MIN_WORDS: Final = 500  # Минимальное количество слов во введении
    CONCLUSION_MIN_WORDS: Final = 500  # Минимальное количество слов в заключении


# ========== Style Requirements ==========


class StyleRequirements:
    """Требования к стилю."""

    MIN_SENTENCE_LENGTH: Final = 10
    MAX_SENTENCE_LENGTH: Final = 50

    MIN_PARAGRAPH_LENGTH: Final = 50
    MAX_PARAGRAPH_LENGTH: Final = 500

    SCIENTIFIC_TERMS_RATIO: Final = 0.05  # Минимальная доля научной терминологии


# ========== Citation Requirements ==========


class CitationRequirements:
    """Требования к цитированию."""

    MIN_CITATION_COUNT: Final = 20  # Минимальное количество цитат
    MIN_AUTHORS_COUNT: Final = 10  # Минимальное количество авторов

    MAX_CITATION_RATIO: Final = 0.2  # Максимальная доля цитируемого текста


# ========== GOST Requirements ==========


class GOSTRequirements:
    """Требования ГОСТ."""

    PAGE_NUMBERING: Final = "Нумерация страниц"
    MARGINS: Final = "Поля страницы"
    FONT_SIZE: Final = "Размер шрифта"
    LINE_SPACING: Final = "Межстрочный интервал"
    TABLE_FORMAT: Final = "Формат таблиц"
    FIGURE_FORMAT: Final = "Формат рисунков"
    REFERENCE_FORMAT: Final = "Формат ссылок"

    REQUIRED_FIELDS: Final = [
        PAGE_NUMBERING,
        MARGINS,
        FONT_SIZE,
        LINE_SPACING,
        REFERENCE_FORMAT,
    ]


# ========== Text Processing ==========


class TextProcessing:
    """Константы для обработки текста."""

    DEFAULT_ENCODING: Final = "utf-8"
    MAX_FILE_SIZE: Final = 10 * 1024 * 1024  # 10 MB

    CHUNK_SIZE: Final = 4000  # Размер чанка для обработки текста


# ========== LLM Configuration ==========


class LLMConfig:
    """Конфигурация LLM."""

    DEFAULT_MAX_TOKENS: Final = 4096
    DEFAULT_TEMPERATURE: Final = 0.7

    PROMPT_TEMPLATES: Final = {
        "structure": "Проверьте структуру дипломной работы на соответствие академическим стандартам.",
        "purpose": "Оцените соответствие цели и задач содержанию работы.",
        "relevance": "Оцените актуальность темы исследования.",
        "conclusions": "Проверьте наличие и корректность выводов.",
        "logic": "Оцените логическую связность работы.",
        "style": "Проверьте соответствие научному стилю изложения.",
        "citations": "Проверьте правильность цитирования.",
        "gost": "Проверьте соответствие стандартам оформления.",
    }


# ========== Status Codes ==========


class AnalysisStatus:
    """Статусы анализа."""

    PENDING: Final = "pending"
    PROCESSING: Final = "processing"
    COMPLETED: Final = "completed"
    FAILED: Final = "failed"


class UserRole:
    """Роли пользователей."""

    STUDENT: Final = "student"
    ADMIN: Final = "admin"
    SUPERVISOR: Final = "supervisor"


# ========== Cache TTL ==========


class CacheTTL:
    """Время жизни кэша в секундах."""

    SHORT: Final = 300  # 5 минут
    MEDIUM: Final = 3600  # 1 час
    LONG: Final = 86400  # 24 часа
    VERY_LONG: Final = 604800  # 7 дней

    USER: Final = MEDIUM
    DOCUMENT: Final = MEDIUM
    ANALYSIS: Final = LONG
    REPORT: Final = MEDIUM
    HISTORY: Final = VERY_LONG


# ========== Pagination ==========


class Pagination:
    """Параметры пагинации."""

    DEFAULT_LIMIT: Final = 20
    DEFAULT_OFFSET: Final = 0
    MAX_LIMIT: Final = 100
