import pytesseract

# Set the Tesseract executable path (adjust based on your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_with_confidence(image):
    """Extract text and confidence score using Tesseract OCR."""
    # Use PSM 6 for structured text and limit character set
    custom_config = r'--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-/,.'
    text = pytesseract.image_to_string(image, config=custom_config)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT, config=custom_config)
    confidences = [float(conf) for conf in data["conf"] if int(conf) > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    return text, avg_confidence