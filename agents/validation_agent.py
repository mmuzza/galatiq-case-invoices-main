

import sqlite3
from schemas.invoice_schema import Invoice
from collections import defaultdict

# We create a list of errors and record any fields that can affect collecting payment for it.
# Later we will use these errors to determine if approval is needed via approval_agent
def validate_invoice(invoice: Invoice, db_path: str) -> dict:

    errors = []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    inventory = {}
    cursor.execute("SELECT item, stock FROM inventory")
    for row in cursor.fetchall():
        inventory[row[0]] = row[1]
    conn.close()


    # accumulate quantities by canonical name
    total_quantities = defaultdict(int)
    for item in invoice.items:
        key = item.canonical_item or item.item
        total_quantities[key] += item.quantity

    ###################################################################################
    

    # We will check for 8 major things to validate if invoice is corrrect:


    # 1. 
    # If no vendor exists
    if not invoice.vendor:
        errors.append("Vendor is missing")





    # 2. 
    # Checking if items exist and stock is enough
    # Whether we have enough stock to sell those items
    for item in invoice.items:

        inventory_key = item.canonical_item or item.item

        if item.quantity < 0:
            errors.append(f"Negative quantity for item {item.item}")

        
        if inventory_key not in inventory:
            errors.append(f"Item '{item.item}' not found in inventory")





    # 3.
    # Since same items are repeated on invoices due to rush or special orders
    # We make sure their quantity is combined with the same non rush / non special orders
    # Such as [WidgetA (rush order) : qt 10 : unit price 300] & [Widget A : qt 2 : unit price 250]==> total quantity == 12 and keep price separate
    for key in total_quantities:
        if key in inventory and total_quantities[key] > inventory[key]:
            errors.append(
                f"Total quantity for {key} ({total_quantities[key]}) exceeds stock ({inventory[key]})"
            )





    #4.
    # Make sure payment is not overdue: due date - invoice date > 0
    invoice_date = getattr(invoice, "date", None)
    due_date = getattr(invoice, "due_date", None)
    if not due_date:
        errors.append("Due date is missing")
    elif invoice_date and due_date < invoice_date:
        errors.append(f"Due date {due_date} is before invoice date {invoice_date}")





    # 5
    # If tax rate is applicable, need to make sure invoice has applied correct tax amount
    calculated_subtotal = sum(li.quantity * li.unit_price for li in invoice.items)
    expected_tax = 0

    if hasattr(invoice, "tax_rate") and invoice.tax_rate:
        expected_tax = round(calculated_subtotal * invoice.tax_rate, 2)
        if abs(expected_tax - invoice.tax_amount) > 0.01:
            errors.append("Tax amount does not match tax rate applied to subtotal")

        



    # 6
    # If shipping is applicable, need to make sure its positive amount
    expected_shipping = 0
    if hasattr(invoice, "shipping") and invoice.shipping:
        expected_shipping = invoice.shipping
        if expected_shipping < 0:
            errors.append("Shipping amount cannot be negative")





    # 7.
    # Subtotal, tax, shipping should all add up to the total amount of invoice otherwise invoice is incorrect
    calculated_total = calculated_subtotal + expected_tax + expected_shipping
    if abs(calculated_total - invoice.total_amount) > 0.01:
        errors.append("Total amount does not match sum of line items plus tax and shipping")
    




    # 8
    # Any amount that is not positive is an invoice error
    if invoice.total_amount < 0:
        errors.append("Total amount cannot be negative")
     




    # Return valid if no errors otherwise list of errors for next agent to decide if VP review is required
    return {"valid": len(errors) == 0, "errors": errors}