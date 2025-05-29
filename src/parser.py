import re

def parse_invoice_data(text):
    """Parse the extracted text to get structured invoice data."""
    invoice_data = {}
    
    # Define regex patterns for general fields
    fields = {
        "invoice_number": r"Invoice\s*(No|Number)\.?\s*[:\-]?\s*(\w+)",
        "invoice_date": r"Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})",
        "supplier_gst_number": r"Supplier\s*GST\s*[:\-]?\s*([\w\d]+)",
        "bill_to_gst_number": r"Bill\s*To\s*GST\s*[:\-]?\s*([\w\d]+)",
        "po_number": r"PO\s*Number\s*[:\-]?\s*(\w+)",
        "shipping_address": r"Shipping\s*Address\s*[:\-]?\s*(.+?)(?=\n|$)",
    }
    
    # Extract general fields
    for field, pattern in fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_data[field] = match.group(1 if field != "invoice_number" else 2)
        else:
            invoice_data[field] = "N/A"
    
    # Extract table contents
    table_data = []
    lines = text.split("\n")
    for line in lines:
        if re.match(r"^\d+\s+", line):  # Assuming table rows start with a number
            parts = line.split()
            if len(parts) >= 5:  # Ensure enough parts for table fields
                row = parse_table_line(parts)
                if row:
                    table_data.append(row)
    invoice_data["table_contents"] = table_data
    invoice_data["no_items"] = len(table_data)
    return invoice_data

def parse_table_line(parts):
    """Parse a single table line into a dictionary."""
    if len(parts) < 5:
        return None
    serial_number = parts[0] if parts[0].isdigit() else "N/A"
    total_amount = parts[-1] if parts[-1].replace('.', '', 1).isdigit() else "N/A"
    unit_price = parts[-2] if parts[-2].replace('.', '', 1).isdigit() else "N/A"
    quantity = parts[-3] if parts[-3].replace('.', '', 1).isdigit() else "N/A"
    hsn_sac = parts[-4]
    description = " ".join(parts[1:-4]) if len(parts) > 5 else parts[1]
    return {
        "serial_number": serial_number,
        "description": description,
        "hsn_sac": hsn_sac,
        "quantity": float(quantity) if quantity != "N/A" else 0,
        "unit_price": float(unit_price) if unit_price != "N/A" else 0,
        "total_amount": float(total_amount) if total_amount != "N/A" else 0
    }