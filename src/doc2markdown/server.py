#!/usr/bin/env python3
"""
MCP Server for converting documents to Markdown format.

This server provides tools to convert various file formats (doc, docx, etc.)
to Markdown using the MarkItDown library. When model-based conversion is
enabled, image-based PDFs are converted using the DeepSeek-OCR-2 model.

Runs over HTTP by default (host/port via env or args). Use --stdio for stdio transport.
"""

import os
import sys
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from markitdown import MarkItDown


def _parse_model_based_conversion() -> bool:
    """Read model_based_conversion from env or argv (for MCP client config)."""
    env_val = os.environ.get("DOC2MARKDOWN_MODEL_BASED_CONVERSION", "").lower()
    if env_val in ("1", "true", "yes"):
        return True
    if "--model-based-conversion" in sys.argv:
        return True
    return False


def _parse_http_host() -> str:
    """Host for HTTP server. Env DOC2MARKDOWN_HTTP_HOST or default 127.0.0.1."""
    return os.environ.get("DOC2MARKDOWN_HTTP_HOST", "127.0.0.1")


def _parse_http_port() -> int:
    """Port for HTTP server. Env DOC2MARKDOWN_HTTP_PORT or default 8000."""
    try:
        return int(os.environ.get("DOC2MARKDOWN_HTTP_PORT", "8000"))
    except ValueError:
        return 8000


# Model-based conversion: when True, image PDFs use DeepSeek-OCR-2
MODEL_BASED_CONVERSION = _parse_model_based_conversion()


@lifespan
async def _ocr_model_lifespan(server):
    """Load OCR model at server start when model-based conversion is enabled."""
    if not MODEL_BASED_CONVERSION:
        yield {}
        return
    try:
        import torch
        from doc2markdown.deepseek_v2_ocr import get_ocr_model
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
        get_ocr_model(device)
    except Exception:
        pass  # Defer failure to first conversion if deps missing
    yield {}


# Initialize FastMCP server (HTTP by default; lifespan loads OCR model at startup when flag is on)
mcp = FastMCP("doc2markdown", lifespan=_ocr_model_lifespan)

# Initialize the MarkItDown converter
converter = MarkItDown()


def _convert_to_markdown_sync(file_path: str) -> str:
    """
    Convert a document file to Markdown format (sync, returns plain string).
    Used by the MCP tool.
    """
    if not file_path:
        return "Error: No file path provided. Please specify a file path."

    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        return f"Error: File not found: {path}"

    if not path.is_file():
        return f"Error: Path is not a file: {path}"

    extension = path.suffix.lower()
    supported_extensions = {
        ".doc", ".docx", ".pdf", ".pptx", ".xlsx",
        ".html", ".htm", ".txt", ".md", ".rtf",
    }

    if extension not in supported_extensions:
        return (
            f"Warning: File extension '{extension}' may not be fully supported. "
            "Attempting conversion anyway..."
        )

    # Model-based conversion: for PDFs, use DeepSeek-OCR-2 when enabled and PDF is image-based
    if extension == ".pdf" and MODEL_BASED_CONVERSION:
        try:
            from doc2markdown.deepseek_v2_ocr import (
                is_image_pdf,
                pdf_to_markdown_with_ocr,
            )
        except ImportError as e:
            return (
                f"Error: Model-based conversion is enabled but OCR dependencies are not installed "
                f"(torch, transformers, pdf2image, pypdf). Install with: pip install torch transformers pdf2image pypdf. "
                f"Original error: {e}"
            )
        if is_image_pdf(path):
            try:
                markdown_content = pdf_to_markdown_with_ocr(str(path))
                if not markdown_content or not markdown_content.strip():
                    return f"Warning: Model-based conversion produced empty content for: {path.name}"
                return markdown_content
            except Exception as e:
                return f"Error converting image PDF '{path.name}' with model: {e}"
        # Fall through to MarkItDown for text-based PDFs

    try:
        result = converter.convert(str(path))
        markdown_content = result.text_content

        if not markdown_content or not markdown_content.strip():
            return (
                f"Warning: The conversion produced empty content. "
                f"The file may be empty or the format may not be supported: {path.name}"
            )

        return markdown_content

    except Exception as e:
        return f"Error converting file '{path.name}': {str(e)}"


@mcp.tool()
def convert_to_markdown(file_path: str) -> str:
    """
    Converts a document file to Markdown format.
    Supports doc, docx, PDF, pptx, xlsx, HTML, txt, and other document formats.
    Takes a file path as input and returns the document content as Markdown text.
    """
    return _convert_to_markdown_sync(file_path)


# --- Test compatibility: async list_tools and convert returning list[TextContent] ---
class _TextContent:
    __slots__ = ("type", "text")
    def __init__(self, type: str, text: str):
        self.type = type
        self.text = text


class _Tool:
    __slots__ = ("name", "description", "inputSchema")
    def __init__(self, name: str, description: str, inputSchema: dict):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema


async def list_tools():
    """Return tools in MCP format (for test compatibility)."""
    return [
        _Tool(
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


async def convert_to_markdown_async(file_path: str) -> list:
    """Async wrapper that returns list[TextContent] (for test compatibility)."""
    return [_TextContent(type="text", text=_convert_to_markdown_sync(file_path))]


def main() -> None:
    """Entry point for the CLI command. Uses HTTP transport unless --stdio is passed."""
    use_stdio = "--stdio" in sys.argv
    if use_stdio:
        mcp.run(transport="stdio")
    else:
        host = _parse_http_host()
        port = _parse_http_port()
        # Allow override via --host / --port in argv
        if "--host" in sys.argv:
            i = sys.argv.index("--host")
            if i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
        if "--port" in sys.argv:
            i = sys.argv.index("--port")
            if i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    pass
        mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
