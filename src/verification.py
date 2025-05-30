import re
import numpy as np
from typing import Dict

def perform_verifiability_checks(invoice_data: Dict, confidences: Dict) -> Dict:
    report = {
        "field_verification": {},
        "line_items_verification": [],
        "total_calculations_verification": {},
        "summary": {"issues": []}
    }
    
    fields = [
        "invoice_number", "invoice_date", "supplier_gst_number",
        "bill_to_gst_number", "po_number", "shipping_address",
        "subtotal", "discount", "gst", "final_total"
    ]
    
    for field in fields:
        value = invoice_data.get(field)
        present = value is not None and value != "Not Found" and value != 0.0
        
        if present:
            words = str(value).split()
            word_confs = [confidences.get(word, 0.7) for word in words if word in confidences]
            confidence = np.mean(word_confs) if word_confs else 0.85
        else:
            confidence = 0.0
            
        report["field_verification"][field] = {
            "confidence": round(confidence, 2),
            "present": present
        }
    
    for i, item in enumerate(invoice_data.get("table_contents", [])):
        try:
            qty = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            total = item.get("total_amount", 0)
            
            calculated_total = round(qty * unit_price, 2)
            check_passed = abs(calculated_total - total) < 0.01
            
            report["line_items_verification"].append({
                "row": i+1,
                "line_total_check": {
                    "calculated_value": calculated_total,
                    "extracted_value": total,
                    "check_passed": check_passed
                }
            })
            
            if not check_passed:
                report["summary"]["issues"].append(
                    f"Line {i+1} total mismatch: {total} vs {calculated_total}"
                )
        except Exception as e:
            report["summary"]["issues"].append(f"Line {i+1} error: {str(e)}")
    
    try:
        subtotal_calc = sum(item["total_amount"] for item in invoice_data.get("table_contents", []))
        subtotal_ext = invoice_data.get("subtotal", 0)
        discount = invoice_data.get("discount", 0) or 0
        gst = invoice_data.get("gst", 0) or 0
        final_total_ext = invoice_data.get("final_total", 0)
        
        final_total_calc = subtotal_calc - discount + gst
        
        report["total_calculations_verification"] = {
            "subtotal_check": {
                "calculated_value": subtotal_calc,
                "extracted_value": subtotal_ext,
                "check_passed": abs(subtotal_calc - subtotal_ext) < 0.01
            },
            "discount_check": {
                "extracted_value": discount,
                "present": discount > 0
            },
            "gst_check": {
                "extracted_value": gst,
                "present": gst > 0
            },
            "final_total_check": {
                "calculated_value": final_total_calc,
                "extracted_value": final_total_ext,
                "check_passed": abs(final_total_calc - final_total_ext) < 0.01
            }
        }
        
        if not report["total_calculations_verification"]["subtotal_check"]["check_passed"]:
            report["summary"]["issues"].append(
                f"Subtotal mismatch: {subtotal_ext} vs {subtotal_calc}"
            )
            
        if not report["total_calculations_verification"]["final_total_check"]["check_passed"]:
            report["summary"]["issues"].append(
                f"Final total mismatch: {final_total_ext} vs {final_total_calc}"
            )
            
    except Exception as e:
        report["summary"]["issues"].append(f"Total calculation error: {str(e)}")
    
    report["summary"]["all_fields_present"] = all(
        report["field_verification"][f]["present"] 
        for f in ["invoice_number", "invoice_date", "final_total"]
    )
    
    report["summary"]["all_line_items_valid"] = all(
        item["line_total_check"]["check_passed"]
        for item in report["line_items_verification"]
    )
    
    return report
