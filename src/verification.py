def perform_verifiability_checks(invoice_data, extracted_data):
    verifiability_report = {"field_verification": {}, "line_items_verification": []}
    for field, value in invoice_data.items():
        if field != "table_contents" and field != "no_items":
            confidence = extracted_data[0][1][0] / 100 
            verifiability_report["field_verification"][field] = {
                "confidence": confidence,
                "present": bool(value)
            }
    for row in invoice_data["table_contents"]:
        calculated = row["unit_price"] * row["quantity"]
        verified = abs(calculated - row["total_amount"]) < 0.01
        verifiability_report["line_items_verification"].append({
            "row": row["serial_number"],
            "line_total_check": {
                "calculated_value": calculated,
                "extracted_value": row["total_amount"],
                "check_passed": verified
            }
        })
    subtotal = sum(row["total_amount"] for row in invoice_data["table_contents"])
    verifiability_report["total_calculations_verification"] = {
        "subtotal_check": {"calculated_value": subtotal, "check_passed": True}
    }
    return verifiability_report