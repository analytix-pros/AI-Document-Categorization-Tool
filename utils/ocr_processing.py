"""OCR processing helper - returns JSON for every model (available or not)."""

import os
import sys
import json
import streamlit as st
from PIL import Image
from typing import List, Union

# Ensure project root is in path
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import FULL_DATABASE_FILE_PATH
from initial_setup.system_checker import check_ocr_dependencies
from initial_setup.poppler_installer import install_poppler


print(f"Current Directory: {os.getcwd()}")
pdf_path = os.path.join("utils", "65474 BK Discharged.pdf")  # ← SAMPLE PDF


# --------------------------------------------------------------
# Get available OCR models from initial_setup.system_checker
# --------------------------------------------------------------
def get_available_ocr_models() -> List[str]:
    """Get list of available OCR models on the system."""
    ocr_status = check_ocr_dependencies()
    print(f"[DEBUG] OCR Status: {ocr_status}")
    return ocr_status.get('available_models', [])


# --------------------------------------------------------------
# Helper: Split text into non-empty lines (exactly like fitz version)
# --------------------------------------------------------------
def _split_into_lines(text: str) -> List[str]:
    """
    Normalise any line-ending to '\\n' and return a list of non-empty,
    stripped lines - exactly the same behaviour as the fitz version.
    """
    return [
        line.strip()
        for line in text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
        if line.strip()
    ]


# --------------------------------------------------------------
# INTERNAL: Load PDF / image from path **or** bytes → list of PIL images
# --------------------------------------------------------------
def _load_pdf_or_image(document_input: Union[str, bytes]) -> List["Image.Image"]:
    """
    Accepts a file path (str) **or** raw PDF/image bytes.
    Returns a list of PIL.Image.Image (one per page for PDFs).
    """
    from PIL import Image
    import io
    import pypdfium2 as pdfium

    # ----- 1. Path (string) -------------------------------------------------
    if isinstance(document_input, str):
        if document_input.lower().endswith('.pdf'):
            pdf = pdfium.PdfDocument(document_input)
            images = []
            for i in range(len(pdf)):
                page = pdf[i]
                bitmap = page.render(scale=2.0)
                img = bitmap.to_pil()
                images.append(img)
                page.close()
            pdf.close()
            return images
        else:  # single image file
            return [Image.open(document_input)]

    # ----- 2. Bytes ---------------------------------------------------------
    if isinstance(document_input, (bytes, bytearray)):
        # Try to treat as PDF first
        try:
            pdf = pdfium.PdfDocument(document_input)
            images = []
            for i in range(len(pdf)):
                page = pdf[i]
                bitmap = page.render(scale=2.0)
                img = bitmap.to_pil()
                images.append(img)
                page.close()
            pdf.close()
            return images
        except Exception:  # not a PDF → treat as single image
            buf = io.BytesIO(document_input)
            return [Image.open(buf)]

    raise ValueError("document_input must be a path (str) or PDF/image bytes")


# --------------------------------------------------------------
# NEW: Convert PDF pages to PNG image bytes for database storage
# --------------------------------------------------------------
def convert_pdf_to_image_bytes(document_input: Union[str, bytes]) -> bytes:
    """
    Convert all pages of a PDF into a single PNG image stored as bytes.
    
    For multi-page PDFs, pages are stacked vertically with spacing.
    
    Parameters
    ----------
    document_input : str | bytes
        File system path or raw PDF bytes.
    
    Returns
    -------
    bytes
        PNG image bytes containing all PDF pages.
    """
    import io
    
    images = _load_pdf_or_image(document_input)
    
    if len(images) == 1:
        buf = io.BytesIO()
        images[0].save(buf, format='PNG')
        return buf.getvalue()
    
    # Multi-page: stack vertically with spacing
    spacing = 20
    widths = [img.width for img in images]
    heights = [img.height for img in images]
    
    max_width = max(widths)
    total_height = sum(heights) + spacing * (len(images) - 1)
    
    combined = Image.new('RGB', (max_width, total_height), 'white')
    
    y_offset = 0
    for img in images:
        x_offset = (max_width - img.width) // 2
        combined.paste(img, (x_offset, y_offset))
        y_offset += img.height + spacing
    
    buf = io.BytesIO()
    combined.save(buf, format='PNG')
    return buf.getvalue()


# --------------------------------------------------------------
# INTERNAL: Run OCR on images using the specified model
# --------------------------------------------------------------
def _extract_pages_safe(model_name: str, images: List["Image.Image"]) -> List[str]:
    """
    Extract text from images using the specified OCR model.
    Returns a list of strings (one per page).
    """
    import tempfile
    import shutil

    if model_name == "Tesseract":
        import pytesseract
        pages = []
        for img in images:
            text = pytesseract.image_to_string(img)
            pages.append(text)
        return pages

    elif model_name == "EasyOCR":
        import easyocr
        reader = easyocr.Reader(['en'])
        pages = []
        for img in images:
            tmp_dir = tempfile.mkdtemp()
            try:
                p = os.path.join(tmp_dir, "temp.png")
                img.save(p, "PNG")
                result = reader.readtext(p)
                lines = [word_info[1] for word_info in result]
                pages.append("\n".join(lines))
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
        return pages

    elif model_name == "PaddleOCR":
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        tmp_dir = tempfile.mkdtemp()
        img_paths = []
        try:
            for i, img in enumerate(images):
                p = os.path.join(tmp_dir, f"page_{i+1}.png")
                img.save(p, "PNG")
                img_paths.append(p)

            pages = []
            for p in img_paths:
                result = ocr.ocr(p, cls=True)
                lines = [word_info[1][0] for line in result for word_info in line]
                pages.append("\n".join(lines))
            return pages
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    else:
        raise ValueError(f"Unknown model: {model_name}")


