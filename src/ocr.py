import pytesseract
from PIL import Image
import numpy as np
from pytesseract import Output
import cv2
import os

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

def detect_logo(image, output_dir, pdf_name):
    try:
        if isinstance(image, Image.Image):
            image = np.array(image)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        height, width = gray.shape
        top_height = int(height * 0.25)  # Increased to 25% for better coverage
        corner_width = int(width * 0.25)
        
        regions = [
            thresh[0:top_height, 0:corner_width],  # Top-left
            thresh[0:top_height, width - corner_width:width],  # Top-right
            thresh[0:top_height, int(width * 0.375):int(width * 0.625)]  # Top-center
        ]
        
        logo_detected = False
        logo_image = None
        output_path = None
        
        for idx, region in enumerate(regions):
            contours, _ = cv2.findContours(region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                if 2000 < area < (top_height * corner_width * 0.5):  # Adjusted area filter
                    if idx == 0:  # Top-left
                        logo_image = image[0:top_height, 0:corner_width][y:y+h, x:x+w]
                    elif idx == 1:  # Top-right
                        logo_image = image[0:top_height, width - corner_width:width][y:y+h, x:x+w]
                    else:  # Top-center
                        logo_image = image[0:top_height, int(width * 0.375):int(width * 0.625)][y:y+h, x:x+w]
                    
                    logo_detected = True
                    output_path = os.path.join(output_dir, f"{pdf_name}_logo.png")
                    cv2.imwrite(output_path, logo_image)
                    break
            if logo_detected:
                break
        
        return logo_detected, output_path if logo_detected else None

    except Exception as e:
        print(f"Logo Detection Error: {str(e)}")
        return False, None