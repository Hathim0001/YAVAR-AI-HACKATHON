import re
import bisect
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def group_into_rows(elements, threshold=20):
    """Group text elements into rows based on Y-coordinates."""
    valid_elements = [elem for elem in elements if 'y' in elem and isinstance(elem['y'], (int, float))]
    if not valid_elements:
        logging.warning("No elements with valid Y-coordinates found.")
        return []
    
    sorted_elements = sorted(valid_elements, key=lambda e: e['y'])
    rows = []
    current_row = [sorted_elements[0]]
    for elem in sorted_elements[1:]:
        try:
            if elem['y'] - current_row[-1]['y'] < threshold:
                current_row.append(elem)
            else:
                rows.append(sorted(current_row, key=lambda e: e['x']))
                current_row = [elem]
        except Exception as e:
            logging.error(f"Error grouping row element {elem}: {str(e)}")
            continue
    if current_row:
        rows.append(sorted(current_row, key=lambda e: e['x']))
    return rows

def define_regions(rows):
    """Define regions of the invoice for spatial analysis."""
    regions = {
        "header": [],
        "vendor": [],
        "customer": [],
        "table": [],
        "footer": []
    }
    
    regions["header"] = list(range(min(5, len(rows))))
    
    for i, row in enumerate(rows):
        row_text = ' '.join([e['text'].lower() for e in row])
        if any(kw in row_text for kw in ["bill to", "ship to", "customer", "client", "seller", "attention to"]):
            break
        regions["vendor"].append(i)
    
    customer_start = i
    for i in range(customer_start, len(rows)):
        row_text = ' '.join([e['text'].lower() for e in row])
        if any(kw in row_text for kw in ["description", "items", "no.", "qty", "item", "organic", "amount", "1.", "01"]):
            break
        regions["customer"].append(i)
    
    table_start = i
    for i in range(table_start, len(rows)):
        row_text = ' '.join([e['text'].lower() for e in row])
        if any(kw in row_text for kw in ["summary", "total", "footer", "vat [%]", "subtotal", "gst", "sales tax", "total due"]):
            break
        regions["table"].append(i)
    
    regions["footer"] = list(range(i, len(rows)))
    
    return regions

def find_table_header(rows, regions):
    """Identify the table header row based on keywords within the table region."""
    header_keywords = ["description", "item", "quantity", "qty", "price", "rate", "amount", "total", "hsn/sac", "s.no", "sl.no", "no.", "product", "net price", "net worth", "gross", "subtotal", "um", "vat [%]"]
    for i in regions["table"]:
        row = rows[i]
        row_text = ' '.join([e['text'].lower() for e in row])
        keyword_count = sum(1 for kw in header_keywords if kw in row_text.replace(" ", ""))
        if keyword_count >= 1:  # Lowered threshold
            return i, row, header_keywords
    return None, None, None

def parse_table(rows, header_row, header_keywords, start_index):
    """Parse table rows into structured data based on column positions."""
    header_mapping = {
        "s.no": "serial_number", "sl.no": "serial_number", "no.": "serial_number",
        "description": "description", "item": "description", "organic items": "description",
        "hsn/sac": "hsn_sac",
        "quantity": "quantity", "qty": "quantity", "quantity(kg)": "quantity",
        "price": "unit_price", "rate": "unit_price", "unit price": "unit_price", "net price": "unit_price", "price/kg": "unit_price",
        "amount": "total_amount", "total": "total_amount", "net worth": "net_worth", "gross": "total_amount", "subtotal": "total_amount",
        "vat [%]": "vat",
        "um": "unit_measure"
    }
    
    header_words = []
    for elem in header_row:
        for keyword in header_keywords:
            if keyword in elem['text'].lower().replace(" ", ""):
                header_words.append((elem, keyword))
                break
    header_words.sort(key=lambda x: x[0]['x'])
    
    centers = [(word[0]['x'] + word[0]['width'] / 2) for word in header_words]
    boundaries = [0] + [(centers[i] + centers[i+1]) / 2 for i in range(len(centers)-1)] + [10000]
    
    table_data = []
    for row in rows[start_index + 1:]:
        row_text = ' '.join([e['text'].lower() for e in row])
        if any(kw in row_text for kw in ['total', 'subtotal', 'gst', 'discount', 'summary', 'vat [%]', 'sales tax', 'total due']):
            break
        
        columns = [[] for _ in range(len(header_words))]
        for elem in row:
            center_x = elem['x'] + elem['width'] / 2
            col_idx = min(max(0, bisect.bisect_left(boundaries, center_x) - 1), len(header_words) - 1)
            columns[col_idx].append(elem)
        
        row_data = {}
        for i, (header_elem, keyword) in enumerate(header_words):
            field = header_mapping.get(keyword, keyword)
            col_text = ' '.join([e['text'] for e in columns[i]])
            if field in ['quantity', 'unit_price', 'total_amount', 'net_worth']:
                num_match = re.search(r'\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?', col_text.replace(',', '').replace('$', ''))
                if num_match:
                    num_str = num_match.group()
                    try:
                        row_data[field] = float(num_str)
                    except ValueError as e:
                        logging.warning(f"Failed to convert '{num_str}' to float for field '{field}': {str(e)}")
                        row_data[field] = 0.0
                else:
                    row_data[field] = 0.0
            elif field == 'vat':
                vat_match = re.search(r'(\d+)%', col_text)
                row_data[field] = float(vat_match.group(1)) if vat_match else 0.0
            else:
                row_data[field] = col_text if col_text else "Not Found"
        
        for field in ['serial_number', 'description', 'hsn_sac', 'quantity', 'unit_price', 'total_amount']:
            if field not in row_data:
                row_data[field] = 0.0 if field in ['quantity', 'unit_price', 'total_amount'] else "Not Found"
        
        table_data.append(row_data)
    
    return table_data

