"""Pluggable OCR. Driven entirely by the profile's `ocr:` block.

Supported engines:
  tesseract  — shells out to the `tesseract` binary (default)
  easyocr    — optional, requires `pip install archex[easyocr]`
"""
from __future__ import annotations

import os
import subprocess
import tempfile

from PIL import Image, ImageEnhance, ImageFilter


def _preprocess(img_path: str, cfg: dict) -> str:
    """Apply optional image cleanup before OCR. Returns a temp file path."""
    pre = cfg.get("preprocess", {}) or {}
    img = Image.open(img_path)

    if pre.get("grayscale", True):
        img = img.convert("L")
    if "contrast" in pre:
        img = ImageEnhance.Contrast(img).enhance(float(pre["contrast"]))
    if pre.get("sharpen"):
        img = img.filter(ImageFilter.SHARPEN)
    max_w = pre.get("max_width")
    if max_w and img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((int(max_w), int(img.height * ratio)), Image.LANCZOS)

    fd, tmp = tempfile.mkstemp(suffix=".png", prefix="archex_ocr_")
    os.close(fd)
    img.save(tmp)
    return tmp


def _tesseract(img_path: str, cfg: dict) -> str | None:
    lang = cfg.get("lang", "eng")
    psm = str(cfg.get("psm", 6))
    r = subprocess.run(
        ["tesseract", img_path, "stdout", "-l", lang, "--psm", psm],
        capture_output=True,
        timeout=cfg.get("timeout", 90),
    )
    text = r.stdout.decode("utf-8", errors="replace").strip()
    return text or None


_easyocr_reader = None


def _easyocr(img_path: str, cfg: dict) -> str | None:
    global _easyocr_reader
    try:
        import easyocr
    except ImportError as e:
        raise RuntimeError("easyocr not installed — `pip install archex[easyocr]`") from e
    if _easyocr_reader is None:
        langs = cfg.get("easyocr_langs") or [cfg.get("lang", "en")]
        _easyocr_reader = easyocr.Reader(langs, gpu=cfg.get("gpu", False))
    lines = _easyocr_reader.readtext(img_path, detail=0, paragraph=True)
    text = "\n".join(lines).strip()
    return text or None


def ocr_image(img_path: str, cfg: dict) -> str | None:
    """Run OCR on a single image per the profile's ocr config."""
    engine = cfg.get("engine", "tesseract")
    if engine == "tesseract":
        tmp = _preprocess(img_path, cfg)
        try:
            return _tesseract(tmp, cfg)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass
    elif engine == "easyocr":
        return _easyocr(img_path, cfg)
    raise ValueError(f"Unknown OCR engine: {engine}")
