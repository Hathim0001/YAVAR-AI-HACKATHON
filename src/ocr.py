import pytesseract
from PIL import Image
import numpy as np
from pytesseract import Output

def extract_text_with_positions(image):
    try:
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        data = pytesseract.image_to_data(
            pil_image, 
            output_type=Output.DICT,
            config='--psm 6'
        )
        
        elements = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 60:
                text = data['text'][i].strip()
                x = data['left'][i]
                y = data['top'][i]
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
