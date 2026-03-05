"""
CLI to convert a document to Markdown and print to stdout.

Available after install as: doc2markdown-convert
"""

import argparse
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="doc2markdown-convert",
        description="Convert a document to Markdown and print to stdout.",
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

    # Import after setting env so server's MODEL_BASED_CONVERSION sees it
    from doc2markdown.server import _convert_to_markdown_sync

    result = _convert_to_markdown_sync(args.file_path)
    print(result, end="" if result.endswith("\n") else "\n")


if __name__ == "__main__":
    main()
    sys.exit(0)
