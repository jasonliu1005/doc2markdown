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

Base only (MarkItDown conversion; no DeepSeek-OCR-2):

```bash
pip install git+https://github.com/yourusername/doc2markdown.git
```

With DeepSeek-OCR-2 (model-based image PDF conversion):

```bash
pip install "git+https://github.com/yourusername/doc2markdown.git#egg=doc2markdown-mcp[deepseek-ocr2]"
```

### Option 3: Install from source

```bash
git clone https://github.com/yourusername/doc2markdown.git
cd doc2markdown
pip install .
```

### Model-based conversion (DeepSeek-OCR-2)

For image-based PDF conversion with the DeepSeek-OCR-2 model, install the **deepseek-ocr2** extra:

```bash
pip install doc2markdown-mcp[deepseek-ocr2]
```

Or from source:

```bash
pip install -e ".[deepseek-ocr2]"
```

This pulls in PyTorch, Transformers, PyMuPDF, tokenizers, and the model’s other dependencies. Without this extra, PDFs are converted with MarkItDown only (no local OCR model).

**CUDA (optional)**  
For GPU inference with CUDA 11.8, install PyTorch from the official index first, then the extra:

```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118
pip install doc2markdown-mcp[deepseek-ocr2]
```

**Flash Attention (optional, Linux/CUDA only)**  
Faster inference when Flash Attention is available. Install after the above (requires build tools):

```bash
pip install flash-attn==2.7.3 --no-build-isolation
```

If `flash-attn` is not installed or fails to load, the code falls back to eager attention. This project uses **transformers** for the model (not vLLM), so the vLLM wheel is not required.

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

The server runs over **HTTP** by default. Start it once (e.g. in a terminal or as a service), then add to `~/.cursor/mcp.json` using **type + url** (same style as other HTTP MCP servers):

```json
{
  "mcpServers": {
    "doc2markdown": {
      "type": "http",
      "url": "http://127.0.0.1:9000/mcp"
    }
  }
}
```

Start the server before using Cursor:

```bash
doc2markdown
# or with model-based conversion (OCR for image PDFs):
doc2markdown --model-based-conversion --port 9000
```

Use a different port if needed (e.g. `doc2markdown --port 9000`), then set `"url": "http://127.0.0.1:9000/mcp"` in mcp.json.

**Alternative — stdio (subprocess):** If you prefer Cursor to start the server as a subprocess over stdio:

```json
{
  "mcpServers": {
    "doc2markdown": {
      "command": "doc2markdown",
      "args": ["--stdio"]
    }
  }
}
```

If using a venv, use the full path to the executable in `"command"`.

## Usage

Once configured, you can use the tool in your MCP-compatible client:

> "Convert the document at /path/to/document.docx to markdown"

### Available Tools

#### convert_to_markdown

Converts a document file to Markdown format.

**Parameters:**
- `file_path` (string, required): The absolute or relative path to the document file to convert.

## CLI tool (document → Markdown to stdout)

After installing the package, the **`doc2markdown-convert`** command converts a document to Markdown and prints to stdout:

```bash
doc2markdown-convert path/to/document.pdf

# Use OCR for image-based PDFs
doc2markdown-convert path/to/scanned.pdf --model-based-conversion
```

Supports the same formats as the MCP tool. Set `DOC2MARKDOWN_MODEL_BASED_CONVERSION=true` to enable model-based conversion without the flag.

**From repo (without installing):** `python scripts/debug_convert.py <path> [--model-based-conversion]`

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
│       ├── server.py           # MCP server implementation
│       └── deepseek_v2_ocr.py  # Model-based PDF conversion (image PDFs)
├── tests/
│   ├── test_server.py         # MCP server tests
│   ├── test_deepseek_ocr.py    # OCR / image-PDF detection tests
│   └── fixtures/               # Optional: scanned PDF for image-PDF tests
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Development Setup

```bash
git clone https://github.com/yourusername/doc2markdown.git
cd doc2markdown
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -e .
pip install pytest pypdf    # for running tests
```

### Running Tests

Use the project’s virtual environment so all dependencies (including `fastmcp`, `markitdown`) are available:

```bash
source .venv/bin/activate   # or: .venv\Scripts\activate on Windows
```

**Option 1: Server tests (async)**

```bash
python tests/test_server.py
```

**Option 2: All tests with pytest**

```bash
pip install pytest pypdf   # if not already in venv
python -m pytest tests/ -v
```

**Run specific test files:**

```bash
python -m pytest tests/test_server.py -v
python -m pytest tests/test_deepseek_ocr.py -v
```

If you don’t activate the venv, run pytest with the venv’s Python explicitly:

```bash
.venv/bin/python -m pytest tests/ -v
```

**Integration test (real model on fixture PDF):** With a scanned PDF at `tests/fixtures/scanned.pdf` (or `scanned_or_image.pdf`), run the actual OCR pipeline test:

```bash
python -m pytest tests/test_deepseek_ocr.py -m integration -v
```

Skip integration tests in quick runs: `python -m pytest -m "not integration" -v`.

## License

MIT License
