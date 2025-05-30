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
        data = pytesseract.image_to_data(pil_image, output_type=Output.DICT, config='--psm 6')
        elements = []
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 50:
                text = data['text'][i].strip()
                x = data['left'][i]
                y = data['top'][i]
                if text and x is not None and y is not None and isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    element = {'text': text, 'x': int(x), 'y': int(y), 'width': data['width'][i], 'height': data['height'][i], 'confidence': float(data['conf'][i]) / 100.0}
                    elements.append(element)
        return elements
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return []

def detect_seal_signature(image, output_dir, pdf_name, ocr_elements=None):
    try:
        if isinstance(image, Image.Image):
            image = np.array(image)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        if ocr_elements:
            mask = np.ones_like(thresh) * 255
            for elem in ocr_elements:
                x, y, w, h = elem['x'], elem['y'], elem['width'], elem['height']
                cv2.rectangle(mask, (x, y), (x + w, y + h), 0, -1)
            kernel = np.ones((10, 10), np.uint8)
            mask = cv2.dilate(mask, kernel, iterations=2)
            thresh = cv2.bitwise_and(thresh, mask)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        red_lower1 = np.array([0, 70, 50])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([170, 70, 50])
        red_upper2 = np.array([180, 255, 255])
        blue_lower = np.array([100, 50, 50])
        blue_upper = np.array([140, 255, 255])
        red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
        red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
        blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
        color_mask = cv2.bitwise_or(red_mask1, red_mask2)
        color_mask = cv2.bitwise_or(color_mask, blue_mask)
        combined_thresh = cv2.bitwise_or(thresh, color_mask)
        kernel = np.ones((5, 5), np.uint8)
        combined_thresh = cv2.morphologyEx(combined_thresh, cv2.MORPH_CLOSE, kernel)
        height, width = gray.shape
        contours, _ = cv2.findContours(combined_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        max_area = height * width * 0.15
        min_area = 300
        largest_element = None
        largest_area = 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if min_area < area < max_area and area > largest_area:
                largest_area = area
                largest_element = {'x': x, 'y': y, 'width': w, 'height': h}
        if largest_element:
            x, y, w, h = largest_element['x'], largest_element['y'], largest_element['width'], largest_element['height']
            element_image = image[y:y + h, x:x + w]
            output_path = os.path.join(output_dir, f"{pdf_name}_seal_signature.png")
            cv2.imwrite(output_path, element_image)
            return True, output_path
        return False, None
    except Exception as e:
        print(f"Seal/Signature Detection Error: {str(e)}")
        return False, None