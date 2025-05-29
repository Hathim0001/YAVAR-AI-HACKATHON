import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from preprocess import preprocess_image
from ocr import extract_text_with_confidence
from invoice_parser import parse_invoice_data
from verification import perform_verifiability_checks
from output import save_outputs

# Define the path to Poppler binaries (adjust this to your Poppler installation path)
poppler_path = r"C:\Users\Mohammed Hathim\Downloads\poppler\Library\bin"

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
input_dir = os.path.join(base_dir, "pdfs", "samples")
output_dir = os.path.join(base_dir, "pdfs", "output")


# Ensure input directory exists
if not os.path.exists(input_dir):
    raise FileNotFoundError(f"Input directory '{input_dir}' does not exist. Please create it and place your PDFs there.")

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Get list of PDF files
pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]

# Check if any PDFs are found
if not pdf_files:
    raise FileNotFoundError(f"No PDF files found in '{input_dir}'. Please add some PDFs to process.")

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

for pdf_file in pdf_files:
    # Step 1: Convert PDF to images
    pdf_path = os.path.join(input_dir, pdf_file)
    try:
        images_pil = convert_from_path(pdf_path, poppler_path=poppler_path)
    except Exception as e:
        if "poppler" in str(e).lower():
            raise RuntimeError(f"Poppler not found at '{poppler_path}'. Please ensure the path is correct and contains Poppler binaries (e.g., pdftoppm.exe).")
        raise e
    images = [np.array(img) for img in images_pil]  # Convert PIL images to numpy arrays

    # Step 2: Preprocess images
    preprocessed_images = [preprocess_image(img) for img in images]

    # Step 3: Extract text and confidence scores using OCR
    try:
        extracted_data = [extract_text_with_confidence(img) for img in preprocessed_images]
    except Exception as e:
        if "tesseract" in str(e).lower():
            raise RuntimeError("Tesseract OCR is not accessible. Ensure Tesseract is installed and the path to tesseract.exe is correctly specified in ocr.py.")
        raise e

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

print("Processing complete. Check the output directory for results.")