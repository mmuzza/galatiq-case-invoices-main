
# Running into minor issues with names of the items
# for example widgeta is formatted as widget A or WidgetA (rush) or gadget X which are not matching against inventory mock database
# To resolve that we will use canonical

import re
import unicodedata
import sqlite3


def canonicalize(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]", "", text) 
    return text



def load_inventory_canonical(db_path: str) -> dict:
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    inventory = {}
    cursor.execute("SELECT item, stock FROM inventory")
    for item, stock in cursor.fetchall():
        canon_item = canonicalize(item)
        inventory[canon_item] = item
    
    conn.close()
    return inventory



def check_canonical_item(invoice_canonical_item: str, canonical_inventory: dict):

    canonical_item = canonicalize(invoice_canonical_item)


    if canonical_item in canonical_inventory:
        # print("cannnonical item: ", canonical_inventory[canonical_item])
        return canonical_inventory[canonical_item]


    for inv_canonical, inv_orig in canonical_inventory.items():
        if canonical_item.startswith(inv_canonical):
            return inv_orig

    return None




def apply_canonical_to_invoice(invoice_obj, canonical_inventory):

    for item in invoice_obj.items:
        matched_name = check_canonical_item(item.item, canonical_inventory)
        if matched_name:
            item.canonical_item = matched_name
        else:
            item.canonical_item = None
