"""
Модуль анализаторов документов.

Содержит базовый класс и конкретные реализации анализаторов.
"""

from app.core.analyzers.base_analyzer import (
    AnalyzerCriteria,
    AnalyzerResult,
    BaseAnalyzer,
)
from app.core.analyzers.citations_analyzer import CitationsAnalyzer
from app.core.analyzers.conclusions_analyzer import ConclusionsAnalyzer
from app.core.analyzers.gost_analyzer import GOSTAnalyzer
from app.core.analyzers.logic_analyzer import LogicAnalyzer
from app.core.analyzers.purpose_analyzer import PurposeAnalyzer
from app.core.analyzers.relevance_analyzer import RelevanceAnalyzer
from app.core.analyzers.structure_analyzer import StructureAnalyzer
from app.core.analyzers.style_analyzer import StyleAnalyzer

__all__ = [
    "AnalyzerCriteria",
    "AnalyzerResult",
    "BaseAnalyzer",
    "CitationsAnalyzer",
    "ConclusionsAnalyzer",
    "GOSTAnalyzer",
    "LogicAnalyzer",
    "PurposeAnalyzer",
    "RelevanceAnalyzer",
    "StructureAnalyzer",
    "StyleAnalyzer",
]

ANALYZER_CLASSES: dict[str, type[BaseAnalyzer]] = {
    "structure": StructureAnalyzer,
    "purpose": PurposeAnalyzer,
    "relevance": RelevanceAnalyzer,
    "conclusions": ConclusionsAnalyzer,
    "logic": LogicAnalyzer,
    "style": StyleAnalyzer,
    "citations": CitationsAnalyzer,
    "gost": GOSTAnalyzer,
}
