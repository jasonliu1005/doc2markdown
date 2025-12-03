#!/usr/bin/env python3
"""
MCP Server for converting documents to Markdown format.

This server provides tools to convert various file formats (doc, docx, etc.)
to Markdown using the MarkItDown library.
"""

import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from markitdown import MarkItDown


# Initialize the MCP server
server = Server("doc2markdown")

# Initialize the MarkItDown converter
converter = MarkItDown()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="convert_to_markdown",
            description=(
                "Converts a document file to Markdown format. "
                "Supports doc, docx, and other document formats. "
                "Takes a file path as input and returns the document content as Markdown text."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The absolute or relative path to the document file to convert."
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "convert_to_markdown":
        return await convert_to_markdown(arguments.get("file_path", ""))
    else:
        raise ValueError(f"Unknown tool: {name}")


async def convert_to_markdown(file_path: str) -> list[TextContent]:
    """
    Convert a document file to Markdown format.
    
    Args:
        file_path: Path to the document file to convert.
        
    Returns:
        List containing the converted Markdown text.
    """
    if not file_path:
        return [TextContent(
            type="text",
            text="Error: No file path provided. Please specify a file path."
        )]
    
    # Resolve the path
    path = Path(file_path).expanduser().resolve()
    
    # Check if file exists
    if not path.exists():
        return [TextContent(
            type="text",
            text=f"Error: File not found: {path}"
        )]
    
    # Check if it's a file (not a directory)
    if not path.is_file():
        return [TextContent(
            type="text",
            text=f"Error: Path is not a file: {path}"
        )]
    
    # Get file extension for validation
    extension = path.suffix.lower()
    supported_extensions = {'.doc', '.docx', '.pdf', '.pptx', '.xlsx', '.html', '.htm', '.txt', '.md', '.rtf'}
    
    if extension not in supported_extensions:
        return [TextContent(
            type="text",
            text=f"Warning: File extension '{extension}' may not be fully supported. Attempting conversion anyway..."
        )]
    
    try:
        # Convert the document to Markdown
        result = converter.convert(str(path))
        
        # The result object has a text_content attribute
        markdown_content = result.text_content
        
        if not markdown_content or not markdown_content.strip():
            return [TextContent(
                type="text",
                text=f"Warning: The conversion produced empty content. The file may be empty or the format may not be supported: {path.name}"
            )]
        
        return [TextContent(
            type="text",
            text=markdown_content
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error converting file '{path.name}': {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

