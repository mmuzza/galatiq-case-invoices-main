# TO TEST: PYTHONPATH=. pytest -v tests/test_payment.py 

import pytest
from agents.payment_agent import payment, mock_payment
from schemas.invoice_schema import Invoice, LineItem 


@pytest.fixture
def sample_invoice():
    return Invoice(
        invoice_number="INV-001",
        vendor="Test Vendor",
        items=[LineItem(item="WidgetA", quantity=1, unit_price=100.0)],
        total_amount=100.0,
        date="2026-03-01",
        due_date="2026-03-10"
    )

def test_payment_blocked_by_validation(sample_invoice):
    validation_result = {"valid": False, "errors": ["Negative quantity detected"]}
    approval_result = {"vp_review_required": False}

    result = payment(sample_invoice, validation_result, approval_result)

    assert result["status"] == "blocked"
    assert result["reason"] == "Validation failed"
    assert "Negative quantity detected" in result["details"]

def test_payment_pending_vp_review(sample_invoice):
    validation_result = {"valid": True, "errors": []}
    approval_result = {"vp_review_required": True}

    result = payment(sample_invoice, validation_result, approval_result)

    assert result["status"] == "pending_vp_review"
    assert result["reason"] == "Invoice requires VP approval before payment"

def test_payment_success(sample_invoice):
    validation_result = {"valid": True, "errors": []}
    approval_result = {"vp_review_required": False}

    result = payment(sample_invoice, validation_result, approval_result)

    assert result["status"] == "success"
    assert result["message"] == f"Paid {sample_invoice.total_amount} to {sample_invoice.vendor}"