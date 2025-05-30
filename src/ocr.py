import pytesseract
from PIL import Image
import numpy as np
from pytesseract import Output

def extract_text_with_positions(image):
    """Extract text with positions using Tesseract OCR."""
    try:
        # Convert to PIL image if needed
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Run Tesseract with detailed output
        data = pytesseract.image_to_data(
            pil_image, 
            output_type=Output.DICT,
            config='--psm 6'  # Assume uniform block of text
        )
        
        elements = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 60:  # Filter low-confidence detections
                text = data['text'][i].strip()
                x = data['left'][i]
                y = data['top'][i]
                # Validate coordinates
                if text and x is not None and y is not None and isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    element = {
                        'text': text,
                        'x': int(x),
                        'y': int(y),
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': float(data['conf'][i]) / 100.0
                    }
                    elements.append(element)
        
        return elements

    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return []