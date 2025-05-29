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
input_dir = "D:/YAVAR-AI-HACKATHON/input_pdfs/"
output_dir = "D:/YAVAR-AI-HACKATHON/input_pdfs/"

# Check if input directory exists
if not os.path.exists(input_dir):
    raise FileNotFoundError(f"Input directory '{input_dir}' does not exist. Please create it and place your PDFs there.")

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Get list of PDF files
pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]

if not pdf_files:
    print("No PDF files found in the input directory. Please add some PDFs to process.")
    exit()

for pdf_file in pdf_files:
    # Step 1: Convert PDF to images
    pdf_path = os.path.join(input_dir, pdf_file)
    images_pil = convert_from_path(pdf_path)
    images = [np.array(img) for img in images_pil]  # Convert PIL images to numpy arrays

    # Step 2: Preprocess images
    preprocessed_images = [preprocess_image(img) for img in images]

    # Step 3: Extract text and confidence scores using OCR
    extracted_data = [extract_text_with_confidence(img) for img in preprocessed_images]

    # Combine text from all pages
    full_text = "\n".join([data[0] for data in extracted_data])

    # Step 4: Parse extracted text into structured invoice data
    invoice_data = parse_invoice_data(full_text)

    # Step 5: Detect seal and signature from original images
    seal_signature_img = detect_seal_signature(images)
    base_name = os.path.splitext(pdf_file)[0]
    if seal_signature_img is not None:
        invoice_data["seal_and_sign_present"] = True
        save_seal_signature(seal_signature_img, output_dir, base_name)
    else:
        invoice_data["seal_and_sign_present"] = False

    # Step 6: Perform verifiability checks
    verifiability_report = perform_verifiability_checks(invoice_data, extracted_data)

    # Step 7: Save outputs with unique filenames
    save_outputs(invoice_data, verifiability_report, output_dir, base_name)

def detect_seal_signature(images):
    """Detect a seal or signature in the images using contour detection."""
    for img in images:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
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