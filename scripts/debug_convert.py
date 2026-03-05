#!/usr/bin/env python3
"""
Debug script: convert any supported document to Markdown and print to stdout.

Usage:
  python scripts/debug_convert.py <path_to_document>
  python scripts/debug_convert.py <path> --model-based-conversion   # use OCR for image PDFs

Supports: .doc, .docx, .pdf, .pptx, .xlsx, .html, .htm, .txt, .md, .rtf

When --model-based-conversion is set (or DOC2MARKDOWN_MODEL_BASED_CONVERSION=true),
image-based PDFs are converted with DeepSeek-OCR-2 instead of MarkItDown.
"""

import argparse
import os
import sys
from pathlib import Path

# Allow running from repo root without installing the package
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

# Set model-based flag from CLI before importing server (server reads env/argv at import)
def main():
    parser = argparse.ArgumentParser(
        description="Convert a document to Markdown and print to stdout."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the document to convert (.doc, .docx, .pdf, .pptx, etc.)",
    )
    parser.add_argument(
        "--model-based-conversion",
        action="store_true",
        help="Use DeepSeek-OCR-2 for image-based PDFs (otherwise use MarkItDown for all PDFs)",
    )
    args = parser.parse_args()

    if args.model_based_conversion:
        os.environ["DOC2MARKDOWN_MODEL_BASED_CONVERSION"] = "true"

    from doc2markdown.server import _convert_to_markdown_sync

    result = _convert_to_markdown_sync(args.file_path)
    print(result, end="" if result.endswith("\n") else "\n")


if __name__ == "__main__":
    main()
