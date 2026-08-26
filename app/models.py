from typing import Optional
from pydantic import BaseModel, Field

class ExtractedLine(BaseModel):
    description: str
    quantity: Optional[int] = None
    unit: Optional[str] = None
    unit_price: Optional[int] = None
    amount: int

class ExtractedTax(BaseModel):
    tax_rate_text: Optional[str] = None
    taxable_amount: Optional[int] = None
    tax_amount: Optional[int] = None

class RawExtraction(BaseModel):
    supplier_name: Optional[str] = None
    registration_no: Optional[str] = None
    invoice_number: Optional[str] = None
    issue_date_raw: Optional[str] = None
    due_date_raw: Optional[str] = None
    currency: Optional[str] = "JPY"
    lines: list[ExtractedLine] = Field(default_factory=list)
    taxes: list[ExtractedTax] = Field(default_factory=list)

    printed_subtotal: Optional[int] = None
    printed_tax_amount: Optional[int] = None
    printed_total_amount: Optional[int] = None

class NormalizedLine(BaseModel):
    description: str
    quantity: Optional[int] = None
    unit: str
    unit_price: Optional[int] = None
    amount: int
    tax_code: str

class NormalizedInvoice(BaseModel):
    partner_code: str
    invoice_number: str
    issue_date: str
    due_date: str
    lines: list[NormalizedLine]
    subtotal: int
    tax_amount: int
    total_amount: int

class VerificationResult(BaseModel):
    passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class ProcessingResult(BaseModel):
    filename: str
    status: str

    raw_extraction: Optional[RawExtraction] = None
    normalized_invoice: Optional[NormalizedInvoice] = None
    verification: Optional[VerificationResult] = None

    accounting_result: Optional[dict] = None

    error_code: Optional[str] = None
    error_message: Optional[str] = None