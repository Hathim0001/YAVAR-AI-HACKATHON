import os
from preprocess import preprocess_image
from ocr import extract_text_with_confidence
from parser import parse_invoice_data
from verification import perform_verifiability_checks
from output import save_outputs

input_dir = "current_directory/input/"
output_dir = "current_directory/output/"

pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]

for pdf_file in pdf_files:
    images = convert_pdf_to_images(os.path.join(input_dir, pdf_file))
    preprocessed_images = [preprocess_image(img) for img in images]
    extracted_data = [extract_text_with_confidence(img) for img in preprocessed_images]
    invoice_data = parse_invoice_data(extracted_data)
    seal_signature_img = detect_seal_signature(preprocessed_images)
    if seal_signature_img:
        invoice_data["seal_and_sign_present"] = True
        save_seal_signature(seal_signature_img, output_dir)
    else:
        invoice_data["seal_and_sign_present"] = False
    verifiability_report = perform_verifiability_checks(invoice_data, extracted_data)
    save_outputs(invoice_data, verifiability_report, output_dir)

def convert_pdf_to_images(pdf_path):
    pass

def detect_seal_signature(images):
    pass

def save_seal_signature(img, output_dir):
    pass