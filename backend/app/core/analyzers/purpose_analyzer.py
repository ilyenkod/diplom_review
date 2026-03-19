"""
Анализатор цели и задач.

Проверяет соответствие цели и задач содержанию работы.
"""

from app.core.analyzers.base_analyzer import BaseAnalyzer
from app.core.const import AnalysisCriteria
from app.core.interfaces.llm import LLMClient, Message
from app.infrastructure.llm.prompts import get_prompt
from app.infrastructure.logging import AppLogger


class PurposeAnalyzer(BaseAnalyzer):
    """Анализатор цели и задач дипломной работы.

    Проверяет:
    - Наличие четкой цели
    - Соответствие задач цели
    - Достижимость задач
    - Правильность формулировок
    """

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует анализатор цели и задач.

        Args:
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        super().__init__(
            name=AnalysisCriteria.PURPOSE,
            description=AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.PURPOSE],
            llm_client=llm_client,
            logger=logger,
            max_score=AnalysisCriteria.MAX_SCORES[AnalysisCriteria.PURPOSE],
        )
        self._prompt = get_prompt(AnalysisCriteria.PURPOSE)

    def _build_prompt(self, text: str, **kwargs: object) -> list[Message]:
        """Строит промпт для анализа цели и задач.

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
                content=f"Проанализируй цель и задачи в следующем тексте:\n\n{text}",
            ),
        ]