def extract_general_fields(rows, regions):
    """Extract general fields from rows in the header and customer regions."""
    patterns = {
        "invoice_number": r"(?:invoice\s*(?:number|#|no\.?|no\s*:))\s*[:\s#]*([\w\d-]+)|no\s*:\s*([\d]{8})|([\d]{8})",
        "invoice_date": r"(?:invoice\s*)?date\s*[:\s]*(?:\s*of\s*issue\s*[:\s]*)?(\w+\s+\d{1,2},\s+\d{4})|date\s*(?:of issue\s*)?[:\s]*(\d{2}/\d{2}/\d{4})|(\d{4}-\d{2}-\d{2})|(\d{2}-\d{2}-\d{4})|(\d{2}\s+\w+\s+\d{4})|(\d{2}\.\d{2}\.\d{4})|(\d{2}/\d{2}/\d{2})",
        "supplier_gst_number": r"(?:supplier|vendor|seller)\s*(?:gst(?:in)?|tax\s*id|abn)\s*[:\-]?\s*([\d\s-]+)",
        "bill_to_gst_number": r"(?:bill\s*to|customer|client)\s*(?:gst(?:in)?|tax\s*id)\s*[:\-]?\s*([\d\s-]+)",
        "po_number": r"(?:po|purchase\s*order|order)\s*(?:no|number|#|id)\s*[:\-]?\s*([\w\d-]+)",
        "shipping_address": r"(?:bill\s*to|ship\s*to|customer\s*name\s*[:\s]*|client\s*[:\s]*|attention\s*to\s*)(.*?)(?=(?:invoice\s*(?:number|date)|description\s*from\s*until|items|no\.|tax\s*id|iban|abn|$))"
    }
    
    fields = {}
    header_text = ' '.join([' '.join([e['text'] for e in rows[i]]) for i in regions["header"]])
    customer_text = ' '.join([' '.join([e['text'] for e in rows[i]]) for i in regions["customer"]])
    all_text = header_text + ' ' + customer_text
    
    # Invoice date from header only
    date_match = re.search(patterns["invoice_date"], header_text, re.IGNORECASE)
    if date_match:
        fields["invoice_date"] = next(group for group in date_match.groups() if group is not None).strip()
    else:
        fields["invoice_date"] = "Not Found"
    
    inv_match = re.search(patterns["invoice_number"], header_text, re.IGNORECASE)
    if inv_match:
        fields["invoice_number"] = next(group for group in inv_match.groups() if group is not None).strip()
    else:
        fields["invoice_number"] = "Not Found"
    
    # Capture supplier and bill-to GST numbers
    supplier_gst_match = re.search(patterns["supplier_gst_number"], all_text, re.IGNORECASE)
    fields["supplier_gst_number"] = supplier_gst_match.group(1).strip() if supplier_gst_match else "Not Found"
    
    bill_to_gst_match = re.search(patterns["bill_to_gst_number"], all_text, re.IGNORECASE)
    fields["bill_to_gst_number"] = bill_to_gst_match.group(1).strip() if bill_to_gst_match else "Not Found"
    
    for field in ["po_number", "shipping_address"]:
        match = re.search(patterns[field], all_text, re.IGNORECASE | re.DOTALL)
        if match:
            fields[field] = next(group for group in match.groups() if group is not None).strip()
            if field == "shipping_address":
                # Clean up shipping address
                fields[field] = re.sub(r'(?:seller|vendor|johnson\s*plc|tax\s*id\s*[:\s]*[\d-]+|iban\s*[:\s]*.*?$|abn\s*[\d\s]+)', '', fields[field], flags=re.IGNORECASE).strip()
        else:
            fields[field] = "Not Found"
    
    return fields

