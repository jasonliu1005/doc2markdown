#!/usr/bin/env python3
"""
Run the doc2markdown-convert CLI from the repo without installing the package.

Usage (from repo root):
  python scripts/debug_convert.py <path_to_document>
  python scripts/debug_convert.py <path> --model-based-conversion

After installing the package, use the installed command instead:
  doc2markdown-convert <path>
  doc2markdown-convert <path> --model-based-conversion
"""

import sys
from pathlib import Path

# Allow running from repo root without installing
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from doc2markdown.convert_cli import main

if __name__ == "__main__":
    main()
