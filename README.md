# doc2markdown MCP Server

An MCP (Model Context Protocol) server that converts various document formats to Markdown. Supports DOC/DOCX, PDF, PPTX, and more using the MarkItDown library.

## Features

- **convert_to_markdown**: Converts document files to Markdown format
  - Supports: `.doc`, `.docx`, `.pdf`, `.pptx`, `.xlsx`, `.html`, `.txt`, `.rtf`
  - Returns clean Markdown text

## Installation

### Option 1: Install from PyPI (recommended)

```bash
pip install doc2markdown-mcp
```

### Option 2: Install from GitHub

```bash
pip install git+https://github.com/yourusername/doc2markdown.git
```

### Option 3: Install from source

```bash
git clone https://github.com/yourusername/doc2markdown.git
cd doc2markdown
pip install .
```

## Configuration

After installation, configure your MCP client to use the server.

### Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "doc2markdown": {
      "command": "doc2markdown"
    }
  }
}
```

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "doc2markdown": {
      "command": "doc2markdown"
    }
  }
}
```

**Note**: If you installed in a virtual environment, use the full path:

```json
{
  "mcpServers": {
    "doc2markdown": {
      "command": "/path/to/your/venv/bin/doc2markdown"
    }
  }
}
```

## Usage

Once configured, you can use the tool in your MCP-compatible client:

> "Convert the document at /path/to/document.docx to markdown"

### Available Tools

#### convert_to_markdown

Converts a document file to Markdown format.

**Parameters:**
- `file_path` (string, required): The absolute or relative path to the document file to convert.

## Supported Formats

| Format | Extension | Support Level |
|--------|-----------|---------------|
| Microsoft Word | `.doc`, `.docx` | ✅ Full |
| PDF | `.pdf` | ✅ Full |
| PowerPoint | `.pptx` | ✅ Full |
| Excel | `.xlsx` | ✅ Full |
| HTML | `.html`, `.htm` | ✅ Full |
| Plain Text | `.txt` | ✅ Full |
| Markdown | `.md` | ✅ Full |
| Rich Text | `.rtf` | ✅ Full |

## Development

### Project Structure

```
doc2markdown/
├── src/
│   └── doc2markdown/
│       ├── __init__.py
│       └── server.py      # Main MCP server implementation
├── tests/
│   └── test_server.py     # Test script
├── pyproject.toml         # Package configuration
├── requirements.txt       # Development dependencies
└── README.md
```

### Development Setup

```bash
git clone https://github.com/yourusername/doc2markdown.git
cd doc2markdown
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Running Tests

```bash
python tests/test_server.py
```

## License

MIT License
