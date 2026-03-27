
def mock_payment(vendor, amount):
    # print(f"Paid {amount} to {vendor}")
    return {
        "message": f"Paid {amount} to {vendor}",
        "status": "success"
    }


def payment(invoice_obj, validation_result, approval_result):

    # If validation failed -> block payment
    if not validation_result.get("valid", False):
        return {
            "status": "blocked",
            "reason": "Validation failed",
            "details": validation_result.get("errors", [])
        }

    # If VP review required -> block payment
    if approval_result.get("vp_review_required", False):
        return {
            "status": "pending_vp_review",
            "reason": "Invoice requires VP approval before payment"
        }

    # Otherwise → process payment
    result = mock_payment(invoice_obj.vendor, invoice_obj.total_amount)

    return result
