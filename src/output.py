import os
import json
import pandas as pd
import cv2
import numpy as np

def detect_seal_signature(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:
                x, y, w, h = cv2.boundingRect(contour)
                return image[y:y+h, x:x+w], True
        return None, False
    except Exception as e:
        print(f"Seal detection error: {str(e)}")
        return None, False

def save_outputs(invoice_data, verifiability_report, image, output_dir, base_name):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f"extracted_data_{base_name}.json"), 'w') as f:
        json.dump(invoice_data, f, indent=4)
    
    with open(os.path.join(output_dir, f"verifiability_report_{base_name}.json"), 'w') as f:
        json.dump(verifiability_report, f, indent=4)
    
    general_df = pd.DataFrame([invoice_data["general_information"]])
    table_df = pd.DataFrame(invoice_data["table_contents"])
    with pd.ExcelWriter(os.path.join(output_dir, f"extracted_data_{base_name}.xlsx")) as writer:
        general_df.to_excel(writer, sheet_name="General Information", index=False)
        table_df.to_excel(writer, sheet_name="Table Contents", index=False)
    
    seal_img, detected = detect_seal_signature(image)
    if detected:
        cv2.imwrite(os.path.join(output_dir, f"seal_signature_{base_name}.png"), seal_img)
        invoice_data["general_information"]["seal_and_sign_present"] = True
    else:
        invoice_data["general_information"]["seal_and_sign_present"] = False
