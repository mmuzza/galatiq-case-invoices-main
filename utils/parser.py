
# Reading in files (.txt, .json, .pdf, .csv)

import json
import pdfplumber
from schemas.invoice_schema import Invoice



def load_invoice_file(path: str):
    if path.endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages)
    elif path.endswith((".txt", ".csv", ".xml")):
        with open(path, "r") as f:
            return f.read()
    else:
        raise ValueError(f"File type not supported: {path}")



def load_json_invoice(file_path: str) -> Invoice:
    with open(file_path, "r") as f:
        data = json.load(f)

    invoice_data = {
        "invoice_number": data.get("invoice_number", ""),
        "vendor": data.get("vendor", {}).get("name", ""),
        "items": [
            {
                "item": li.get("item") or li.get("name", ""),
                "quantity": li.get("quantity", 0),
                "unit_price": li.get("unit_price", 0.0),
            }
            for li in data.get("line_items", [])
        ],
        "total_amount": data.get("total", 0.0),
        "date": data.get("date", ""),
        "due_date": data.get("due_date", ""),
        "tax_rate": data.get("tax_rate", 0.0),
        "tax_amount": data.get("tax_amount", 0.0),
        "shipping": data.get("shipping", 0.0)
    }

    return Invoice(**invoice_data)