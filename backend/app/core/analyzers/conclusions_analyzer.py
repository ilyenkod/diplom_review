"""
Анализатор выводов.

Проверяет наличие и корректность выводов в заключении.
"""

from app.core.analyzers.base_analyzer import BaseAnalyzer
from app.core.const import AnalysisCriteria
from app.core.interfaces.llm import LLMClient, Message
from app.infrastructure.llm.prompts import get_prompt
from app.infrastructure.logging import AppLogger


class ConclusionsAnalyzer(BaseAnalyzer):
    """Анализатор выводов дипломной работы.

    Проверяет:
    - Наличие заключения с выводами
    - Соответствие выводов задачам
    - Конкретность и обоснованность
    - Наличие рекомендаций
    """

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует анализатор выводов.

        Args:
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        super().__init__(
            name=AnalysisCriteria.CONCLUSIONS,
            description=AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.CONCLUSIONS],
            llm_client=llm_client,
            logger=logger,
            max_score=AnalysisCriteria.MAX_SCORES[AnalysisCriteria.CONCLUSIONS],
        )
        self._prompt = get_prompt(AnalysisCriteria.CONCLUSIONS)

    def _build_prompt(self, text: str, **kwargs: object) -> list[Message]:
        """Строит промпт для анализа выводов.

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
                content=f"Проанализируй выводы в следующем тексте:\n\n{text}",
            ),
        ]
