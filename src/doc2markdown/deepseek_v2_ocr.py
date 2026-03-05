"""
DeepSeek-OCR-2 based conversion of image PDFs to Markdown.

Provides is_image_pdf() to detect image-based PDFs and pdf_to_markdown_with_ocr()
to convert them to markdown. Optional dependency: torch, transformers, pymupdf.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

MODEL_NAME = "deepseek-ai/DeepSeek-OCR-2"
MD_PROMPT = "<image>\n<|grounding|>Convert the document to markdown. "

# Minimum average characters per page to consider PDF as text-based (not image)
MIN_CHARS_PER_PAGE = 50

# Cached model and tokenizer, loaded once on first use (lazy init)
_cached_tokenizer = None
_cached_model = None
_cached_device: str | None = None


def is_image_pdf(pdf_path: str | Path) -> bool:
    """
    Detect if a PDF is image-based (e.g. scanned) by checking extractable text length.

    Uses pypdf to extract text. If the average number of characters per page
    is below MIN_CHARS_PER_PAGE, the PDF is considered image-based.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        True if the PDF appears to be image-based, False otherwise.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        # If pypdf not installed, assume text-based and let MarkItDown handle it
        return False

    path = Path(pdf_path)
    if not path.exists() or not path.suffix.lower() == ".pdf":
        return False

    try:
        reader = PdfReader(str(path))
        num_pages = len(reader.pages)
        if num_pages == 0:
            return False
        total_chars = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            total_chars += len(text.strip())
        avg_chars = total_chars / num_pages
        return avg_chars < MIN_CHARS_PER_PAGE
    except Exception:
        return False


