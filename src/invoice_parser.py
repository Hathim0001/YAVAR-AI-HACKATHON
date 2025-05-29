import re

def parse_invoice_data(text):
    """Parse invoice details from OCR-extracted text."""
    invoice_data = {}
    
    # Regex patterns for key fields
    fields = {
        "invoice_number": r"(?:Invoice|Inv|Bill|Billing)\s*(?:No|Number|#|ID)?\.?\s*[:\-]?\s*(\d+|\w+)",
        "invoice_date": r"(?:Invoice\s*)?Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})",
        "supplier_gst_number": r"(?:Supplier|Vendor)\s*GST(?:IN)?\s*[:\-]?\s*([\w\d]+)",
        "bill_to_gst_number": r"(?:Bill\s*To|Customer)\s*GST(?:IN)?\s*[:\-]?\s*([\w\d]+)",
        "po_number": r"(?:PO|Purchase\s*Order|Order)\s*(?:No|Number|#|ID)?\.?\s*[:\-]?\s*(\w+)",
        "shipping_address": r"(?:Ship\s*To|Shipping\s*Address|Deliver\s*To|Bill\s*To|Customer\s*Name\s*)([\s\S]+?)(?=\n\s*\n|$)"
    }
    
    # Extract fields
    for field, pattern in fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        invoice_data[field] = match.group(1).strip() if match else "N/A"
    
    # Parse table data (if present)
    table_pattern = r"^(.*?)\s+(Nov\s+\d{2},\s+\d{4})\s+(Nov\s+\d{2},\s+\d{4})\s+(?:USD\s+)?[\$]?\d+\.\d{2}\s*$"
    table_data = []
    lines = text.split("\n")
    for line in lines:
        match = re.match(table_pattern, line.strip(), re.IGNORECASE)
        if match:
            description = match.group(1).strip()
            from_date = match.group(2)
            until_date = match.group(3)
            amount = re.search(r"(?:USD\s+)?[\$]?\d+\.\d{2}", line).group(0)
            amount_value = float(re.sub(r'[^\d.]', '', amount))
            row = {
                "serial_number": "N/A",
                "description": f"{description} (From: {from_date}, Until: {until_date})",
                "hsn_sac": "N/A",
                "quantity": 1.0,
                "unit_price": amount_value,
                "total_amount": amount_value
            }
            table_data.append(row)
    
    invoice_data["table_contents"] = table_data
    invoice_data["no_items"] = len(table_data)
    return invoice_data