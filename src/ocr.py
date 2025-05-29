import pytesseract

def extract_text_with_confidence(image):
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    text = " ".join(word for word in data["text"] if word.strip())
    confidences = [float(conf) for conf in data["conf"] if conf != "-1"]
    return text, confidences