# Test fixtures

Optional fixture for image-based PDF tests:

- **`scanned_or_image.pdf`** (or `scanned.pdf`, `image_based.pdf`) – A real scanned or image-only PDF (no text layer, or very little extractable text).
  - **`test_actual_image_based_pdf_fixture`** – Asserts the fixture is detected as image-based. Skipped if no fixture exists.
  - **`test_actual_model_based_conversion_fixture`** (marker: `integration`) – Runs the real DeepSeek-OCR-2 pipeline on the fixture and checks that non-empty markdown is produced. Requires OCR deps (torch, transformers, pymupdf). Run with: `pytest tests/test_deepseek_ocr.py -m integration -v`. Exclude from quick runs: `pytest -m "not integration"`.
