
# TO RUN ENTER IN TERMINAL: PYTHONPATH=. pytest -v tests/test_validation.py

import pytest
from schemas.invoice_schema import Invoice, LineItem
from agents.validation_agent import validate_invoice
import tempfile
import sqlite3

# -------------------------------
# Setup temporary inventory DB
# -------------------------------
def setup_inventory_db():
    db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    conn = sqlite3.connect(db.name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE inventory (
            item TEXT PRIMARY KEY,
            stock INTEGER
        )
    """)
    inventory_items = [
        ("WidgetA", 10),
        ("WidgetB", 5),
        ("GadgetX", 8),
    ]
    cursor.executemany("INSERT INTO inventory (item, stock) VALUES (?, ?)", inventory_items)
    conn.commit()
    conn.close()
    return db.name

DB_PATH = setup_inventory_db()



# -------------------------------
# Test Cases
# -------------------------------

# 1. Vendor missing
def test_vendor_missing():
    invoice = Invoice(
        invoice_number="INV-001",
        vendor="",
        items=[LineItem(item="WidgetA", quantity=1, unit_price=100.0)],
        total_amount=100.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert "Vendor is missing" in result["errors"]

# 2. Item not in inventory
def test_item_not_in_inventory():
    invoice = Invoice(
        invoice_number="INV-002",
        vendor="Test Vendor",
        items=[LineItem(item="UnknownItem", quantity=1, unit_price=50.0)],
        total_amount=50.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert "Item 'UnknownItem' not found in inventory" in result["errors"]

# 3. Negative quantity
def test_negative_quantity():
    invoice = Invoice(
        invoice_number="INV-003",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=-5, unit_price=100.0)],
        total_amount=-500.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert any("Negative quantity" in e for e in result["errors"])
    assert "Total amount cannot be negative" in result["errors"]

# 4. Quantity exceeds stock
def test_quantity_exceeds_stock():
    invoice = Invoice(
        invoice_number="INV-004",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=20, unit_price=100.0)],  # stock = 10
        total_amount=2000.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert any("exceeds stock" in e for e in result["errors"])

# 5. Due date missing
def test_due_date_missing():
    invoice = Invoice(
        invoice_number="INV-005",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=1, unit_price=100.0)],
        total_amount=100.0,
        date="2026-03-01",
        due_date=None
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert "Due date is missing" in result["errors"]

# 6. Due date before invoice date
def test_due_date_before_invoice():
    invoice = Invoice(
        invoice_number="INV-006",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=1, unit_price=100.0)],
        total_amount=100.0,
        date="2026-03-10",
        due_date="2026-03-05"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert any("Due date" in e and "before invoice date" in e for e in result["errors"])

# 7. Tax amount mismatch
def test_tax_amount_mismatch():
    invoice = Invoice(
        invoice_number="INV-007",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=2, unit_price=100.0)],
        total_amount=210.0,
        tax_rate=0.1,
        tax_amount=5.0,  # Should be 20.0
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert "Tax amount does not match tax rate applied to subtotal" in result["errors"]

# 8. Negative shipping
def test_negative_shipping():
    invoice = Invoice(
        invoice_number="INV-008",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=1, unit_price=100.0)],
        total_amount=90.0,
        shipping=-10.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert "Shipping amount cannot be negative" in result["errors"]

# 9. Total amount mismatch
def test_total_amount_mismatch():
    invoice = Invoice(
        invoice_number="INV-009",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=1, unit_price=100.0)],
        total_amount=150.0,  # Should be 100.0
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert not result["valid"]
    assert "Total amount does not match sum of line items plus tax and shipping" in result["errors"]

# 10. Valid invoice
def test_valid_invoice():
    invoice = Invoice(
        invoice_number="INV-010",
        vendor="Valid Vendor",
        items=[LineItem(item="WidgetA", quantity=2, unit_price=100.0)],
        total_amount=200.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    result = validate_invoice(invoice, DB_PATH)
    assert result["valid"]
    assert len(result["errors"]) == 0