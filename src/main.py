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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "samples")  # Corrected to match your directory structure
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Ensure directories exist
os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Increase PIL's maximum image pixel limit to suppress DecompressionBombWarning
Image.MAX_IMAGE_PIXELS = 200000000  # Set a higher limit

def process_pdf(pdf_path, output_dir):
    """Process a single PDF file."""
    try:
        # Convert PDF to images with a lower DPI to handle large images
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        logging.info(f"Processing {base_name}.pdf")
        images = convert_from_path(pdf_path, dpi=200)  # Reduced DPI to manage large images
        
        all_elements = []
        last_image = None
        for i, image in enumerate(images):
            logging.info(f"Processing page {i+1}")
            image_np = np.array(image)
            
            # Preprocess image
            preprocessed = preprocess_image(image_np)
            if preprocessed is None or preprocessed.size == 0:
                logging.error("Preprocessing returned an empty image.")
                raise ValueError("Preprocessing failed: Empty image")
            
            # Extract text with positions
            elements = extract_text_with_positions(preprocessed)
            if not elements:
                logging.warning(f"No text elements extracted from page {i+1}.")
            all_elements.append(elements)
            
            # Keep the last image for seal detection
            last_image = image_np
        
        # Check if any elements were extracted
        if not any(all_elements):
            logging.error("No text elements extracted from any page.")
            raise ValueError("OCR failed: No text extracted")
        
        # Parse extracted data
        invoice_data = parse_invoice_data(all_elements)
        if not invoice_data["table_contents"]:
            logging.warning("No table contents extracted.")
        
        # Perform verifiability checks
        verifiability_report = perform_verifiability_checks(invoice_data, all_elements)
        
        # Save outputs
        save_outputs(invoice_data, verifiability_report, last_image, output_dir, base_name)
        
        logging.info(f"Processed {base_name}.pdf successfully")
        return True
    except Exception as e:
        logging.error(f"Error processing {pdf_path}: {str(e)}", exc_info=True)
        return False

def main():
    # Get list of PDF files
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logging.error(f"No PDF files found in '{INPUT_DIR}'")
        raise FileNotFoundError(f"No PDF files found in '{INPUT_DIR}'")
    
    # Process each PDF
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        process_pdf(pdf_path, OUTPUT_DIR)
    
    logging.info("Processing complete. Check output directory for results.")

if __name__ == "__main__":
    main()