def extract_vendor_customer_info(rows, regions):
    """Extract vendor and customer information using spatial regions."""
    vendor_info = {
        "company_name": "Not Found",
        "address": [],
        "phone": "Not Found",
        "website": "Not Found"
    }
    customer_info = {
        "customer_name": "Not Found",
        "address": []
    }
    
    # Vendor info
    vendor_text = ' '.join([' '.join([e['text'] for e in rows[i]]) for i in regions["vendor"]])
    company_pattern = r"(?:[A-Za-z\s]+\s*(?:Pty\. Ltd\.|Inc\.|LLC|PLC|WOODWORK))|(?:[A-Za-z\s]+Equipment)"
    phone_pattern = r"(?:\+\d{1,3}\s*)?(?:\d{1,4}[\s-])?\d{3}[\s-]\d{3}[\s-]\d{4}|\d{10}|\(\d{2,3}\)\s*\d{7,8}"
    website_pattern = r"www\.[a-zA-Z0-9]+\.[a-zA-Z]{2,}|(?:[a-zA-Z0-9]+\.)*(?:com|org|net)"
    
    company_match = re.search(company_pattern, vendor_text, re.IGNORECASE)
    if company_match:
        vendor_info["company_name"] = company_match.group().strip()
    
    phone_match = re.search(phone_pattern, vendor_text)
    if phone_match:
        vendor_info["phone"] = phone_match.group()
    
    website_match = re.search(website_pattern, vendor_text)
    if website_match:
        vendor_info["website"] = website_match.group()
    
    address_lines = []
    for i in regions["vendor"]:
        row_text = ' '.join([e['text'] for e in rows[i]])
        if row_text.strip() and not re.search(r"(?:invoice|date|number|client|seller|no\s*:)", row_text, re.IGNORECASE):
            if vendor_info["company_name"] not in row_text and vendor_info["website"] not in row_text and vendor_info["phone"] not in row_text:
                address_lines.append(row_text.strip())
    vendor_info["address"] = address_lines if address_lines else ["Not Found"]
    
    # Customer info
    customer_text = ' '.join([' '.join([e['text'] for e in rows[i]]) for i in regions["customer"]])
    customer_name_pattern = r"(?:bill\s*to|ship\s*to|customer\s*name\s*[:\s]*|client\s*[:\s]*|attention\s*to\s*)([A-Za-z\s-]+?)(?=\s*(?:tax\s*id|address|\d{3,}|$))"
    customer_name_match = re.search(customer_name_pattern, customer_text, re.IGNORECASE)
    if customer_name_match:
        full_name = customer_name_match.group(1).strip()
        customer_info["customer_name"] = full_name.replace('Seller:', '').replace('Client:', '').replace('Johnson PLC', '').strip()
    
    customer_address = []
    for i in regions["customer"]:
        row_text = ' '.join([e['text'] for e in rows[i]])
        if re.search(r"(?:invoice\s*(?:date|date\s*of\s*issue|number)|total|description\s*from\s*until|items|no\.|tax\s*id|iban|worth|\d+\.\s+\w+|\d+\s+\w+|summary|\d+%\s*\d|payment\s*info|account|bank\s*details|terms)", row_text, re.IGNORECASE):
            continue
        if row_text.strip() and not re.search(r"(?:seller|client|attention\s*to)", row_text.lower()):
            customer_address.append(row_text.strip())
    customer_info["address"] = customer_address if customer_address else ["Not Found"]
    
    return vendor_info, customer_info

def extract_additional_info(rows, regions):
    """Extract payment terms and bank details from footer region."""
    additional_info = {
        "payment_terms": "Not Found",
        "bank_details": {}
    }
    
    footer_text = ' '.join([' '.join([e['text'] for e in rows[i]]) for i in regions["footer"]])
    
    payment_terms_pattern = r"payment\s*due\s*[:\s]*(.*?)(?=\s*(?:description|total|bank|$))"
    payment_match = re.search(payment_terms_pattern, footer_text, re.IGNORECASE)
    if payment_match:
        additional_info["payment_terms"] = payment_match.group(1).strip()
    
    bank_patterns = {
        "account_name": r"(?:account\s*name|bank\s*account\s*name)[:\s]*(.*?)(?=\s*(?:bank\s*name|bsb|$))",
        "bank_name": r"(?:bank\s*name|name\s*of\s*bank|bank\s*details)[:\s]*(.*?)(?=\s*(?:bsb|account\s*number|bank\s*address|$))",
        "account_number": r"account\s*(?:number)[:\s]*([\d-]+)",
        "swift_code": r"swift\s*code[:\s]*([A-Z0-9]+)",
        "iban": r"iban\s*[:\s]*([A-Z0-9]+)"
    }
    
    bank_details = {}
    for key, pattern in bank_patterns.items():
        match = re.search(pattern, footer_text, re.IGNORECASE)
        bank_details[key] = match.group(1).strip() if match else "Not Found"
    
    additional_info["bank_details"] = bank_details
    return additional_info

