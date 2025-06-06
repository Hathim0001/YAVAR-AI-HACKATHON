# Invoice Data Extraction and Verification

**Yavar Internship Selection – May 2025 Hackathon**

This project extracts and verifies structured data from scanned invoice PDFs using Python and open-source tools. It supports diverse invoice layouts and ensures data integrity with verifiability checks. Outputs are generated in JSON, Excel, and image formats.

---

## Overview

A modular solution to process non-searchable (scanned) invoice PDFs:
- Enhance image quality
- Extract key fields using OCR
- Perform validation and verifiability checks
- Output structured results

---

## Approach

The pipeline is structured into the following stages:

### 1. Image Preprocessing
**Purpose:** Enhance image quality for accurate OCR

**Techniques:**
- **Resizing:** Scale to 1000px width using `imutils.resize`
- **Grayscale Conversion:** `cv2.cvtColor`
- **Denoising:** `cv2.fastNlMeansDenoising` (h=10)
- **Thresholding:** Adaptive Gaussian (`cv2.adaptiveThreshold`, blockSize=31, C=10)
- **Deskewing:** Detect contours and correct perspective (`cv2.findContours`, `four_point_transform`)

**Libraries:** `OpenCV`, `imutils`

---

### 2. OCR Processing
**Library:** [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) via `pytesseract`

**Process:**
- Convert PDFs to images (`pdf2image`, DPI=200)
- Extract text and coordinates (`pytesseract.image_to_data`, `--psm 6`)
- Filter out detections with confidence < 60

**Output:** Text elements with position, dimensions, and confidence

---

### 3. Data Extraction

#### General Fields
- **Fields:** `invoice_number`, `invoice_date`, `supplier_gst_number`, `bill_to_gst_number`, `po_number`, `shipping_address`
- **Method:** Group by Y-coordinates (threshold=20), split into regions via keyword heuristics, use regex

#### Table Contents
- **Fields:** `serial_number`, `description`, `hsn_sac`, `quantity`, `unit_price`, `total_amount`
- **Method:** Locate header keywords, map columns using X-coordinates and `bisect`, extract and convert numerics

#### Additional Fields
- Vendor/Customer Info: name, phone, address
- Payment Terms & Bank Details
- Totals: Compute subtotal, extract or calculate `discount`, `gst`, and `final_total`

---

### 4. Verifiability Checks
- **Confidence Scores:** Tesseract average per field (0.0 to 1.0)
- **Line Item Validation:** `unit_price × quantity ≈ total_amount` (tolerance: 0.01)
- **Total Check:** `final_total ≈ subtotal - discount + gst`
- **Flags:** Track field presence and check status

---

### 5. Output Generation
| Format | Description |
|--------|-------------|
| **JSON** | `extracted_data_<base_name>.json`, `verifiability_report_<base_name>.json` |
| **Excel** | `extracted_data_<base_name>.xlsx` with "General Information" and "Table Contents" sheets |
| **Image** | Detected seal/signature saved as `seal_signature_<base_name>.png` |

**Libraries:** `pandas`, `openpyxl`, `os`, `logging`

---

### 6. Error Handling
- Graceful fallback to defaults (`"Not Found"`, `0.0`) on failure
- Logs errors during preprocessing, OCR, or parsing
- Directory-safe using `os.makedirs(..., exist_ok=True)`

---

## Tech Stack

| Component       | Library/Tool           |
|----------------|------------------------|
| OCR            | Tesseract + pytesseract |
| Preprocessing  | OpenCV, imutils         |
| PDF Handling   | pdf2image               |
| Excel Export   | pandas, openpyxl        |
| Regex/Parsing  | re, bisect              |
| Logging/OS     | logging, os             |

---

## Fine-Tuning

| Area | Configurations |
|------|----------------|
| Tesseract | `--psm 6` for structured layout; try `--psm 3` for sparse |
| Denoising | Adjust `h` parameter |
| Thresholding | Tune `blockSize`, `C` |
| Regex | Match various date, GSTIN, and currency formats |
| Seal Detection | Adjust contour area threshold |

---

## Generalizability

- **Layouts:** Region-based parsing + regex handles diverse formats
- **Image Quality:** Preprocessing improves robustness
- **Scalability:** Easy to extend with more fields/validations
- **Open Source:** Built entirely with open-source libraries

---

## Limitations & Future Improvements

| Limitation | Improvement |
|------------|-------------|
| Poor results with handwriting or complex tables | Integrate deep learning OCR (e.g., [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)) |
| Rule-based parsing | Use layout detection models (e.g., Detectron2) |
| Static seal detection | Train seal classification model |
