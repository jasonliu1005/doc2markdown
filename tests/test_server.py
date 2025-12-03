#!/usr/bin/env python3
"""
Test script for the doc2markdown MCP server.
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doc2markdown.server import convert_to_markdown, list_tools


async def test_list_tools():
    """Test that tools are listed correctly."""
    print("Testing list_tools...")
    tools = await list_tools()
    assert len(tools) == 1
    assert tools[0].name == "convert_to_markdown"
    print("✓ list_tools passed")
    return True


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


async def test_file_not_found():
    """Test handling of non-existent file."""
    print("\nTesting file not found handling...")
    
    result = await convert_to_markdown("/nonexistent/file.docx")
    assert len(result) == 1
    assert "Error" in result[0].text
    print("✓ File not found handling passed")
    return True


async def test_empty_path():
    """Test handling of empty file path."""
    print("\nTesting empty path handling...")
    
    result = await convert_to_markdown("")
    assert len(result) == 1
    assert "Error" in result[0].text
    print("✓ Empty path handling passed")
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