def extract_totals(rows, table_contents, regions):
    """Extract total fields from rows after the table and compute subtotal from line items."""
    total_patterns = {
        "subtotal": r"(?:sub ?total|total before tax|net amount)\s*[:\-]?\s*\$?([\d.,]+)",
        "discount": r"(?:discount|less|deduction|deduct)\s*[:\-]?\s*\$?([\d.,]+)",
        "gst": r"(?:gst|tax|vat|cgst|sgst|igst|sales\s*tax)\s*(?:\d+\%)?\s*[:\-]?\s*\$?([\d.,]+)",
        "final_total": r"(?:total|grand total|amount due|final amount|total due)\s*[:\-]?\s*([A-Za-z\s]*\$[\d.,]+|[\d.,]+)",
        "summary_totals": r"vat\s*\[\%\]\s*net\s*worth\s*vat\s*gross\s*worth\s*(\d+)%\s*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)|(\d+)%\s*([\d.,]+)\s*([\d.,]+)\s*([\d.,]+)"
    }
    
    totals = {}
    # Initialize totals
    totals['subtotal'] = 0.0
    totals['gst'] = 0.0
    totals['discount'] = 0.0
    totals['final_total'] = 0.0
    totals['summary_totals'] = 0.0
    
    # Compute from table contents if available
    if table_contents:
        subtotal = sum(item.get('net_worth', item.get('total_amount', 0.0)) for item in table_contents)
        totals['subtotal'] = subtotal
        gst = 0.0
        for item in table_contents:
            if 'vat' in item and 'net_worth' in item:
                gst += (item['vat'] / 100) * item['net_worth']
        totals['gst'] = round(gst, 2)
    
    # Extract totals from footer
    text_after_table = ' '.join([' '.join([e['text'] for e in rows[i]]) for i in regions["footer"]])
    for field, pattern in total_patterns.items():
        match = re.search(pattern, text_after_table, re.IGNORECASE)
        if match:
            if field == "summary_totals":
                groups = [g for g in match.groups() if g is not None]
                totals['subtotal'] = float(groups[-3].replace(',', '.'))
                totals['gst'] = float(groups[-2].replace(',', '.'))
                totals['final_total'] = float(groups[-1].replace(',', '.'))
            else:
                value = match.group(1).replace(',', '.').replace('USD', '').replace('$', '').strip()
                try:
                    totals[field] = float(value) if value else 0.0
                except ValueError as e:
                    logging.warning(f"Failed to convert total '{field}' value '{value}': {str(e)}")
                    totals[field] = 0.0
    
    if totals['final_total'] == 0.0 and table_contents:
        totals['final_total'] = totals['subtotal'] + totals['gst'] - totals.get('discount', 0.0)
    
    return totals

def parse_invoice_data(all_elements):
    """Parse invoice data from OCR elements across all pages."""
    invoice_data = {
        "general_information": {},
        "vendor_information": {},
        "customer_information": {},
        "table_contents": [],
        "no_items": 0,
        "totals": {},
        "additional_information": {}
    }
    
    for page_elements in all_elements:
        rows = group_into_rows(page_elements)
        regions = define_regions(rows)
        
        if not invoice_data["general_information"]:
            invoice_data["general_information"] = extract_general_fields(rows, regions)
            invoice_data["general_information"]["seal_and_sign_present"] = False
        
        vendor_info, customer_info = extract_vendor_customer_info(rows, regions)
        invoice_data["vendor_information"] = vendor_info
        invoice_data["customer_information"] = customer_info
        
        invoice_data["additional_information"] = extract_additional_info(rows, regions)
        
        table_start_index, header_row, header_keywords = find_table_header(rows, regions)
        if table_start_index is not None:
            table_data = parse_table(rows, header_row, header_keywords, table_start_index)
            invoice_data["table_contents"].extend(table_data)
        else:
            logging.warning("No table header found on this page.")
        
        invoice_data["totals"].update(extract_totals(rows, invoice_data["table_contents"], regions))
    
    invoice_data["no_items"] = len(invoice_data["table_contents"])
    return invoice_data