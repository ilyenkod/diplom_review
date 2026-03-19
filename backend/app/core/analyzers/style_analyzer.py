"""
Анализатор научного стиля.

Проверяет соответствие научному стилю изложения.
"""

from app.core.analyzers.base_analyzer import BaseAnalyzer
from app.core.const import AnalysisCriteria
from app.core.interfaces.llm import LLMClient, Message
from app.infrastructure.llm.prompts import get_prompt
from app.infrastructure.logging import AppLogger


class StyleAnalyzer(BaseAnalyzer):
    """Анализатор научного стиля дипломной работы.

    Проверяет:
    - Соответствие научному стилю
    - Отсутствие разговорной лексики
    - Использование научной терминологии
    - Отсутствие клише и штампов
    """

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует анализатор научного стиля.

        Args:
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        super().__init__(
            name=AnalysisCriteria.STYLE,
            description=AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.STYLE],
            llm_client=llm_client,
            logger=logger,
            max_score=AnalysisCriteria.MAX_SCORES[AnalysisCriteria.STYLE],
        )
        self._prompt = get_prompt(AnalysisCriteria.STYLE)

    def _build_prompt(self, text: str, **kwargs: object) -> list[Message]:
        """Строит промпт для анализа научного стиля.

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
                content=f"Проанализируй научный стиль следующего текста:\n\n{text}",
            ),
        ]
