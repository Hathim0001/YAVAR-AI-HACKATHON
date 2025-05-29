import pytesseract

def extract_text_with_confidence(image):
    """Extract text and average confidence score from an image using Tesseract."""
    text = pytesseract.image_to_string(image)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    confidences = [float(conf) for conf in data["conf"] if int(conf) > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    return text, avg_confidence