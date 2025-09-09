"""Optional integration test that exercises real OCR if available.

This test only runs when both dependencies are importable AND the
environment variable RUN_REAL_OCR_TESTS is set to '1'.
This prevents CI from attempting heavyweight model downloads.
"""

import os
import asyncio
import tempfile
from pathlib import Path

import pytest


def _real_ocr_ready() -> bool:
    if os.environ.get("RUN_REAL_OCR_TESTS") != "1":
        return False
    try:
        import surya  # noqa: F401
        import fitz  # PyMuPDF  # noqa: F401
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _real_ocr_ready(),
    reason="Real OCR deps not available or RUN_REAL_OCR_TESTS!=1"
)


@pytest.mark.asyncio
async def test_real_ocr_smoke_extracts_some_text():
    """Smoke test: ensure extract_text returns a non-empty string when real OCR is enabled.

    Creates a tiny PNG with text; depending on model, OCR may or may not
    capture synthetic text perfectly. We assert only non-empty output to
    keep this test tolerant.
    """
    from PIL import Image, ImageDraw
    from app.services.ocr_service import extract_text

    # Create a small image with some text
    img = Image.new("RGB", (200, 80), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 30), "INV-TEST-001", fill=(0, 0, 0))

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img.save(tmp.name)
        tmp_path = Path(tmp.name)

    try:
        text = await extract_text(tmp_path)
        assert isinstance(text, str)
        assert len(text.strip()) > 0
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

