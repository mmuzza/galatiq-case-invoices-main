# TO RUN ENTER IN TERMINAL: PYTHONPATH=. pytest -v tests/test_normalization.py

import pytest
from unittest.mock import MagicMock
from agents.normalization_agent import normalize_invoice
from schemas.invoice_schema import Invoice, LineItem

invoice_clean = """
INVOICE
Vendor: Widgets Inc.
Invoice Number: INV-1001
Date: 2026-01-15
Due Date: 2026-02-01
Items:
  WidgetA qty: 10 unit price: $250.00
Subtotal: $5000.00
"""

invoice_multiple_items = """
INVOICE
Vendor: Gadgets Co.
Invoice Number: INV-2002
Date: 2026-03-10
Due Date: 2026-03-25
Items:
  GadgetX qty: 5 unit price: $100.00
  GadgetY qty: 2 unit price: $300.00
Subtotal: $1100.00
"""

invoice_missing_due_date = """
INVOICE
Vendor: Supplies Ltd.
Invoice Number: INV-3003
Date: 2026-04-01
Items:
  Paper qty: 50 unit price: $2.00
Subtotal: $100.00
"""

invoice_messy = """
INVOICE


Vendor : Widgets Inc.

Invoice Number: INV-4004


Date: 2026-05-05
Due Date: 2026-05-20

Items:
    WidgetB    qty:3  unit price: $150.00  
    WidgetC qty :  7 unit price : $50.00

Subtotal: $750.00
"""

@pytest.fixture
def gpt_client():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"invoice_number": "INV-1001", "vendor": "Widgets Inc.", "items": [{"item": "WidgetA","quantity":10,"unit_price":250.0}], "total_amount": 5000.0, "due_date": "2026-02-01"}'))
    ]
    client.chat.completions.create.return_value = mock_response
    return client

def test_normalize_clean_invoice(gpt_client):
    normalized = normalize_invoice(invoice_clean, gpt_client)
    assert isinstance(normalized, Invoice)
    assert normalized.invoice_number == "INV-1001"
    assert normalized.vendor == "Widgets Inc."
    assert len(normalized.items) == 1
    assert normalized.total_amount == 5000.0
    assert normalized.due_date == "2026-02-01"


@pytest.fixture
def gpt_client_multiple_items():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"invoice_number": "INV-2002", "vendor": "Gadgets Co.", "items": [{"item":"GadgetX","quantity":5,"unit_price":100.0},{"item":"GadgetY","quantity":2,"unit_price":300.0}], "total_amount": 1100.0, "due_date": "2026-03-25"}'))
    ]
    client.chat.completions.create.return_value = mock_response
    return client

@pytest.fixture
def gpt_client_missing_due():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"invoice_number": "INV-3003", "vendor": "Supplies Ltd.", "items":[{"item":"Paper","quantity":50,"unit_price":2.0}], "total_amount":100.0, "due_date": null}'))
    ]
    client.chat.completions.create.return_value = mock_response
    return client

@pytest.fixture
def gpt_client_messy():
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"invoice_number": "INV-4004", "vendor": "Widgets Inc.", "items":[{"item":"WidgetB","quantity":3,"unit_price":150.0},{"item":"WidgetC","quantity":7,"unit_price":50.0}], "total_amount":750.0, "due_date": "2026-05-20"}'))
    ]
    client.chat.completions.create.return_value = mock_response
    return client

def test_normalize_multiple_items(gpt_client_multiple_items):
    normalized = normalize_invoice(invoice_multiple_items, gpt_client_multiple_items)
    assert isinstance(normalized, Invoice)
    assert normalized.invoice_number == "INV-2002"
    assert normalized.vendor == "Gadgets Co."
    assert len(normalized.items) == 2
    assert normalized.total_amount == 1100.0
    assert normalized.due_date == "2026-03-25"

def test_normalize_missing_due_date(gpt_client_missing_due):
    normalized = normalize_invoice(invoice_missing_due_date, gpt_client_missing_due)
    assert isinstance(normalized, Invoice)
    assert normalized.invoice_number == "INV-3003"
    assert normalized.vendor == "Supplies Ltd."
    assert len(normalized.items) == 1
    assert normalized.total_amount == 100.0
    assert normalized.due_date is None

def test_normalize_messy_invoice(gpt_client_messy):
    normalized = normalize_invoice(invoice_messy, gpt_client_messy)
    assert isinstance(normalized, Invoice)
    assert normalized.invoice_number == "INV-4004"
    assert normalized.vendor == "Widgets Inc."
    assert len(normalized.items) == 2
    assert normalized.total_amount == 750.0
    assert normalized.due_date == "2026-05-20"