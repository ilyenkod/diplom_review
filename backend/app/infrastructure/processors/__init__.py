"""Document processors infrastructure."""

from app.infrastructure.processors.base import BaseProcessor, ProcessorResult
from app.infrastructure.processors.docx_processor import DocxProcessor
from app.infrastructure.processors.pdf_processor import PdfProcessor
from app.infrastructure.processors.txt_processor import TxtProcessor

__all__ = [
    "BaseProcessor",
    "DocxProcessor",
    "PdfProcessor",
    "ProcessorResult",
    "TxtProcessor",
]
