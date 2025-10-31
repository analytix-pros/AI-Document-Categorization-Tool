"""OCR processing helper that uses only available models."""
import streamlit as st
from initial_setup.system_checker import check_ocr_dependencies


def get_available_ocr_models():
    """
    Get list of available OCR models on the system.
    
    Returns:
        list: Names of available OCR models (e.g., ['Tesseract', 'EasyOCR'])
    """
    ocr_status = check_ocr_dependencies()
    return ocr_status.get('available_models', [])


def process_document_with_available_ocr(document_path, preferred_model=None):
    """
    Process document using available OCR models.
    
    Args:
        document_path: Path to document to process
        preferred_model: Preferred OCR model name (optional)
        
    Returns:
        dict: {'success': bool, 'text': str, 'model_used': str, 'error': str}
    """
    available_models = get_available_ocr_models()
    
    if not available_models:
        return {
            'success': False,
            'text': None,
            'model_used': None,
            'error': 'No OCR models available on this system'
        }
    
    # Try preferred model first if specified and available
    models_to_try = []
    if preferred_model and preferred_model in available_models:
        models_to_try.append(preferred_model)
        models_to_try.extend([m for m in available_models if m != preferred_model])
    else:
        models_to_try = available_models
    
    # Try each available model
    for model_name in models_to_try:
        try:
            if model_name == 'Tesseract':
                result = process_with_tesseract(document_path)
            elif model_name == 'EasyOCR':
                result = process_with_easyocr(document_path)
            elif model_name == 'PaddleOCR':
                result = process_with_paddleocr(document_path)
            else:
                continue
            
            if result['success']:
                return result
        except Exception as e:
            # Log error but continue to next model
            print(f"Error with {model_name}: {str(e)}")
            continue
    
    return {
        'success': False,
        'text': None,
        'model_used': None,
        'error': f'All available OCR models failed. Tried: {", ".join(models_to_try)}'
    }


def process_with_tesseract(document_path):
    """Process document with Tesseract."""
    try:
        import pytesseract
        from PIL import Image
        import pypdfium2 as pdfium
        
        # Handle PDF or image
        if document_path.lower().endswith('.pdf'):
            # Use pypdfium2 to convert PDF pages to images
            pdf = pdfium.PdfDocument(document_path)
            texts = []
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                bitmap = page.render(scale=2.0)  # 2x scale for better quality
                pil_image = bitmap.to_pil()
                texts.append(pytesseract.image_to_string(pil_image))
                page.close()
            pdf.close()
            text = '\n\n'.join(texts)
        else:
            image = Image.open(document_path)
            text = pytesseract.image_to_string(image)
        
        return {
            'success': True,
            'text': text,
            'model_used': 'Tesseract',
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'text': None,
            'model_used': 'Tesseract',
            'error': str(e)
        }


def process_with_easyocr(document_path):
    """Process document with EasyOCR."""
    try:
        import easyocr
        
        reader = easyocr.Reader(['en'])
        result = reader.readtext(document_path)
        text = '\n'.join([item[1] for item in result])
        
        return {
            'success': True,
            'text': text,
            'model_used': 'EasyOCR',
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'text': None,
            'model_used': 'EasyOCR',
            'error': str(e)
        }


def process_with_paddleocr(document_path):
    """Process document with PaddleOCR."""
    try:
        from paddleocr import PaddleOCR
        
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(document_path, cls=True)
        
        text_lines = []
        for line in result:
            for word_info in line:
                text_lines.append(word_info[1][0])
        
        text = '\n'.join(text_lines)
        
        return {
            'success': True,
            'text': text,
            'model_used': 'PaddleOCR',
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'text': None,
            'model_used': 'PaddleOCR',
            'error': str(e)
        }


def display_available_ocr_status():
    """Display status of available OCR models in Streamlit."""
    available = get_available_ocr_models()
    
    if not available:
        st.error("⚠️ No OCR models available")
        st.info("Please install at least one OCR model from the sidebar")
        return False
    
    if len(available) < 3:
        st.info(f"ℹ️ Using available OCR models: {', '.join(available)}")
    else:
        st.success(f"✅ All OCR models available: {', '.join(available)}")
    
    return True


def example_usage():
    """Example of how to use this module."""
    # Get available models
    available = get_available_ocr_models()
    print(f"Available OCR models: {available}")
    
    # Process a document (will automatically use available models)
    result = process_document_with_available_ocr('/path/to/document.pdf')
    
    if result['success']:
        print(f"OCR successful using {result['model_used']}")
        print(f"Extracted text: {result['text'][:100]}...")
    else:
        print(f"OCR failed: {result['error']}")