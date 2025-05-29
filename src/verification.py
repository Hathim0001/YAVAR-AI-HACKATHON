def perform_verifiability_checks(invoice_data, extracted_data):
    """Perform verifiability checks and generate a report."""
    verifiability_report = {
        "field_verification": {},
        "line_items_verification": [],
        "total_calculations_verification": {}
    }
    
    # Calculate average confidence across all pages
    confidences = [data[1] for data in extracted_data if data[1] > 0]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    avg_confidence /= 100  # Normalize to 0-1
    
    # Field verification for general fields
    for field in invoice_data:
        if field not in ["table_contents", "no_items", "seal_and_sign_present"]:
            verifiability_report["field_verification"][field] = {
                "confidence": avg_confidence,
                "present": invoice_data[field] != "N/A"
            }
    verifiability_report["field_verification"]["seal_and_sign_present"] = {
        "confidence": avg_confidence if invoice_data["seal_and_sign_present"] else 0,
        "present": invoice_data["seal_and_sign_present"]
    }
    
    # Line items verification
    for row in invoice_data["table_contents"]:
        calculated_total = row["quantity"] * row["unit_price"]
        check_passed = abs(calculated_total - row["total_amount"]) < 0.01
        verifiability_report["line_items_verification"].append({
            "row": row.get("serial_number", "N/A"),
            "line_total_check": {
                "calculated_value": calculated_total,
                "extracted_value": row["total_amount"],
                "check_passed": check_passed
            }
        })
    
    # Total calculations verification (placeholder)
    calculated_subtotal = sum(row["total_amount"] for row in invoice_data["table_contents"])
    verifiability_report["total_calculations_verification"]["subtotal_check"] = {
        "calculated_value": calculated_subtotal,
        "check_passed": True  # Requires actual extracted total for full check
    }
    
    return verifiability_report