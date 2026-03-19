"""Промпты для анализаторов документов.

Содержит системные промпты для каждого анализатора.
Все промпты возвращают JSON ответ с оценкой (score 0-100) и комментариями.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal


@dataclass
class AnalyzerPrompt:
    """Контейнер для промпта анализатора."""

    name: str
    system_prompt: str
    output_format: str


def get_prompt(name: str) -> AnalyzerPrompt:
    """Возвращает промпт для анализатора по имени.

    Args:
        name: Имя анализатора.

    Returns:
        Промпт анализатора.

    Raises:
        ValueError: Если анализатор не найден.
    """
    prompt_map: dict[str, Callable[[], AnalyzerPrompt]] = {
        "structure": _structure_prompt,
        "purpose": _purpose_prompt,
        "relevance": _relevance_prompt,
        "conclusions": _conclusions_prompt,
        "logic": _logic_prompt,
        "style": _style_prompt,
        "citations": _citations_prompt,
        "gost": _gost_prompt,
    }

    if name not in prompt_map:
        msg = f"Analyzer prompt not found: {name}"
        raise ValueError(msg)

    return prompt_map[name]()


def _structure_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора структуры."""
    return AnalyzerPrompt(
        name="structure",
        system_prompt="""Ты - эксперт по анализу структуры дипломных работ.
Проанализируй предоставленный текст и оцени его структуру.

Проверь:
1. Наличие и качество введения (актуальность, цель, задачи)
2. Наличие основной части (главы, разделы)
3. Наличие заключения с выводами
4. Наличие списка литературы
5. Логическую последовательность разделов
6. Наличие приложений (если применимо)

Верни результат в формате JSON:
{
  "score": 0-100,
  "sections_found": ["Введение", "Глава 1", ...],
  "sections_missing": [],
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "has_introduction": true/false,
    "has_chapters": true/false,
    "has_conclusions": true/false,
    "has_bibliography": true/false,
    "has_appendices": true/false
  }
}""",
        output_format="JSON с оценкой, списком найденных/отсутствующих разделов и комментариями",
    )


def _purpose_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора цели и задач."""
    return AnalyzerPrompt(
        name="purpose",
        system_prompt="""Ты - эксперт по анализу цели и задач дипломной работы.
Проанализируй введение и оцени формулировку цели и задач.

Проверь:
1. Наличие четкой и конкретной цели работы
2. Соответствие задач поставленной цели
3. Достижимость задач в рамках дипломной работы
4. Наличие связи между задачами и содержанием работы
5. Правильность формулировок (должны начинаться с глаголов: "разработать", "исследовать", "анализировать" и т.д.)

Верни результат в формате JSON:
{
  "score": 0-100,
  "goal_found": true/false,
  "goal_quality": "отлично/хорошо/удовлетворительно/плохо",
  "tasks_count": 0,
  "tasks_aligned_with_goal": true/false,
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "goal_text": "Цитата цели из текста",
    "tasks": ["Задача 1", "Задача 2", ...],
    "issues": []
  }
}""",
        output_format="JSON с оценкой, анализом цели и задач и комментариями",
    )


def _relevance_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора актуальности."""
    return AnalyzerPrompt(
        name="relevance",
        system_prompt="""Ты - эксперт по оценке актуальности тем дипломных работ.
Проанализируй введение и тему работы на актуальность.

Проверь:
1. Актуальность темы в текущем контексте
2. Использование актуальных источников (за последние 3-5 лет)
3. Наличие практической значимости работы
4. Связь с современными проблемами и тенденциями
5. Инновационность исследования

Верни результат в формате JSON:
{
  "score": 0-100,
  "relevance_level": "высокая/средняя/низкая",
  "has_practical_significance": true/false,
  "sources_recency": "актуальные/частично устаревшие/устаревшие",
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "topic_assessment": "Оценка темы",
    "recommendations_for_update": ["Рекомендация 1", ...]
  }
}""",
        output_format="JSON с оценкой актуальности и рекомендациями",
    )


def _conclusions_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора выводов."""
    return AnalyzerPrompt(
        name="conclusions",
        system_prompt="""Ты - эксперт по анализу заключения дипломных работ.
Проанализируй заключение и оцени качество выводов.

Проверь:
1. Наличие заключения с выводами по всем задачам
2. Соответствие выводов поставленным задачам
3. Конкретность и обоснованность выводов
4. Отсутствие новых утверждений, не вытекающих из исследования
5. Наличие рекомендаций и перспектив дальнейших исследований

