import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, JSON
from .database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REVIEW, REJECTED
    
    # AI / Rule decisions
    system_decision = Column(String(20), nullable=True)  # APPROVE, REVIEW, REJECT
    rule_score = Column(Float, default=100.0)
    rationale = Column(Text, nullable=True)

    # Human review workflow
    human_decision = Column(String(20), nullable=True)  # APPROVE, REVIEW, REJECT
    human_notes = Column(Text, nullable=True)
    human_decided_at = Column(DateTime, nullable=True)

    # High-level summary
    vendor_name = Column(String(255), nullable=True)
    invoice_number = Column(String(100), nullable=True, index=True)
    po_number = Column(String(100), nullable=True, index=True)
    invoice_total = Column(Float, nullable=True)
    po_total = Column(Float, nullable=True)
    currency = Column(String(10), default="INR")

    # Document details
    invoice_filename = Column(String(255), nullable=True)
    po_filename = Column(String(255), nullable=True)

    # Structured extractions & results
    invoice_data = Column(JSON, nullable=True)
    po_data = Column(JSON, nullable=True)
    discrepancies = Column(JSON, nullable=True)
