import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
from preprocess import preprocess_image
from ocr import extract_text_with_positions
from invoice_parser import parse_invoice_data
from verification import perform_verifiability_checks
from output import save_outputs
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "samples")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

Image.MAX_IMAGE_PIXELS = 200000000

def process_pdf(pdf_path, output_dir):
    try:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        logging.info(f"Processing {base_name}.pdf")
        images = convert_from_path(pdf_path, dpi=200)
        
        all_elements = []
        last_image = None
        for i, image in enumerate(images):
            logging.info(f"Processing page {i+1}")
            image_np = np.array(image)
            
            preprocessed = preprocess_image(image_np)
            if preprocessed is None or preprocessed.size == 0:
                logging.error("Preprocessing returned an empty image.")
                raise ValueError("Preprocessing failed: Empty image")
            
            elements = extract_text_with_positions(preprocessed)
            if not elements:
                logging.warning(f"No text elements extracted from page {i+1}.")
            all_elements.append(elements)
            
            last_image = image_np
        
        if not any(all_elements):
            logging.error("No text elements extracted from any page.")
            raise ValueError("OCR failed: No text extracted")
        
        invoice_data = parse_invoice_data(all_elements)
        if not invoice_data["table_contents"]:
            logging.warning("No table contents extracted.")
        
        verifiability_report = perform_verifiability_checks(invoice_data, all_elements)
        
        save_outputs(invoice_data, verifiability_report, last_image, output_dir, base_name)
        
        logging.info(f"Processed {base_name}.pdf successfully")
        return True
    except Exception as e:
        logging.error(f"Error processing {pdf_path}: {str(e)}", exc_info=True)
        return False

def main():
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logging.error(f"No PDF files found in '{INPUT_DIR}'")
        raise FileNotFoundError(f"No PDF files found in '{INPUT_DIR}'")
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        process_pdf(pdf_path, OUTPUT_DIR)
    
    logging.info("Processing complete. Check output directory for results.")

if __name__ == "__main__":
    main()
