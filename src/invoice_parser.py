import re

def parse_invoice_data(text):
    """
    Parse extracted text from an invoice PDF to retrieve structured data.
    
    Args:
        text (str): The raw text extracted from the invoice PDF.
    
    Returns:
        dict: A dictionary containing the extracted invoice details.
    """
    invoice_data = {}
    
    # Define regex patterns for key invoice fields
    fields = {
        "invoice_number": r"(?:Invoice|Inv|Bill|Billing)\s*(?:No|Number|#|ID)?\.?\s*[:\-]?\s*(\w+)",
        "invoice_date": r"(?:Invoice\s*)?Date\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})",
        "supplier_gst_number": r"(?:Supplier|Vendor)\s*GST(?:IN)?\s*[:\-]?\s*([\w\d]+)",
        "bill_to_gst_number": r"(?:Bill\s*To|Customer)\s*GST(?:IN)?\s*[:\-]?\s*([\w\d]+)",
        "po_number": r"(?:PO|Purchase\s*Order|Order)\s*(?:No|Number|#|ID)?\.?\s*[:\-]?\s*(\w+)(?!\s*SWIFT)",  # Avoid matching SWIFT code
        "shipping_address": r"(?:Ship\s*To|Shipping\s*Address|Deliver\s*To|Bill\s*To|Customer\s*Name\s*\n)([\s\S]+?)(?=\n\n|$)",  # Capture address after Customer Name
    }
    
    # Extract each field using its regex pattern
    for field, pattern in fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        invoice_data[field] = match.group(1).strip() if match else "N/A"
    
    # Define regex pattern for table rows
    # Matches: Description, From, Until, Amount (no serial number or quantity)
    table_pattern = r"^(.*?)\s+(Nov\s+\d{2},\s+\d{4})\s+(Nov\s+\d{2},\s+\d{4})\s+(?:USD\s+)?[\$]?\d+\.\d{2}\s*$"
    table_data = []
    
    # Split text into lines and process each line for table data
    lines = text.split("\n")
    for line in lines:
        match = re.match(table_pattern, line.strip(), re.IGNORECASE)
        if match:
            description = match.group(1).strip()
            from_date = match.group(2)
            until_date = match.group(3)
            # Extract amount (last part of the line)
            amount = re.search(r"(?:USD\s+)?[\$]?\d+\.\d{2}", line).group(0)
            amount_value = float(re.sub(r'[^\d.]', '', amount))
            
            # Structure the row data (assume quantity = 1 since not specified)
            row = {
                "serial_number": "N/A",  # No serial number in this invoice
                "description": f"{description} (From: {from_date}, Until: {until_date})",
                "hsn_sac": "N/A",  # Not present in the invoice
                "quantity": 1.0,   # Assume 1 since not specified
                "unit_price": amount_value,
                "total_amount": amount_value
            }
            table_data.append(row)
    
    # Add table data and item count to the invoice data
    invoice_data["table_contents"] = table_data
    invoice_data["no_items"] = len(table_data)
    
    return invoice_data

# Example usage
if __name__ == "__main__":
    # Sample invoice text (based on index.pdf)
    sample_text = """
    INVOICE

    YesLogic Pty. Ltd.
    7 / 39 Bouverie St
    Carlton VIC 3053
    Australia
    www.yeslogic.com
    ABN 32 101 193 560

    Customer Name
    Street
    Postcode City
    Country

    Invoice date: Nov 26, 2016
    Invoice number: 161126
    Payment due: 30 days after invoice date

    Description            From          Until          Amount
    Prince Upgrades & Support  Nov 26, 2016  Nov 26, 2017  USD $950.00

    TOTAL USD $950.00

    Please transfer amount to:
    Bank account name: Yes Logic Pty Ltd
    Name of Bank: Commonwealth Bank of Australia (CBA)
    BANK STATE BRANCH (BSB): 063010
    BANK STATE BRANCH (BSB): 063019
    Bank account number: 13201652
    Bank SWIFT code: CTBAAU2S
    231 Swanston St, Melbourne, VIC 3000, Australia
    """
    
    result = parse_invoice_data(sample_text)
    print("Invoice Data:")
    for key, value in result.items():
        print(f"{key}: {value}")