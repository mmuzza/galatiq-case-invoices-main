
# Pydantic for converting the fields from the invoice into correct types incase LLM does not

from pydantic import BaseModel
from typing import List, Optional


class LineItem(BaseModel):
    item: str
    quantity: int
    unit_price: float
    canonical_item: Optional[str] = None


class Invoice(BaseModel):
    invoice_number: Optional[str] = ""
    vendor: Optional[str] = ""
    items: List[LineItem] = []
    total_amount: float = 0.0
    date: Optional[str] = ""
    due_date: Optional[str] = ""
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    shipping: float = 0.0
