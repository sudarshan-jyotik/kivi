import os
import sys
import asyncio

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(ROOT_DIR, "backend", ".env"))

from app.services.document_parser import parse_pdf_bytes
from app.services.sarvam_extractor import extract_document_data
from app.services.matching_engine import match_documents
from app.services.decision_engine import compute_rule_decision, generate_rationale
from app.services.report_generator import generate_review_pdf
from app.models import Review


async def run_e2e_tests():
    print("=" * 60)
    print("STARTING AP AGENT END-TO-END PIPELINE VERIFICATION")
    print("=" * 60)

    samples_dir = os.path.join(ROOT_DIR, "samples")

    for i in [1, 2, 3]:
        inv_path = os.path.join(samples_dir, f"sample_{i}_invoice.pdf")
        po_path = os.path.join(samples_dir, f"sample_{i}_po.pdf")

        print(f"\n--- Testing Sample #{i} ---")
        with open(inv_path, "rb") as f:
            inv_bytes = f.read()
        with open(po_path, "rb") as f:
            po_bytes = f.read()

        # Step 1: Document Parsing
        print("1. Parsing PDFs...")
        parsed_inv = parse_pdf_bytes(inv_bytes, f"sample_{i}_invoice.pdf")
        parsed_po = parse_pdf_bytes(po_bytes, f"sample_{i}_po.pdf")
        assert len(parsed_inv.full_text) > 50, f"Failed to extract text from sample_{i}_invoice.pdf"
        assert len(parsed_po.full_text) > 50, f"Failed to extract text from sample_{i}_po.pdf"
        print(f"   Parsed {len(parsed_inv.pages)} invoice page(s) and {len(parsed_po.pages)} PO page(s).")

        # Step 2: Sarvam AI Extraction
        print("2. Extracting structured data via Sarvam AI...")
        inv_data = await extract_document_data(parsed_inv.full_text, doc_type_hint="INVOICE")
        po_data = await extract_document_data(parsed_po.full_text, doc_type_hint="PURCHASE_ORDER")

        print(f"   Invoice Vendor: {inv_data.vendor_name} | Inv#: {inv_data.document_number} | Total: ₹{inv_data.grand_total:,.2f}")
        print(f"   PO Vendor:      {po_data.vendor_name} | PO#:  {po_data.document_number} | Total: ₹{po_data.grand_total:,.2f}")
        print(f"   Items count:    Invoice: {len(inv_data.line_items)}, PO: {len(po_data.line_items)}")

        # Step 3: Deterministic Matching
        print("3. Running Deterministic Matching Engine...")
        discrepancies = match_documents(
            invoice_data=inv_data,
            po_data=po_data,
            invoice_doc=parsed_inv,
            po_doc=parsed_po
        )
        print(f"   Detected {len(discrepancies)} discrepancy(ies).")
        for d in discrepancies:
            print(f"     - [{d.severity.upper()}] {d.title}: {d.description}")

        # Step 4: Rule Decision & Rationale
        print("4. Computing Rule Decision & Rationale...")
        decision, score = compute_rule_decision(discrepancies)
        rationale = await generate_rationale(decision, score, discrepancies, inv_data, po_data)
        print(f"   RECOMMENDATION: {decision} (Score: {score:.0f}/100)")
        print(f"   AI RATIONALE:   {rationale}")

        # Step 5: PDF Report Generation
        print("5. Generating PDF Audit Report...")
        mock_review = Review(
            id=f"test-review-{i}",
            status=decision,
            system_decision=decision,
            rule_score=score,
            rationale=rationale,
            vendor_name=inv_data.vendor_name,
            invoice_number=inv_data.document_number,
            po_number=po_data.document_number,
            invoice_total=inv_data.grand_total,
            po_total=po_data.grand_total,
            currency=inv_data.currency or "INR",
            invoice_filename=f"sample_{i}_invoice.pdf",
            po_filename=f"sample_{i}_po.pdf",
            invoice_data=inv_data.model_dump(),
            po_data=po_data.model_dump(),
            discrepancies=[d.model_dump() for d in discrepancies]
        )
        pdf_bytes = generate_review_pdf(mock_review)
        assert len(pdf_bytes) > 1000, "Generated PDF is empty or invalid"
        print(f"   PDF Report successfully generated ({len(pdf_bytes)} bytes).")

        # Specific Assertions per Sample
        if i == 1:
            assert decision == "APPROVE", f"Expected Sample 1 to APPROVE, got {decision}"
            assert len(discrepancies) == 0, f"Expected 0 discrepancies for Sample 1, got {len(discrepancies)}"
            print("   >>> Sample 1 Verification: SUCCESS (APPROVE clean match)")
        elif i == 2:
            assert decision in ["REJECT", "REVIEW"], f"Expected Sample 2 to REJECT or REVIEW, got {decision}"
            assert len(discrepancies) > 0, "Expected discrepancies for Sample 2"
            print(f"   >>> Sample 2 Verification: SUCCESS ({decision} on price/qty/tax mismatch)")
        elif i == 3:
            assert decision in ["REVIEW", "REJECT"], f"Expected Sample 3 to REVIEW, got {decision}"
            assert len(discrepancies) > 0, "Expected extra item discrepancy for Sample 3"
            print(f"   >>> Sample 3 Verification: SUCCESS ({decision} on unapproved extra item)")

    print("\n" + "=" * 60)
    print("ALL 3 SAMPLES SUCCESSFULLY VALIDATED END-TO-END!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
