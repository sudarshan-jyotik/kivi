import os
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Review
from ..schemas import ReviewResponse, ReviewSummary, DecisionRequest
from ..services.document_parser import parse_pdf_bytes
from ..services.sarvam_extractor import extract_document_data
from ..services.matching_engine import match_documents
from ..services.decision_engine import compute_rule_decision, generate_rationale
from ..services.report_generator import generate_review_pdf

router = APIRouter(prefix="/reviews", tags=["Reviews"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _to_review_summary(r: Review) -> ReviewSummary:
    discrepancies = r.discrepancies or []
    high_count = sum(1 for d in discrepancies if d.get("severity") == "high")
    return ReviewSummary(
        id=r.id,
        created_at=r.created_at,
        status=r.status,
        system_decision=r.system_decision,
        human_decision=r.human_decision,
        vendor_name=r.vendor_name,
        invoice_number=r.invoice_number,
        po_number=r.po_number,
        invoice_total=r.invoice_total,
        po_total=r.po_total,
        currency=r.currency or "INR",
        discrepancy_count=len(discrepancies),
        high_severity_count=high_count
    )


@router.get("", response_model=List[ReviewSummary])
def list_reviews(
    db: Session = Depends(get_db),
    status: str = Query(None, description="Filter by status (APPROVED, REVIEW, REJECTED, PENDING)"),
    search: str = Query(None, description="Search by vendor or invoice/po number")
):
    query = db.query(Review)
    if status:
        query = query.filter(Review.status == status.upper())
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Review.vendor_name.ilike(s)) |
            (Review.invoice_number.ilike(s)) |
            (Review.po_number.ilike(s))
        )
    reviews = query.order_by(Review.created_at.desc()).all()
    return [_to_review_summary(r) for r in reviews]


@router.post("", response_model=ReviewResponse)
async def create_review(
    invoice: UploadFile = File(..., description="Invoice PDF document"),
    po: UploadFile = File(..., description="Purchase Order PDF document"),
    db: Session = Depends(get_db)
):
    # 1. Validate file types
    if not invoice.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invoice must be a PDF file.")
    if not po.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Purchase Order must be a PDF file.")

    # 2. Read bytes and check size (<= 10MB)
    invoice_bytes = await invoice.read()
    po_bytes = await po.read()

    if len(invoice_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"Invoice exceeds maximum size of 10MB ({len(invoice_bytes)/(1024*1024):.1f}MB).")
    if len(po_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"Purchase Order exceeds maximum size of 10MB ({len(po_bytes)/(1024*1024):.1f}MB).")

    # 3. Document text extraction (PyMuPDF with OCR fallback)
    try:
        parsed_invoice = parse_pdf_bytes(invoice_bytes, invoice.filename)
        parsed_po = parse_pdf_bytes(po_bytes, po.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF documents: {str(e)}")

    if not parsed_invoice.full_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in the Invoice PDF (even after OCR fallback).")
    if not parsed_po.full_text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in the Purchase Order PDF.")

    # 4. Extract structured JSON via Sarvam AI
    try:
        invoice_data = await extract_document_data(parsed_invoice.full_text, doc_type_hint="INVOICE")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Invoice data extraction failed: {str(e)}")

    try:
        po_data = await extract_document_data(parsed_po.full_text, doc_type_hint="PURCHASE_ORDER")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Purchase Order data extraction failed: {str(e)}")

    # 5. Check duplicate invoice in DB
    existing_duplicate = db.query(Review).filter(
        Review.invoice_number == invoice_data.document_number,
        Review.vendor_name.ilike(f"%{invoice_data.vendor_name.strip()}%")
    ).first()
    is_duplicate = existing_duplicate is not None

    # 6. Deterministic matching engine
    discrepancies = match_documents(
        invoice_data=invoice_data,
        po_data=po_data,
        invoice_doc=parsed_invoice,
        po_doc=parsed_po,
        is_duplicate_invoice=is_duplicate
    )

    # 7. Rule decision + Sarvam AI rationale
    rule_decision, rule_score = compute_rule_decision(discrepancies)
    rationale = await generate_rationale(
        decision=rule_decision,
        score=rule_score,
        discrepancies=discrepancies,
        invoice_data=invoice_data,
        po_data=po_data
    )

    # 8. Persist Review record
    review = Review(
        status=rule_decision,  # initial status matches system recommendation
        system_decision=rule_decision,
        rule_score=rule_score,
        rationale=rationale,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.document_number,
        po_number=po_data.document_number,
        invoice_total=invoice_data.grand_total,
        po_total=po_data.grand_total,
        currency=invoice_data.currency or "INR",
        invoice_filename=invoice.filename,
        po_filename=po.filename,
        invoice_data=invoice_data.model_dump(),
        po_data=po_data.model_dump(),
        discrepancies=[d.model_dump() for d in discrepancies]
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: str, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/{review_id}/decision", response_model=ReviewResponse)
def update_decision(
    review_id: str,
    payload: DecisionRequest,
    db: Session = Depends(get_db)
):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    dec = payload.decision.upper()
    if dec not in ["APPROVE", "REJECT", "REVIEW"]:
        raise HTTPException(status_code=400, detail="Decision must be 'APPROVE', 'REJECT', or 'REVIEW'")

    review.human_decision = dec
    review.human_notes = payload.notes
    review.human_decided_at = datetime.now(timezone.utc)
    
    # Map decision to status
    if dec == "APPROVE":
        review.status = "APPROVED"
    elif dec == "REJECT":
        review.status = "REJECTED"
    else:
        review.status = "REVIEW"

    db.commit()
    db.refresh(review)
    return review


@router.get("/{review_id}/report")
def download_report(review_id: str, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    pdf_bytes = generate_review_pdf(review)
    filename = f"AP_Report_{review.invoice_number or review.id}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
