"""OCR processing utilities for document analysis."""
import json
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from database.db_models import create_connection


def get_active_ocr_models():
    """Retrieve active OCR models from database with their settings."""
    conn = create_connection()
    query = """
        SELECT ocr_models_uuid, name, default_language, default_dpi, max_pages
        FROM ocr_models
        WHERE is_active = 1
        ORDER BY name
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    models = []
    for row in rows:
        models.append({
            'uuid': row[0],
            'name': row[1],
            'language': row[2],
            'dpi': row[3],
            'max_pages': row[4]
        })
    
    return models


def extract_text_from_pdf_by_page(pdf_bytes, ocr_model_name, dpi=300, max_pages=None):
    """
    Extract text from PDF page by page using specified OCR model.
    
    Args:
        pdf_bytes: PDF file as bytes
        ocr_model_name: Name of OCR model ('Tesseract', 'EasyOCR', 'PaddleOCR')
        dpi: DPI for image conversion
        max_pages: Maximum number of pages to process (None for all)
        
    Returns:
        str: Formatted text with page markers
    """
    # Convert PDF to images
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    
    # Limit pages if specified
    if max_pages:
        images = images[:max_pages]
    
    total_pages = len(images)
    extracted_text_parts = []
    
    for page_num, image in enumerate(images, start=1):
        # Add page marker
        page_header = f"(Page {page_num} of {total_pages})"
        
        # Extract text based on OCR model
        if ocr_model_name.lower() == 'tesseract':
            page_text = extract_with_tesseract(image)
        elif ocr_model_name.lower() == 'easyocr':
            page_text = extract_with_easyocr(image)
        elif ocr_model_name.lower() == 'paddleocr':
            page_text = extract_with_paddleocr(image)
        else:
            page_text = f"[Unsupported OCR model: {ocr_model_name}]"
        
        # Combine page header with extracted text
        extracted_text_parts.append(f"{page_header}\n{page_text.strip()}\n")
    
    return "\n".join(extracted_text_parts)


def extract_with_tesseract(image):
    """Extract text from image using Tesseract."""
    try:
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        return f"[Tesseract extraction error: {str(e)}]"


def extract_with_easyocr(image):
    """Extract text from image using EasyOCR."""
    try:
        import easyocr
        import numpy as np
        
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        
        # Initialize reader (cache for efficiency)
        if not hasattr(extract_with_easyocr, 'reader'):
            extract_with_easyocr.reader = easyocr.Reader(['en'])
        
        result = extract_with_easyocr.reader.readtext(img_array)
        text = '\n'.join([item[1] for item in result])
        return text
    except Exception as e:
        return f"[EasyOCR extraction error: {str(e)}]"


def extract_with_paddleocr(image):
    """Extract text from image using PaddleOCR."""
    try:
        from paddleocr import PaddleOCR
        import numpy as np
        
        # Convert PIL Image to numpy array
        img_array = np.array(image)
        
        # Initialize OCR (cache for efficiency)
        if not hasattr(extract_with_paddleocr, 'ocr'):
            extract_with_paddleocr.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        
        result = extract_with_paddleocr.ocr.ocr(img_array, cls=True)
        
        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) > 1:
                    text_lines.append(line[1][0])
        
        text = '\n'.join(text_lines)
        return text
    except Exception as e:
        return f"[PaddleOCR extraction error: {str(e)}]"


def process_document_with_all_ocr_models(pdf_bytes):
    """
    Process a PDF document with all active OCR models.
    
    Args:
        pdf_bytes: PDF file as bytes
        
    Returns:
        dict: {ocr_model_name: extracted_text}
    """
    ocr_models = get_active_ocr_models()
    ocr_results = {}
    
    for model in ocr_models:
        try:
            extracted_text = extract_text_from_pdf_by_page(
                pdf_bytes,
                model['name'],
                dpi=model['dpi'],
                max_pages=model['max_pages']
            )
            ocr_results[model['name']] = extracted_text
        except Exception as e:
            ocr_results[model['name']] = f"[Error processing with {model['name']}: {str(e)}]"
    
    return ocr_results