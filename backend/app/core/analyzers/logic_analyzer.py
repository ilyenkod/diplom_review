"""
Анализатор логической связности.

Проверяет логическую последовательность изложения.
"""

from app.core.analyzers.base_analyzer import BaseAnalyzer
from app.core.const import AnalysisCriteria
from app.core.interfaces.llm import LLMClient, Message
from app.infrastructure.llm.prompts import get_prompt
from app.infrastructure.logging import AppLogger


class LogicAnalyzer(BaseAnalyzer):
    """Анализатор логической связности дипломной работы.

    Проверяет:
    - Логическую последовательность изложения
    - Отсутствие противоречий
    - Связь между главами и разделами
    - Логичность переходов
    """

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует анализатор логической связности.

        Args:
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        super().__init__(
            name=AnalysisCriteria.LOGIC,
            description=AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.LOGIC],
            llm_client=llm_client,
            logger=logger,
            max_score=AnalysisCriteria.MAX_SCORES[AnalysisCriteria.LOGIC],
        )
        self._prompt = get_prompt(AnalysisCriteria.LOGIC)

    def _build_prompt(self, text: str, **kwargs: object) -> list[Message]:
        """Строит промпт для анализа логической связности.

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
                content=f"Проанализируй логическую связность следующего текста:\n\n{text}",
            ),
        ]
