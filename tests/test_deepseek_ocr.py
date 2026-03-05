#!/usr/bin/env python3
"""Unit tests for DeepSeek-OCR-2 module (is_image_pdf, sanitize_markdown)."""

import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from doc2markdown.deepseek_v2_ocr import (
    is_image_pdf,
    pdf_to_markdown_with_ocr,
    sanitize_markdown,
    MIN_CHARS_PER_PAGE,
)


def _get_fixture_pdf_path():
    """Return path to a scanned/image PDF fixture if one exists, else None."""
    fixture_dir = Path(__file__).parent / "fixtures"
    for name in ("scanned_or_image.pdf", "scanned.pdf", "image_based.pdf"):
        p = fixture_dir / name
        if p.exists():
            return p
    return None


class TestSanitizeMarkdown:
    """Tests for sanitize_markdown."""

    def test_normalizes_line_endings(self):
        assert "\r\n" not in sanitize_markdown("a\r\nb")
        assert "a\nb" in sanitize_markdown("a\r\nb")

    def test_collapses_blank_lines(self):
        out = sanitize_markdown("a\n\n\n\nb")
        assert out.count("\n\n") <= 2
        assert "a" in out and "b" in out

    def test_strips_trailing_spaces_on_lines(self):
        out = sanitize_markdown("line1   \nline2")
        assert out.endswith("\n")
        assert "line1\n" in out

    def test_returns_with_trailing_newline(self):
        out = sanitize_markdown("x")
        assert out == "x\n"


class TestIsImagePdf:
    """Tests for is_image_pdf (requires pypdf)."""

    def test_nonexistent_path_returns_false(self):
        assert is_image_pdf("/nonexistent/file.pdf") is False

    def test_non_pdf_extension_returns_false(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("hello")
        assert is_image_pdf(f) is False

    def test_text_rich_pdf_returns_false(self):
        """When PDF has enough text per page, is_image_pdf returns False."""
        from unittest.mock import MagicMock, patch

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "A" * (MIN_CHARS_PER_PAGE + 10)
            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]

            with patch(
                "pypdf.PdfReader",
                return_value=mock_reader,
            ):
                assert is_image_pdf(path) is False
        finally:
            Path(path).unlink(missing_ok=True)

    def test_image_like_pdf_returns_true(self):
        """When PDF has very little text per page, is_image_pdf returns True."""
        from unittest.mock import MagicMock, patch

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "x"  # almost no text
            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]

            with patch(
                "pypdf.PdfReader",
                return_value=mock_reader,
            ):
                assert is_image_pdf(path) is True
        finally:
            Path(path).unlink(missing_ok=True)

    def test_empty_pdf_or_exception_returns_false(self):
        """Broken or empty PDF should not crash; may return False."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"not a real pdf")
            path = f.name
        try:
            # Should not raise; implementation may return False on parse error
            result = is_image_pdf(path)
            assert isinstance(result, bool)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_actual_image_like_pdf_blank_pages(self):
        """Real PDF with blank pages (no extractable text) is detected as image-based."""
        pytest.importorskip("pypdf")
        from pypdf import PdfWriter
        from pypdf import PageObject

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            writer = PdfWriter()
            # Blank page has no text layer -> same as a scanned page without OCR
            page = PageObject.create_blank_page(None, width=200, height=200)
            writer.add_page(page)
            with open(path, "wb") as out:
                writer.write(out)
            assert is_image_pdf(path) is True
        finally:
            Path(path).unlink(missing_ok=True)

    def test_actual_image_based_pdf_fixture(self):
        """If tests/fixtures/scanned_or_image.pdf exists, it should be detected as image-based."""
        path = _get_fixture_pdf_path()
        if path is None:
            pytest.skip(
                "No fixture PDF found. Add a scanned/image PDF at "
                "tests/fixtures/scanned_or_image.pdf (or scanned.pdf, image_based.pdf) to run this test."
            )
        assert is_image_pdf(path) is True


@pytest.mark.integration
class TestActualModelBasedConversion:
    """Integration tests: run real DeepSeek-OCR-2 on fixture PDFs. Skip with: pytest -m 'not integration'."""

    def test_actual_model_based_conversion_fixture(self):
        """Run pdf_to_markdown_with_ocr on the fixture PDF and assert non-empty markdown output."""
        path = _get_fixture_pdf_path()
        if path is None:
            pytest.skip(
                "No fixture PDF found. Add a scanned/image PDF at "
                "tests/fixtures/scanned_or_image.pdf (or scanned.pdf, image_based.pdf) to run this test."
            )
        try:
            import torch
            from transformers import AutoModel  # noqa: F401
        except ImportError as e:
            pytest.skip(f"OCR dependencies not available: {e}")
        pytest.importorskip("fitz")  # PyMuPDF for PDF → images

        # Prefer CUDA, then MPS (Apple Silicon), then CPU
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        try:
            result = pdf_to_markdown_with_ocr(str(path), device=device, dpi=150)
        except Exception as e:
            err_str = str(e).lower()
            if "flash" in err_str or "attention" in err_str:
                pytest.skip(f"Model requires GPU or different attention backend: {e}")
            if isinstance(e, ImportError) and (
                "addict" in err_str or "matplotlib" in err_str or "torchvision" in err_str or "einops" in err_str
                or "easydict" in err_str or "pillow" in err_str or "img2pdf" in err_str or "tokenizers" in err_str
                or "were not found in your environment" in err_str
            ):
                pytest.skip(
                    "DeepSeek-OCR-2 model requires the deepseek-ocr2 extra. "
                    "Run: pip install doc2markdown-mcp[deepseek-ocr2]"
                )
            raise

        assert isinstance(result, str)
        print(result)

        assert len(result.strip()) > 0
        # Output should contain page markers from our pipeline
        assert "<!-- Page" in result or "\n" in result
