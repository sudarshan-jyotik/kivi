import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Review
from ..schemas import ReviewResponse
from ..services.document_parser import parse_pdf_bytes
from ..services.sarvam_extractor import extract_document_data
from ..services.matching_engine import match_documents
from ..services.decision_engine import compute_rule_decision, generate_rationale

router = APIRouter(prefix="/demo", tags=["Demo"])

# Determine samples directory path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
SAMPLES_DIR = os.path.join(PROJECT_ROOT, "samples")


@router.post("/{sample_number}", response_model=ReviewResponse)
async def run_demo_sample(sample_number: int, db: Session = Depends(get_db)):
    """
    Runs an end-to-end audit demonstration using pre-generated sample PDF pairs:
    1: Clean Match -> APPROVE
    2: Price/Qty Mismatch + Wrong GST -> REJECT/REVIEW
    3: Extra Line Item + Total Mismatch -> REVIEW
    """
    if sample_number not in [1, 2, 3]:
        raise HTTPException(status_code=400, detail="Sample number must be 1, 2, or 3.")

    inv_path = os.path.join(SAMPLES_DIR, f"sample_{sample_number}_invoice.pdf")
    po_path = os.path.join(SAMPLES_DIR, f"sample_{sample_number}_po.pdf")

    if not os.path.exists(inv_path) or not os.path.exists(po_path):
        raise HTTPException(
            status_code=404,
            detail=f"Sample files for #{sample_number} not found. Run python scripts/generate_samples.py first."
        )

    with open(inv_path, "rb") as f:
        invoice_bytes = f.read()
    with open(po_path, "rb") as f:
        po_bytes = f.read()

    inv_filename = os.path.basename(inv_path)
    po_filename = os.path.basename(po_path)

    # 1. Parse PDFs
    parsed_invoice = parse_pdf_bytes(invoice_bytes, inv_filename)
    parsed_po = parse_pdf_bytes(po_bytes, po_filename)

    # 2. Extract with Sarvam AI
    try:
        invoice_data = await extract_document_data(parsed_invoice.full_text, doc_type_hint="INVOICE")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI extraction failed for demo invoice: {str(e)}")

    try:
        po_data = await extract_document_data(parsed_po.full_text, doc_type_hint="PURCHASE_ORDER")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI extraction failed for demo PO: {str(e)}")

    # 3. Duplicate invoice check
    existing = db.query(Review).filter(
        Review.invoice_number == invoice_data.document_number,
        Review.vendor_name.ilike(f"%{invoice_data.vendor_name.strip()}%")
    ).first()
    is_duplicate = existing is not None

    # 4. Match
    discrepancies = match_documents(
        invoice_data=invoice_data,
        po_data=po_data,
        invoice_doc=parsed_invoice,
        po_doc=parsed_po,
        is_duplicate_invoice=is_duplicate
    )

    # 5. Rule Decision + Sarvam Rationale
    rule_decision, rule_score = compute_rule_decision(discrepancies)
    rationale = await generate_rationale(
        decision=rule_decision,
        score=rule_score,
        discrepancies=discrepancies,
        invoice_data=invoice_data,
        po_data=po_data
    )

    # 6. Save
    review = Review(
        status=rule_decision,
        system_decision=rule_decision,
        rule_score=rule_score,
        rationale=rationale,
        vendor_name=invoice_data.vendor_name,
        invoice_number=invoice_data.document_number,
        po_number=po_data.document_number,
        invoice_total=invoice_data.grand_total,
        po_total=po_data.grand_total,
        currency=invoice_data.currency or "INR",
        invoice_filename=inv_filename,
        po_filename=po_filename,
        invoice_data=invoice_data.model_dump(),
        po_data=po_data.model_dump(),
        discrepancies=[d.model_dump() for d in discrepancies]
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return review