def sanitize_markdown(md: str) -> str:
    """Light cleanup; keep minimal to avoid damaging tables/math/layout."""
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    md = re.sub(r"[ \t]+\n", "\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def _render_pdf_to_images(pdf_path: str, out_dir: Path, dpi: int = 220) -> list[Path]:
    import fitz  # PyMuPDF – no system deps (e.g. Poppler) required

    out_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []
    doc = fitz.open(pdf_path)
    try:
        for i in range(len(doc)):
            page = doc[i]
            pix = page.get_pixmap(dpi=dpi)
            p = out_dir / f"page_{i + 1:04d}.png"
            pix.save(str(p))
            image_paths.append(p)
    finally:
        doc.close()
    return image_paths


def _stub_llama_flash_attention_if_missing():
    """Stub LlamaFlashAttention2 so DeepSeek-OCR-2's custom code can import it (transformers 4.51+ removed it)."""
    import transformers.models.llama.modeling_llama as llama_mod
    if getattr(llama_mod, "LlamaFlashAttention2", None) is not None:
        return
    try:
        LlamaAttention = getattr(llama_mod, "LlamaAttention")
        llama_mod.LlamaFlashAttention2 = LlamaAttention
    except AttributeError:
        pass


def _load_model(device: str):
    """Load tokenizer and model (used internally by get_ocr_model)."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    _stub_llama_flash_attention_if_missing()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True, use_fast=False)

    # Prefer flash_attention_2 on CUDA when available; fall back to eager on failure
    # (e.g. LlamaFlashAttention2 missing in transformers 4.51+).
    if device == "cuda":
        try:
            model = AutoModel.from_pretrained(
                MODEL_NAME,
                trust_remote_code=True,
                use_safetensors=True,
                _attn_implementation="flash_attention_2",
            )
        except (ImportError, AttributeError, TypeError) as e:
            if "LlamaFlashAttention2" in str(e) or "flash" in str(e).lower():
                model = AutoModel.from_pretrained(
                    MODEL_NAME,
                    trust_remote_code=True,
                    use_safetensors=True,
                    _attn_implementation="eager",
                )
            else:
                raise
    else:
        model = AutoModel.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True,
            use_safetensors=True,
            _attn_implementation="eager",
        )

    if device == "cuda":
        model = model.eval().cuda().to(torch.bfloat16)
    elif device == "mps" and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        model = model.eval().to("mps")
    else:
        model = model.eval()
    return tokenizer, model


def get_ocr_model(device: str = "cuda"):
    """
    Return the cached OCR tokenizer and model, loading them once on first call.
    Subsequent calls reuse the same model (device from first call is used).
    """
    global _cached_tokenizer, _cached_model, _cached_device
    if _cached_model is not None:
        return _cached_tokenizer, _cached_model
    _cached_tokenizer, _cached_model = _load_model(device)
    _cached_device = device
    return _cached_tokenizer, _cached_model


def _ocr_image_to_markdown(tokenizer, model, image_file: str, work_dir: str) -> str:
    import torch

    with torch.inference_mode():
        res = model.infer(
            tokenizer,
            prompt=MD_PROMPT,
            image_file=image_file,
            output_path=work_dir,
            base_size=1024,
            image_size=768,
            crop_mode=True,
            save_results=False,
        )
    if isinstance(res, str):
        return res
    if isinstance(res, dict):
        for k in ("text", "markdown", "result", "output"):
            if k in res and isinstance(res[k], str):
                return res[k]
    return str(res)


def _resolve_device(device: str) -> str:
    """If device is 'cuda' but CUDA is not available, fall back to mps or cpu."""
    if device != "cuda":
        return device
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def pdf_to_markdown_with_ocr(
    pdf_path: str | Path,
    *,
    dpi: int = 220,
    device: str = "cuda",
    tmp_dir: str | Path | None = None,
    keep_tmp: bool = False,
) -> str:
    """
    Convert an image-based PDF to Markdown using DeepSeek-OCR-2.

    Renders each page to an image, runs OCR, and concatenates results
    with page comments.

    Args:
        pdf_path: Path to the PDF file.
        dpi: DPI for rendering PDF pages to images.
        device: "cuda", "mps", or "cpu". If "cuda" and CUDA is not available, uses mps/cpu.
        tmp_dir: Optional directory for temporary files; created automatically if None.
        keep_tmp: If True, do not delete tmp_dir after conversion.

    Returns:
        Markdown string.

    Raises:
        ImportError: If torch, transformers, or pymupdf are not installed.
        RuntimeError: On conversion errors.
    """
    from tqdm import tqdm

    device = _resolve_device(device)
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    cleanup_tmp = tmp_dir is None
    if tmp_dir is None:
        import tempfile
        tmp_dir = Path(tempfile.mkdtemp(prefix="doc2markdown_ocr_"))
    else:
        tmp_dir = Path(tmp_dir)
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

    img_dir = tmp_dir / "pages"
    work_dir = tmp_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        image_paths = _render_pdf_to_images(str(pdf_path), img_dir, dpi=dpi)
        tokenizer, model = get_ocr_model(device)

        parts = []
        for idx, img_path in enumerate(tqdm(image_paths, desc="OCR pages"), start=1):
            md = _ocr_image_to_markdown(
                tokenizer, model, str(img_path), str(work_dir)
            )
            md = sanitize_markdown(md)
            parts.append(f"\n\n<!-- Page {idx} -->\n\n{md}")

        result = "".join(parts).lstrip()
        return result
    finally:
        if cleanup_tmp and not keep_tmp and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> None:
    """CLI entrypoint for PDF -> Markdown via DeepSeek-OCR-2."""
    import argparse

    ap = argparse.ArgumentParser(
        description="Convert image PDF to Markdown using DeepSeek-OCR-2"
    )
    ap.add_argument("--pdf", required=True, help="Input PDF path")
    ap.add_argument("--out_md", required=True, help="Output Markdown path")
    ap.add_argument("--tmp_dir", default="./_tmp_ocr2", help="Temp working directory")
    ap.add_argument("--dpi", type=int, default=220, help="PDF render DPI")
    ap.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    args = ap.parse_args()

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    markdown = pdf_to_markdown_with_ocr(
        args.pdf,
        dpi=args.dpi,
        device=args.device,
        tmp_dir=Path(args.tmp_dir),
        keep_tmp=True,
    )
    out_md.write_text(markdown, encoding="utf-8")
    print(f"Wrote Markdown to: {out_md}")


if __name__ == "__main__":
    main()
