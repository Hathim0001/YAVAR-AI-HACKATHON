import re

def parse_invoice_data(extracted_data):
    invoice_data = {}
    # Combine text from all pages
    text = "\n".join([data[0] for data in extracted_data])

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
        invoice_data[field] = match.group(1 if field != "invoice_number" else 2) if match else "N/A"

    # Extract table contents
    table_data = []
    lines = text.split("\n")
    for line in lines:
        if re.match(r"^\d+\s+", line):  # Assuming rows start with a number
            parts = line.split()
            if len(parts) >= 5:  # Ensure enough parts for table fields
                row = {
                    "serial_number": parts[0] if parts[0].isdigit() else "N/A",
                    "description": " ".join(parts[1:-4]) if len(parts) > 5 else parts[1],
                    "hsn_sac": parts[-4],
                    "quantity": float(parts[-3]) if parts[-3].replace(".", "").isdigit() else 0,
                    "unit_price": float(parts[-2]) if parts[-2].replace(".", "").isdigit() else 0,
                    "total_amount": float(parts[-1]) if parts[-1].replace(".", "").isdigit() else 0
                }
                table_data.append(row)
    invoice_data["table_contents"] = table_data
    invoice_data["no_items"] = len(table_data)
    return invoice_data