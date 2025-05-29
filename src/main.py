import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from preprocess import preprocess_image
from ocr import extract_text_with_confidence
from parser import parse_invoice_data
from verification import perform_verifiability_checks
from output import save_outputs

# Define input and output directories (relative to src/)
input_dir = "../input_pdfs/"
output_dir = "../output/"

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Get list of PDF files
pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]

for pdf_file in pdf_files:
    # Step 1: Convert PDF to images
    pdf_path = os.path.join(input_dir, pdf_file)
    images = convert_pdf_to_images(pdf_path)

    # Step 2: Preprocess images
    preprocessed_images = [preprocess_image(img) for img in images]

    # Step 3: Extract text and confidence scores using OCR
    extracted_data = [extract_text_with_confidence(img) for img in preprocessed_images]

    # Step 4: Parse extracted text into structured invoice data
    invoice_data = parse_invoice_data(extracted_data)

    # Step 5: Detect seal and signature
    seal_signature_img = detect_seal_signature(images)
    base_name = os.path.splitext(pdf_file)[0]
    if seal_signature_img is not None:
        invoice_data["seal_and_sign_present"] = True
        save_seal_signature(seal_signature```python
        save_seal_signature(seal_signature_img, output_dir, base_name)
    else:
        invoice_data["seal_and_sign_present"] = False

    # Step 6: Perform verifiability checks
    verifiability_report = perform_verifiability_checks(invoice_data, extracted_data)

    # Step 7: Save outputs with unique filenames
    save_outputs(invoice_data, verifiability_report, output_dir, base_name)

def convert_pdf_to_images(pdf_path):
    """Convert PDF pages to a list of images using pdf2image."""
    images = convert_from_path(pdf_path)
    # Convert PIL images to OpenCV format (numpy arrays)
    images = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in images]
    return images

def detect_seal_signature(images):
    """Detect a seal or signature in the images using contour detection."""
    for img in images:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 1000 < area < 10000:  # Adjust based on typical seal/signature size
                x, y, w, h = cv2.boundingRect(cnt)
                return img[y:y+h, x:x+w]
    return None

def save_seal_signature(img, output_dir, base_name):
    """Save the detected seal/signature image to the output directory."""
    if img is not None:
        output_path = os.path.join(output_dir, f"seal_signature_{base_name}.png")
        cv2.imwrite(output_path, img)

print("Processing complete. Check the output directory for results.")