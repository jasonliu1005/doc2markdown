# doc2markdown MCP Server

An MCP (Model Context Protocol) server that converts various document formats to Markdown. Currently supports DOC/DOCX files using the MarkItDown library.

## Features

- **convert_to_markdown**: Converts document files to Markdown format
  - Supports: `.doc`, `.docx`, `.pdf`, `.pptx`, `.xlsx`, `.html`, `.txt`, `.rtf`
  - Returns clean Markdown text

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone or navigate to the project directory:

```bash
cd doc2markdown
```

2. Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Server

The server runs over stdio and is designed to be used with MCP-compatible clients like Claude Desktop.

```bash
python src/server.py
```

### Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "doc2markdown": {
      "command": "python",
      "args": ["/absolute/path/to/doc2markdown/src/server.py"],
      "env": {}
    }
  }
}
```

Or if using a virtual environment:

```json
{
  "mcpServers": {
    "doc2markdown": {
      "command": "/absolute/path/to/doc2markdown/.venv/bin/python",
      "args": ["/absolute/path/to/doc2markdown/src/server.py"],
      "env": {}
    }
  }
}
```

### Available Tools

#### convert_to_markdown

Converts a document file to Markdown format.

**Parameters:**
- `file_path` (string, required): The absolute or relative path to the document file to convert.

**Example usage in Claude:**
> "Convert the document at /path/to/document.docx to markdown"

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
│   └── server.py      # Main MCP server implementation
├── tests/
│   └── test_server.py # Test script
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

### Adding New Format Support

The MarkItDown library handles most common document formats. To add specialized handling for a new format:

1. Check if MarkItDown supports the format
2. Add the extension to the `supported_extensions` set in `src/server.py`
3. Add any format-specific error handling if needed

## License

MIT License

