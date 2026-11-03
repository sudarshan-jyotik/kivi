from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from datetime import datetime


class LineItem(BaseModel):
    description: str = Field(..., description="Description of product or service")
    quantity: float = Field(..., description="Quantity ordered/billed")
    unit_price: float = Field(..., description="Price per unit")
    tax_rate: float = Field(default=0.0, description="GST / Tax percentage (e.g. 18.0 for 18%)")
    line_total: float = Field(..., description="Total line amount before or including tax")
    hsn_sac: Optional[str] = Field(None, description="HSN or SAC code if available")


class DocumentData(BaseModel):
    document_type: Optional[str] = Field(None, description="INVOICE or PURCHASE_ORDER")
    vendor_name: str = Field(..., description="Legal vendor or supplier name")
    document_number: str = Field(..., description="Invoice number or PO number")
    date: str = Field(..., description="Document date in YYYY-MM-DD or as written")
    gstin: Optional[str] = Field(None, description="GSTIN of supplier/vendor")
    currency: str = Field(default="INR", description="Currency code (e.g. INR)")
    subtotal: float = Field(..., description="Sum of line item amounts before tax")
    tax_details: Optional[Dict[str, float]] = Field(default_factory=dict, description="Breakup of CGST, SGST, IGST")
    total_tax: float = Field(default=0.0, description="Total tax amount")
    grand_total: float = Field(..., description="Final invoice or PO total amount")
    line_items: List[LineItem] = Field(default_factory=list, description="Extracted line items")


class DiscrepancyEvidence(BaseModel):
    source_document: str = Field(..., description="INVOICE or PURCHASE_ORDER")
    page_number: int = Field(1, description="Page number where discrepancy was detected")
    text_snippet: str = Field(..., description="Verbatim text quote from the document")


class Discrepancy(BaseModel):
    id: str = Field(..., description="Unique identifier for the discrepancy")
    type: str = Field(..., description="e.g. VENDOR_MISMATCH, LINE_ITEM_PRICE_MISMATCH, etc.")
    severity: str = Field(..., description="high, medium, or low")
    title: str = Field(..., description="Short descriptive title")
    description: str = Field(..., description="Detailed explanation of the issue")
    expected_value: Any = Field(None, description="Expected value from PO")
    actual_value: Any = Field(None, description="Actual value from Invoice")
    evidence: Optional[DiscrepancyEvidence] = Field(None, description="Source quote & page")


class DecisionRequest(BaseModel):
    decision: str = Field(..., description="approve, reject, or review")
    notes: Optional[str] = Field(None, description="Optional reviewer notes")


class ReviewSummary(BaseModel):
    id: str
    created_at: datetime
    status: str
    system_decision: Optional[str] = None
    human_decision: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    invoice_total: Optional[float] = None
    po_total: Optional[float] = None
    currency: str = "INR"
    discrepancy_count: int = 0
    high_severity_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(BaseModel):
    id: str
    created_at: datetime
    status: str
    system_decision: Optional[str] = None
    rule_score: float
    rationale: Optional[str] = None
    human_decision: Optional[str] = None
    human_notes: Optional[str] = None
    human_decided_at: Optional[datetime] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    po_number: Optional[str] = None
    invoice_total: Optional[float] = None
    po_total: Optional[float] = None
    currency: str = "INR"
    invoice_filename: Optional[str] = None
    po_filename: Optional[str] = None
    invoice_data: Optional[Dict[str, Any]] = None
    po_data: Optional[Dict[str, Any]] = None
    discrepancies: List[Discrepancy] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    database: str