# --------------------------------------------------------------
# 1. MAIN FUNCTION – only tries *installed* models
# --------------------------------------------------------------
def process_document_with_available_ocr(
    document_input: Union[str, bytes],
    preferred_model: str | None = None,
) -> str:
    """
    OCR a document using only the models that are actually installed.

    Parameters
    ----------
    document_input : str | bytes
        File system path **or** raw PDF/image bytes.
    preferred_model : str, optional
        Model to try first if it is available.

    Returns
    -------
    str
        JSON string with one entry per successful model.
    """
    install_poppler()
    available_models = get_available_ocr_models()
    if not available_models:
        return json.dumps({'error': 'No OCR models available on this system'})

    models_to_try = []
    if preferred_model and preferred_model in available_models:
        models_to_try.append(preferred_model)
        models_to_try.extend(m for m in available_models if m != preferred_model)
    else:
        models_to_try = available_models

    results = {}
    images = _load_pdf_or_image(document_input)

    for model_name in models_to_try:
        try:
            raw_pages = _extract_pages_safe(model_name, images)
            total = len(raw_pages)
            results[model_name] = {
                f"Page {i} out of {total}": "\n".join(_split_into_lines(page_text))
                for i, page_text in enumerate(raw_pages, start=1)
            }
        except Exception as e:
            print(f"[DEBUG] {model_name} failed: {e}")
            continue

    if not results:
        error_results = {'error': 'All available OCR models failed'}
        return error_results
    return results


# --------------------------------------------------------------
# 2. ALL models – tries all 3, skips missing ones
# --------------------------------------------------------------
def process_document_with_all_ocr_models(
    document_input: Union[str, bytes],
    preferred_model: str | None = None,
) -> str:
    """
    OCR a document trying **all** three models (Tesseract, EasyOCR, PaddleOCR).
    Missing dependencies are silently skipped.

    Parameters
    ----------
    document_input : str | bytes
        File system path **or** raw PDF/image bytes.
    preferred_model : str, optional
        Model to try first if it is listed.

    Returns
    -------
    str
        JSON string with one entry per successful model.
    """
    install_poppler()
    all_models = ["Tesseract", "EasyOCR", "PaddleOCR"]
    
    models_to_try = []
    if preferred_model and preferred_model in all_models:
        models_to_try.append(preferred_model)
        models_to_try.extend(m for m in all_models if m != preferred_model)
    else:
        models_to_try = all_models

    results = {}
    images = _load_pdf_or_image(document_input)

    for model_name in models_to_try:
        try:
            raw_pages = _extract_pages_safe(model_name, images)
            total = len(raw_pages)
            results[model_name] = {
                f"Page {i} out of {total}": "\n".join(_split_into_lines(page_text))
                for i, page_text in enumerate(raw_pages, start=1)
            }
        except Exception as e:
            print(f"[DEBUG] {model_name} skipped: {e}")
            continue

    if not results:
        error_results = {'error': 'All OCR models failed or are unavailable'}
        return error_results
    return results


# ————————————————————————————————————————————————————————————
# Streamlit UI
# ————————————————————————————————————————————————————————————
def display_available_ocr_status():
    available = get_available_ocr_models()
    if not available:
        st.error("Warning: No OCR models available")
        st.info("Install at least one OCR model from the sidebar")
        return False
    if len(available) < 3:
        st.info(f"Info: Using: {', '.join(available)}")
    else:
        st.success(f"Success: All models ready: {', '.join(available)}")
    return True


# ————————————————————————————————————————————————————————————
# QUICK TEST: Just pass a PDF → see real JSON with line breaks
# ————————————————————————————————————————————————————————————
if __name__ == "__main__":
    print("\n" + "="*60)
    print("OCR RESULT FOR:", pdf_path)
    print("="*60)

    # Example with a **path**
    result_path = process_document_with_available_ocr(pdf_path)
    print("\n" + "="*60)
    print("\n" + "="*60)
    print(type(result_path))
    print(json.dumps(result_path, indent=4, default=str))

    # # Example with **bytes** (read the same file)
    # with open(pdf_path, "rb") as f:
    #     pdf_bytes = f.read()
    # result_bytes = process_document_with_available_ocr(pdf_bytes)
    # print("\n" + "="*60)
    # print("\n" + "="*60)
    # print(type(result_bytes))
    # print("\n--- Bytes version (should be identical) ---")
    # print(json.dumps(result_bytes, indent=4, default=str))