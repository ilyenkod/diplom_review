"""
Unit-тесты для процессоров документов.

Тестирует:
- BaseProcessor
- ProcessorResult
- DOCX, PDF, TXT процессоры
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.const import FileFormats
from app.infrastructure.processors.base import BaseProcessor, ProcessorResult


# ========== ProcessorResult Tests ==========


@pytest.mark.unit
class TestProcessorResult:
    """Тесты для результата обработки."""

    def test_processor_result_creation_success(self):
        """Тестирует создание результата обработки при успехе."""
        result = ProcessorResult(
            success=True,
            text="Extracted text",
            error=None,
            metadata={"pages": 3},
        )

        assert result.success is True
        assert result.text == "Extracted text"
        assert result.error is None
        assert result.metadata == {"pages": 3}

    def test_processor_result_creation_failure(self):
        """Тестирует создание результата обработки при ошибке."""
        result = ProcessorResult(
            success=False,
            text="",
            error="Failed to process file",
            metadata=None,
        )

        assert result.success is False
        assert result.text == ""
        assert result.error == "Failed to process file"
        assert result.metadata is None

    def test_processor_result_defaults(self):
        """Тестирует значения по умолчанию."""
        result = ProcessorResult(success=True, text="Test")

        assert result.success is True
        assert result.text == "Test"
        assert result.error is None
        assert result.metadata is None


# ========== BaseProcessor Tests ==========


@pytest.mark.unit
class TestBaseProcessor:
    """Тесты для базового процессора."""

    @pytest.fixture
    def mock_processor(self):
        """Возвращает mock процессор для тестирования."""

        class MockProcessor(BaseProcessor):
            def get_supported_extensions(self) -> set[str]:
                return {"txt", "md"}

            async def process(self, file_path: Path) -> ProcessorResult:
                return ProcessorResult(success=True, text="Mock content")

            async def process_bytes(self, content: bytes) -> ProcessorResult:
                text = content.decode("utf-8")
                return ProcessorResult(success=True, text=text)

        return MockProcessor()

    def test_get_supported_extensions(self, mock_processor):
        """Тестирует получение поддерживаемых расширений."""
        extensions = mock_processor.get_supported_extensions()

        assert "txt" in extensions
        assert "md" in extensions
        assert len(extensions) == 2

    def test_can_process_supported_file(self, mock_processor):
        """Тестирует проверку поддерживаемого файла."""
        txt_file = Path("/tmp/test.txt")
        md_file = Path("/tmp/test.md")

        assert mock_processor.can_process(txt_file) is True
        assert mock_processor.can_process(md_file) is True

    def test_can_process_unsupported_file(self, mock_processor):
        """Тестирует проверку неподдерживаемого файла."""
        pdf_file = Path("/tmp/test.pdf")
        docx_file = Path("/tmp/test.docx")

        assert mock_processor.can_process(pdf_file) is False
        assert mock_processor.can_process(docx_file) is False

    @pytest.mark.asyncio
    async def test_process_bytes(self, mock_processor):
        """Тестирует обработку байтов."""
        content = b"Test content"

        result = await mock_processor.process_bytes(content)

        assert result.success is True
        assert result.text == "Test content"

    @pytest.mark.asyncio
    async def test_process(self, mock_processor):
        """Тестирует обработку файла."""
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"Test content")
            file_path = Path(f.name)

        try:
            result = await mock_processor.process(file_path)

            assert result.success is True
            assert result.text == "Mock content"
        finally:
            file_path.unlink()


# ========== Mock Processors Tests ==========


@pytest.mark.unit
class TestMockProcessors:
    """Тесты для mock процессоров."""

    @pytest.mark.asyncio
    async def test_txt_processor_success(self, mock_processors):
        """Тестирует успешную обработку TXT файла."""
        txt_processor = mock_processors[FileFormats.TXT]
        content = b"This is a test text file"

        result = await txt_processor.process_bytes(content)

        assert result.success is True
        assert result.text == "Processed text content"

    @pytest.mark.asyncio
    async def test_pdf_processor_success(self, mock_processors):
        """Тестирует успешную обработку PDF файла."""
        pdf_processor = mock_processors[FileFormats.PDF]
        content = b"%PDF-1.4 fake pdf content"

        result = await pdf_processor.process_bytes(content)

        assert result.success is True
        assert result.text == "Processed text content"

    @pytest.mark.asyncio
    async def test_docx_processor_success(self, mock_processors):
        """Тестирует успешную обработку DOCX файла."""
        docx_processor = mock_processors[FileFormats.DOCX]
        content = b"PK\x03\x04 fake docx content"

        result = await docx_processor.process_bytes(content)

        assert result.success is True
        assert result.text == "Processed text content"

    @pytest.mark.asyncio
    async def test_processor_failure_handling(self, mock_processors):
        """Тестирует обработку ошибок процессора."""
        txt_processor = mock_processors[FileFormats.TXT]

        # Configure mock to return failure
        txt_processor.process_bytes.return_value = ProcessorResult(
            success=False,
            text="",
            error="Processing failed",
        )

        result = await txt_processor.process_bytes(b"content")

        assert result.success is False
        assert result.error == "Processing failed"
        assert result.text == ""

    @pytest.mark.asyncio
    async def test_processor_metadata(self, mock_processors):
        """Тестирует метаданные результата обработки."""
        txt_processor = mock_processors[FileFormats.TXT]

        result = await txt_processor.process_bytes(b"content")

        assert result.metadata is not None
        assert result.metadata.get("pages") == 1


# ========== Processor Integration Tests ==========


@pytest.mark.unit
class TestProcessorIntegration:
    """Интеграционные тесты для процессоров."""

    @pytest.mark.asyncio
    async def test_select_processor_by_extension(self, mock_processors):
        """Тестирует выбор процессора по расширению файла."""
        # Test TXT
        txt_processor = mock_processors.get(FileFormats.TXT)
        assert txt_processor is not None

        # Test PDF
        pdf_processor = mock_processors.get(FileFormats.PDF)
        assert pdf_processor is not None

        # Test DOCX
        docx_processor = mock_processors.get(FileFormats.DOCX)
        assert docx_processor is not None

    @pytest.mark.asyncio
    async def test_all_processors_have_required_methods(self, mock_processors):
        """Тестирует, что все процессоры имеют требуемые методы."""
        for file_type, processor in mock_processors.items():
            # Check for async methods
            assert hasattr(processor, "process")
            assert hasattr(processor, "process_bytes")

            # Verify they are callable
            assert callable(processor.process)
            assert callable(processor.process_bytes)

    @pytest.mark.asyncio
    async def test_processor_result_consistency(self, mock_processors):
        """Тестирует согласованность результатов всех процессоров."""
        test_content = b"Test content"

        for file_type, processor in mock_processors.items():
            # The mock processors return MagicMock objects, so we need to check
            # that they have the expected structure
            result = await processor.process_bytes(test_content)

            # All processors should return objects with required attributes
            assert hasattr(result, "success")
            assert hasattr(result, "text")
            assert hasattr(result, "error")

            # Success or error should be set appropriately
            if result.success:
                assert result.text != ""
                assert result.error is None
            else:
                assert result.text == ""
                assert result.error is not None


# ========== Processor Error Handling Tests ==========


@pytest.mark.unit
class TestProcessorErrorHandling:
    """Тесты обработки ошибок процессорами."""

    @pytest.mark.asyncio
    async def test_empty_content_handling(self, mock_processors):
        """Тестирует обработку пустого содержимого."""
        txt_processor = mock_processors[FileFormats.TXT]

        result = await txt_processor.process_bytes(b"")

        # Mock processors return success even for empty content
        assert result is not None
        assert hasattr(result, "success")

    @pytest.mark.asyncio
    async def test_large_content_handling(self, mock_processors):
        """Тестирует обработку большого содержимого."""
        txt_processor = mock_processors[FileFormats.TXT]

        # Create large content (1MB)
        large_content = b"x" * (1024 * 1024)

        result = await txt_processor.process_bytes(large_content)

        assert result is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_unicode_content_handling(self, mock_processors):
        """Тестирует обработку Unicode содержимого."""
        txt_processor = mock_processors[FileFormats.TXT]

        # Test with various Unicode characters
        unicode_content = "Привет мир 你好世界 مرحبا بالعالم".encode("utf-8")

        result = await txt_processor.process_bytes(unicode_content)

        assert result is not None
        assert result.success is True
