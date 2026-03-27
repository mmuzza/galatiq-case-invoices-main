# To run: PYTHONPATH=. pytest -v tests/test_approval.py


import pytest
from unittest.mock import MagicMock
from schemas.invoice_schema import Invoice, LineItem
from agents.approval_agent import approval_agent


invoice = Invoice(
    invoice_number="INV-001",
    vendor="Test Vendor",
    items=[LineItem(item="WidgetA", quantity=2, unit_price=100.0)],
    total_amount=200.0,
    date="2026-03-01",
    due_date="2026-03-10"
)


mock_response = MagicMock()
mock_response.choices = [
    MagicMock(message=MagicMock(content='{"vp_review_required": true, "summary": "Needs VP review", "reasoning": ["Invoice total is high"]}'))
]

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.chat.completions.create.return_value = mock_response
    return client


# Test: VP review triggered by validation errors
def test_approval_agent_with_errors(mock_client):
    validation_result = {"errors": ["Negative quantity detected"]}
    
    result = approval_agent(validation_result, invoice, mock_client)
    
    assert result["vp_review_required"] is True
    assert "Negative quantity detected" in result["reasoning"] or "Invoice total is high" in result["reasoning"]
    assert isinstance(result["reasoning"], list)
    assert "summary" in result


# Test: VP review triggered by high total
def test_approval_agent_high_invoice_total(mock_client):
    high_invoice = Invoice(
        invoice_number="INV-002",
        vendor="Big Vendor",
        items=[LineItem(item="WidgetA", quantity=200, unit_price=100.0)],
        total_amount=20_000.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    
    validation_result = {"errors": []}
    result = approval_agent(validation_result, high_invoice, mock_client)
    
    assert result["vp_review_required"] is True
    assert any("high" in r.lower() for r in result["reasoning"])

# -----------------------------
# Test: No errors, normal invoice
# -----------------------------
def test_approval_agent_normal_invoice(mock_client):
    validation_result = {"errors": []}
    
    normal_invoice = Invoice(
        invoice_number="INV-003",
        vendor="Small Vendor",
        items=[LineItem(item="WidgetA", quantity=1, unit_price=50.0)],
        total_amount=50.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )
    
    result = approval_agent(validation_result, normal_invoice, mock_client)
    
    assert result["vp_review_required"] is True  # Because our mock LLM response returns true
    assert isinstance(result["reasoning"], list)
    assert "summary" in result