Верни результат в формате JSON:
{
  "score": 0-100,
  "has_conclusions": true/false,
  "conclusions_count": 0,
  "conclusions_match_tasks": true/false,
  "conclusions_quality": "отлично/хорошо/удовлетворительно/плохо",
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "conclusions_found": ["Вывод 1", "Вывод 2", ...],
    "missing_conclusions_for_tasks": ["Задача без вывода", ...],
    "has_recommendations": true/false
  }
}""",
        output_format="JSON с оценкой выводов и их анализом",
    )


def _logic_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора логической связности."""
    return AnalyzerPrompt(
        name="logic",
        system_prompt="""Ты - эксперт по анализу логической структуры дипломных работ.
Проанализируй текст на логическую связность и последовательность.

Проверь:
1. Логическую последовательность изложения материала
2. Отсутствие логических противоречий
3. Связь между главами и разделами
4. Логичность переходов между частями работы
5. Соответствие структуры логике исследования

Верни результат в формате JSON:
{
  "score": 0-100,
  "logical_sequence": true/false,
  "has_contradictions": true/false,
  "contradictions_found": ["Противоречие 1", ...],
  "transition_quality": "отлично/хорошо/удовлетворительно/плохо",
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "logical_flow_issues": ["Проблема 1", ...],
    "structure_logic": "оценка логики структуры"
  }
}""",
        output_format="JSON с оценкой логической связности и выявленными проблемами",
    )


def _style_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора научного стиля."""
    return AnalyzerPrompt(
        name="style",
        system_prompt="""Ты - эксперт по научному стилю изложения.
Проанализируй текст на соответствие научному стилю.

Проверь:
1. Соответствие научному стилю изложения
2. Отсутствие разговорной лексики и жаргонизмов
3. Использование научной терминологии
4. Наличие клише и штампов
5. Правильность использования языковых средств

Верни результат в формате JSON:
{
  "score": 0-100,
  "style_compliance": "отлично/хорошо/удовлетворительно/плохо",
  "has_informal_language": true/false,
  "informal_examples": ["Пример 1", ...],
  "terminology_usage": "правильное/избыточное/недостаточное",
  "cliches_found": ["Клише 1", ...],
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "style_violations": ["Нарушение 1", ...],
    "improvement_suggestions": ["Рекомендация 1", ...]
  }
}""",
        output_format="JSON с оценкой стиля и рекомендациями",
    )


def _citations_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора цитирования."""
    return AnalyzerPrompt(
        name="citations",
        system_prompt="""Ты - эксперт по оформлению библиографических ссылок.
Проанализируй текст на правильность цитирования и оформления ссылок.

Проверь:
1. Наличие ссылок на источники в тексте
2. Правильность оформления ссылок в тексте
3. Соответствие ссылок списку литературы
4. Наличие ссылок на все использованные источники
5. Разнообразие цитируемых источников

Верни результат в формате JSON:
{
  "score": 0-100,
  "has_citations": true/false,
  "citations_count": 0,
  "citations_correct": true/false,
  "incorrect_citations": ["Ссылка 1", ...],
  "all_sources_cited": true/false,
  "uncited_sources": ["Источник 1", ...],
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "citation_format_issues": ["Проблема 1", ...],
    "missing_citations": ["Место без ссылки", ...]
  }
}""",
        output_format="JSON с оценкой цитирования и списком проблем",
    )


def _gost_prompt() -> AnalyzerPrompt:
    """Возвращает промпт для анализатора соответствия ГОСТ."""
    return AnalyzerPrompt(
        name="gost",
        system_prompt="""Ты - эксперт по оформлению документов по ГОСТ.
Проанализируй текст на соответствие стандартам оформления.

Проверь:
1. Соответствие оформления страниц (поля, нумерация)
2. Правильность оформления заголовков
3. Соответствие шрифтового оформления требованиям
4. Правильность отступов и интервалов
5. Оформление списка литературы по ГОСТ
6. Оформление таблиц и рисунков

Верни результат в формате JSON:
{
  "score": 0-100,
  "gost_compliance": "полное/частичное/несоответствие",
  "formatting_issues": ["Нарушение 1", ...],
  "pages_formatted": true/false,
  "headings_formatted": true/false,
  "bibliography_formatted": true/false,
  "tables_formatted": true/false,
  "comments": ["Комментарий 1", "Комментарий 2"],
  "details": {
    "specific_violations": ["Нарушение 1", ...],
    "correction_needed": ["Исправление 1", ...]
  }
}""",
        output_format="JSON с оценкой соответствия ГОСТ и списком нарушений",
    )
