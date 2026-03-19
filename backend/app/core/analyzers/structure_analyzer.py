"""
Анализатор структуры документа.

Проверяет наличие и правильность структуры дипломной работы.
"""

from app.core.analyzers.base_analyzer import BaseAnalyzer
from app.core.const import AnalysisCriteria
from app.core.interfaces.llm import LLMClient, Message
from app.infrastructure.llm.prompts import get_prompt
from app.infrastructure.logging import AppLogger


class StructureAnalyzer(BaseAnalyzer):
    """Анализатор структуры дипломной работы.

    Проверяет наличие обязательных разделов:
    - Введение
    - Основная часть (главы)
    - Заключение
    - Список литературы
    """

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует анализатор структуры.

        Args:
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        super().__init__(
            name=AnalysisCriteria.STRUCTURE,
            description=AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.STRUCTURE],
            llm_client=llm_client,
            logger=logger,
            max_score=AnalysisCriteria.MAX_SCORES[AnalysisCriteria.STRUCTURE],
        )
        self._prompt = get_prompt(AnalysisCriteria.STRUCTURE)

    def _build_prompt(self, text: str, **kwargs: object) -> list[Message]:
        """Строит промпт для анализа структуры.

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
                content=f"Проанализируй структуру следующего текста:\n\n{text}",
            ),
        ]
