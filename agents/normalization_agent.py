
import json
import csv
from typing import Any, Dict
from schemas.invoice_schema import Invoice, LineItem
import os
from utils.parser import load_invoice_file



MAX_RETRIES = 3 # For self correction loop we will try to regenerate answer 3 times from LLM if pydantic fails

# Sending Prompt to tell the LLM to extract the JSON in the desired format to normalize across all files
def normalize_invoice(raw_input: str, client) -> Dict[str, Any]:


    prompt = f"""
You are an expert invoice parser.
Extract the following fields from the invoice, even if the invoice is messy, contains typos, abbreviations, missing labels, or unusual formatting.

Even if a field in the input is a nested dictionary or has extra data,
only extract the requested field values in the following format:


- invoice_number: string
- vendor: string (use the name only)
- items: list of {{item, quantity, unit_price}}
- total_amount: number
- date: string
- due_date: string
- tax_rate: number
- tax_amount: number
- shipping: number

Make sure that the date and due date both follow the format in the example


Return JSON only. Example:

{{
  "invoice_number": "INV-1001",
  "vendor": "Widgets Inc.",
  "items": [
    {{"item": "WidgetA", "quantity": 10, "unit_price": 250.0}},
    {{"item": "WidgetB", "quantity": 5, "unit_price": 500.0}}
  ],
  "total_amount": 5000.0,
  "date": "2026-03-04"
  "due_date": "2026-02-01"
  "tax_rate": 0.08
  "tax_amount": 400
  "shipping": 0
}}

Invoice text/content:
{raw_input}
"""

    # Self correction Loop == 3 times max
    for attempt in range(1, MAX_RETRIES + 1):
        # Sending request to LLM:

        # response = client.chat.completions.create(
        #     model="grok-3",
        #     messages=[{"role": "user", "content": prompt}]
        # )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )


        # Parsing LLM JSON output
        try:
            extracted = json.loads(response.choices[0].message.content)
        except Exception as e:
            print("Error parsing LLM output:", e)
            extracted = {}

        # Validating and converting using Pydantic
        # Incase the LLM hallucinates and produces wrong json, or empty fields
        # So we ground it by comparing to invoice schema
        # It will fix the wrong type, missing values and etc
        try:
            invoice_obj = Invoice(**extracted)
            return invoice_obj
        except Exception as e:
            print(f"[Attempt {attempt}] Pydantic validation error:", e)
            prompt_template = f"""
    Previous extraction failed validation: {extracted}

    Please re-extract the invoice fields correctly in JSON format,
    ensuring all required fields match the types below:

    - invoice_number: string
    - vendor: string
    - items: list of {{item, quantity, unit_price}}
    - total_amount: number
    - date: string
    - due_date: string
    - tax_rate: number
    - tax_amount: number
    - shipping: number

    Invoice text/content:
    {raw_input}
    """


    # return invoice_obj.dict()

    return {"error": "Max retries exceeded, failed to normalize invoice", "raw": extracted}
    
    
