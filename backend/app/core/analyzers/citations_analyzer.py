"""
Анализатор цитирования.

Проверяет правильность цитирования и оформления ссылок.
"""

from app.core.analyzers.base_analyzer import BaseAnalyzer
from app.core.const import AnalysisCriteria
from app.core.interfaces.llm import LLMClient, Message
from app.infrastructure.llm.prompts import get_prompt
from app.infrastructure.logging import AppLogger


class CitationsAnalyzer(BaseAnalyzer):
    """Анализатор цитирования дипломной работы.

    Проверяет:
    - Наличие ссылок на источники
    - Правильность оформления ссылок
    - Соответствие ссылок списку литературы
    - Разнообразие источников
    """

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует анализатор цитирования.

        Args:
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        super().__init__(
            name=AnalysisCriteria.CITATIONS,
            description=AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.CITATIONS],
            llm_client=llm_client,
            logger=logger,
            max_score=AnalysisCriteria.MAX_SCORES[AnalysisCriteria.CITATIONS],
        )
        self._prompt = get_prompt(AnalysisCriteria.CITATIONS)

    def _build_prompt(self, text: str, **kwargs: object) -> list[Message]:
        """Строит промпт для анализа цитирования.

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
                content=f"Проанализируй цитирование в следующем тексте:\n\n{text}",
            ),
        ]
