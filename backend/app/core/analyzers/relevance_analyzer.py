"""
Анализатор актуальности темы.

Проверяет актуальность темы исследования.
"""

from app.core.analyzers.base_analyzer import BaseAnalyzer
from app.core.const import AnalysisCriteria
from app.core.interfaces.llm import LLMClient, Message
from app.infrastructure.llm.prompts import get_prompt
from app.infrastructure.logging import AppLogger


class RelevanceAnalyzer(BaseAnalyzer):
    """Анализатор актуальности темы дипломной работы.

    Проверяет:
    - Актуальность темы в современном контексте
    - Использование актуальных источников
    - Практическую значимость
    - Связь с современными тенденциями
    """

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует анализатор актуальности.

        Args:
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        super().__init__(
            name=AnalysisCriteria.RELEVANCE,
            description=AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.RELEVANCE],
            llm_client=llm_client,
            logger=logger,
            max_score=AnalysisCriteria.MAX_SCORES[AnalysisCriteria.RELEVANCE],
        )
        self._prompt = get_prompt(AnalysisCriteria.RELEVANCE)

    def _build_prompt(self, text: str, **kwargs: object) -> list[Message]:
        """Строит промпт для анализа актуальности.

        Args:
            text: Текст документа.
            **kwargs: Дополнительные параметры.

        Returns:
            Список сообщений для LLM.
        """
        return [
            Message(role="system", content=self._prompt.system_prompt),
            Message(
                role="user",
                content=f"Оцени актуальность темы в следующем тексте:\n\n{text}",
            ),
        ]
