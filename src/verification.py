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
        value = (invoice_data.get("general_information", {}).get(field) or
                 invoice_data.get("totals", {}).get(field))
        present = (value is not None and 
                  value != "Not Found" and 
                  not (isinstance(value, (int, float)) and value == 0.0) and
                  not (isinstance(value, str) and not value.strip()))
        
        if present:
            words = str(value).split() if isinstance(value, str) else [str(value)]
            word_confs = [confidences.get(word, 0.9) for word in words if word in confidences]
            confidence = np.mean(word_confs) if word_confs else 0.9
        else:
            confidence = 0.0
            
        report["field_verification"][field] = {
            "confidence": round(confidence, 2),
            "present": present
        }
    
    for i, item in enumerate(invoice_data.get("table_contents", [])):
        try:
            qty = float(item.get("quantity", 0.0))
            unit_price = float(item.get("unit_price", 0.0))
            total = float(item.get("total_amount", 0.0))
            
            calculated_total = round(qty * unit_price, 2)
            check_passed = abs(calculated_total - total) <= 0.01
            
            desc = item.get("description", "")
            hsn_sac = item.get("hsn_sac", "")
            serial = item.get("serial_number", "")
            
            desc_words = desc.split() if desc != "Not Found" else []
            hsn_words = hsn_sac.split() if hsn_sac != "Not Found" else []
            serial_words = serial.split() if serial != "Not Found" else []
            
            desc_conf = np.mean([confidences.get(w, 0.9) for w in desc_words]) if desc_words else 0.9
            hsn_conf = np.mean([confidences.get(w, 0.9) for w in hsn_words]) if hsn_words else 0.9
            serial_conf = np.mean([confidences.get(w, 0.9) for w in serial_words]) if serial_words else 0.9
            qty_conf = confidences.get(str(qty), 0.9) if qty != 0.0 else 0.9
            price_conf = confidences.get(str(unit_price), 0.9) if unit_price != 0.0 else 0.9
            total_conf = confidences.get(str(total), 0.9) if total != 0.0 else 0.9
            
            report["line_items_verification"].append({
                "row": i+1,
                "description_confidence": round(desc_conf, 2),
                "hsn_sac_confidence": round(hsn_conf, 2),
                "quantity_confidence": round(qty_conf, 2),
                "unit_price_confidence": round(price_conf, 2),
                "total_amount_confidence": round(total_conf, 2),
                "serial_number_confidence": round(serial_conf, 2),
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
        subtotal_calc = sum(float(item["total_amount"]) 
                          for item in invoice_data.get("table_contents", []))
        subtotal_ext = float(invoice_data.get("totals", {}).get("subtotal", 0.0))
        discount = float(invoice_data.get("totals", {}).get("discount", 0.0))
        gst = float(invoice_data.get("totals", {}).get("gst", 0.0))
        final_total_ext = float(invoice_data.get("totals", {}).get("final_total", 0.0))
        
        final_total_calc = round(subtotal_calc - discount + gst, 2)
        
        subtotal_conf = confidences.get(str(subtotal_ext), 0.9) if subtotal_ext != 0.0 else 0.9
        discount_conf = confidences.get(str(discount), 0.9) if discount != 0.0 else 0.9
        gst_conf = confidences.get(str(gst), 0.9) if gst != 0.0 else 0.9
        final_total_conf = confidences.get(str(final_total_ext), 0.9) if final_total_ext != 0.0 else 0.9
        
        report["total_calculations_verification"] = {
            "subtotal_check": {
                "calculated_value": round(subtotal_calc, 2),
                "extracted_value": round(subtotal_ext, 2),
                "check_passed": abs(subtotal_calc - subtotal_ext) <= 0.01,
                "confidence": round(subtotal_conf, 2)
            },
            "discount_check": {
                "extracted_value": round(discount, 2),
                "present": discount > 0,
                "confidence": round(discount_conf, 2)
            },
            "gst_check": {
                "extracted_value": round(gst, 2),
                "present": gst > 0,
                "confidence": round(gst_conf, 2)
            },
            "final_total": {
                "calculated_value": round(final_total_calc, 2),
                "extracted_value": round(final_total_ext, 2),
                "check_passed": abs(final_total_calc - final_total_ext) <= 0.01,
                "confidence": round(final_total_conf, 2)
            }
        }
        
        if not report["total_calculations_verification"]["subtotal_check"]["check_passed"]:
            report["summary"]["issues"].append(
                f"Subtotal mismatch: {round(subtotal_ext, 2)} vs {round(subtotal_calc, 2)}"
            )
            
        if not report["total_calculations_verification"]["final_total_check"]["check_passed"]:
            report["summary"]["issues"].append(
                f"Final total mismatch: {round(final_total_ext, 2)} vs {round(final_total_calc, 2)}"
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
    ) if report["line_items_verification"] else True
    
    return report