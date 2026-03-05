#!/usr/bin/env python3
"""
Test script for the doc2markdown MCP server.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from doc2markdown.server import convert_to_markdown_async as convert_to_markdown, list_tools


@pytest.mark.asyncio
async def test_list_tools():
    """Test that tools are listed correctly."""
    print("Testing list_tools...")
    tools = await list_tools()
    assert len(tools) == 1
    assert tools[0].name == "convert_to_markdown"
    print("✓ list_tools passed")
    return True


@pytest.mark.asyncio
async def test_convert_text_file():
    """Test converting a simple text file."""
    print("\nTesting text file conversion...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("# Test Heading\n\nThis is a test paragraph.\n\n- Item 1\n- Item 2\n")
        temp_path = f.name
    
    try:
        result = await convert_to_markdown(temp_path)
        assert len(result) == 1
        assert "Test Heading" in result[0].text
        assert "test paragraph" in result[0].text
        print(f"✓ Text file conversion passed")
        print(f"  Result preview: {result[0].text[:100]}...")
    finally:
        os.unlink(temp_path)
    
    return True


@pytest.mark.asyncio
async def test_file_not_found():
    """Test handling of non-existent file."""
    print("\nTesting file not found handling...")
    
    result = await convert_to_markdown("/nonexistent/file.docx")
    assert len(result) == 1
    assert "Error" in result[0].text
    print("✓ File not found handling passed")
    return True


@pytest.mark.asyncio
async def test_empty_path():
    """Test handling of empty file path."""
    print("\nTesting empty path handling...")

    result = await convert_to_markdown("")
    assert len(result) == 1
    assert "Error" in result[0].text
    print("✓ Empty path handling passed")
    return True


@pytest.mark.asyncio
async def test_pdf_with_model_based_conversion_image_pdf():
    """When model_based_conversion is on and PDF is image-based, use OCR path (mocked)."""
    print("\nTesting PDF with model-based conversion (image PDF, mocked OCR)...")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 dummy\n")
        pdf_path = f.name
    try:
        import doc2markdown.server as server_module
        with (
            patch.object(server_module, "MODEL_BASED_CONVERSION", True),
            patch(
                "doc2markdown.deepseek_v2_ocr.is_image_pdf",
                return_value=True,
            ),
            patch(
                "doc2markdown.deepseek_v2_ocr.pdf_to_markdown_with_ocr",
                return_value="# OCR Result\n\nContent from DeepSeek-OCR.",
            ),
        ):
            result = await convert_to_markdown(pdf_path)
        assert len(result) == 1
        assert "OCR Result" in result[0].text
        assert "DeepSeek-OCR" in result[0].text
        print("✓ Model-based conversion (image PDF) passed")
    finally:
        os.unlink(pdf_path)
    return True


@pytest.mark.asyncio
async def test_pdf_with_model_based_conversion_text_pdf_fallback():
    """When model_based_conversion is on but PDF is text-based, use MarkItDown."""
    print("\nTesting PDF with model-based conversion (text PDF fallback)...")

    try:
        from pypdf import PdfWriter
        from pypdf import PageObject
    except ImportError:
        print("  (Skipped: pypdf not installed)")
        return True

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name
    try:
        writer = PdfWriter()
        page = PageObject.create_blank_page(None, 200, 200)
        writer.add_page(page)
        with open(pdf_path, "wb") as out:
            writer.write(out)

        import doc2markdown.server as server_module
        with (
            patch.object(server_module, "MODEL_BASED_CONVERSION", True),
            patch(
                "doc2markdown.deepseek_v2_ocr.is_image_pdf",
                return_value=False,
            ),
        ):
            result = await convert_to_markdown(pdf_path)
        # Should have used MarkItDown (may produce empty or minimal content for blank page)
        assert len(result) == 1
        assert "Error" not in result[0].text or "empty" in result[0].text.lower()
        print("✓ Model-based conversion (text PDF fallback) passed")
    finally:
        os.unlink(pdf_path)
    return True


@pytest.mark.asyncio
async def test_model_based_conversion_ocr_raises_returns_error():
    """When model_based is on and OCR raises, return error message."""
    print("\nTesting model-based conversion when OCR raises...")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4\n")
        pdf_path = f.name
    try:
        import doc2markdown.server as server_module
        with (
            patch.object(server_module, "MODEL_BASED_CONVERSION", True),
            patch(
                "doc2markdown.deepseek_v2_ocr.is_image_pdf",
                return_value=True,
            ),
            patch(
                "doc2markdown.deepseek_v2_ocr.pdf_to_markdown_with_ocr",
                side_effect=RuntimeError("CUDA out of memory"),
            ),
        ):
            result = await convert_to_markdown(pdf_path)
        assert len(result) == 1
        assert "Error" in result[0].text
        assert "CUDA" in result[0].text or "model" in result[0].text.lower()
        print("✓ OCR error handling passed")
    finally:
        os.unlink(pdf_path)
    return True


async def main():
    """Run all tests."""
    print("=" * 50)
    print("doc2markdown MCP Server Tests")
    print("=" * 50)
    
    tests = [
        test_list_tools,
        test_convert_text_file,
        test_file_not_found,
        test_empty_path,
        test_pdf_with_model_based_conversion_image_pdf,
        test_pdf_with_model_based_conversion_text_pdf_fallback,
        test_model_based_conversion_ocr_raises_returns_error,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

