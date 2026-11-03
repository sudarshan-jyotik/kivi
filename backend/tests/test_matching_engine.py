import pytest
from app.schemas import DocumentData, LineItem, Discrepancy
from app.services.matching_engine import match_documents, _is_within_tolerance
from app.services.decision_engine import compute_rule_decision


@pytest.fixture
def clean_po_data():
    return DocumentData(
        document_type="PURCHASE_ORDER",
        vendor_name="Acme Technologies India Pvt Ltd",
        document_number="PO-2024-001",
        date="2024-10-15",
        gstin="29AABCA1234F1Z5",
        currency="INR",
        subtotal=512500.0,
        tax_details={"CGST": 46125.0, "SGST": 46125.0},
        total_tax=92250.0,
        grand_total=604750.0,
        line_items=[
            LineItem(description="Dell Latitude 5440 Laptop", quantity=5.0, unit_price=75000.0, tax_rate=18.0, line_total=375000.0),
            LineItem(description="Dell 27-inch 4K Monitor", quantity=5.0, unit_price=25000.0, tax_rate=18.0, line_total=125000.0),
            LineItem(description="Logitech Wireless Keyboard & Mouse Combo", quantity=5.0, unit_price=2500.0, tax_rate=18.0, line_total=12500.0),
        ]
    )


@pytest.fixture
def clean_invoice_data():
    return DocumentData(
        document_type="INVOICE",
        vendor_name="Acme Technologies India Pvt Ltd",
        document_number="INV-2024-101",
        date="2024-10-18",
        gstin="29AABCA1234F1Z5",
        currency="INR",
        subtotal=512500.0,
        tax_details={"CGST": 46125.0, "SGST": 46125.0},
        total_tax=92250.0,
        grand_total=604750.0,
        line_items=[
            LineItem(description="Dell Latitude 5440 Laptop", quantity=5.0, unit_price=75000.0, tax_rate=18.0, line_total=375000.0),
            LineItem(description="Dell 27-inch 4K Monitor", quantity=5.0, unit_price=25000.0, tax_rate=18.0, line_total=125000.0),
            LineItem(description="Logitech Wireless Keyboard & Mouse Combo", quantity=5.0, unit_price=2500.0, tax_rate=18.0, line_total=12500.0),
        ]
    )


def test_clean_match_returns_zero_discrepancies_and_approves(clean_invoice_data, clean_po_data):
    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data
    )
    assert len(discrepancies) == 0

    decision, score = compute_rule_decision(discrepancies)
    assert decision == "APPROVE"
    assert score == 100.0


def test_price_mismatch_detection(clean_invoice_data, clean_po_data):
    # Alter unit price of first item on invoice
    clean_invoice_data.line_items[0].unit_price = 82000.0  # was 75000.0
    clean_invoice_data.line_items[0].line_total = 410000.0
    clean_invoice_data.subtotal = 547500.0
    clean_invoice_data.grand_total = 646050.0

    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data
    )

    price_disc = [d for d in discrepancies if d.type == "LINE_ITEM_PRICE_MISMATCH"]
    assert len(price_disc) == 1
    assert price_disc[0].severity == "high"
    assert "₹75,000.00" in price_disc[0].expected_value
    assert "₹82,000.00" in price_disc[0].actual_value

    decision, score = compute_rule_decision(discrepancies)
    assert decision in ["REJECT", "REVIEW"]
    assert score < 100.0


def test_quantity_mismatch_detection(clean_invoice_data, clean_po_data):
    # Billed 8 units instead of 5
    clean_invoice_data.line_items[1].quantity = 8.0
    clean_invoice_data.line_items[1].line_total = 200000.0
    clean_invoice_data.subtotal = 587500.0
    clean_invoice_data.grand_total = 693250.0

    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data
    )

    qty_disc = [d for d in discrepancies if d.type == "LINE_ITEM_QTY_MISMATCH"]
    assert len(qty_disc) == 1
    assert qty_disc[0].severity == "high"
    assert qty_disc[0].expected_value == 5.0
    assert qty_disc[0].actual_value == 8.0


def test_tax_rate_mismatch_detection(clean_invoice_data, clean_po_data):
    # Tax rate charged 28% instead of 18%
    clean_invoice_data.line_items[0].tax_rate = 28.0

    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data
    )

    tax_disc = [d for d in discrepancies if d.type == "LINE_ITEM_TAX_MISMATCH"]
    assert len(tax_disc) == 1
    assert tax_disc[0].severity == "medium"
    assert tax_disc[0].expected_value == "18.0%"
    assert tax_disc[0].actual_value == "28.0%"


def test_extra_line_item_on_invoice(clean_invoice_data, clean_po_data):
    # Add an unapproved extra line item to invoice
    clean_invoice_data.line_items.append(
        LineItem(description="Express Rush Surcharge", quantity=1.0, unit_price=15000.0, tax_rate=18.0, line_total=15000.0)
    )
    clean_invoice_data.subtotal += 15000.0
    clean_invoice_data.grand_total += 17700.0

    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data
    )

    extra_disc = [d for d in discrepancies if d.type == "LINE_ITEM_EXTRA_ON_INVOICE"]
    assert len(extra_disc) == 1
    assert extra_disc[0].severity == "high"
    assert "Express Rush Surcharge" in extra_disc[0].title


def test_missing_po_item(clean_invoice_data, clean_po_data):
    # Remove one item from the invoice
    clean_invoice_data.line_items.pop()
    clean_invoice_data.subtotal -= 12500.0
    clean_invoice_data.grand_total -= 14750.0

    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data
    )

    missing_disc = [d for d in discrepancies if d.type == "LINE_ITEM_MISSING_FROM_INVOICE"]
    assert len(missing_disc) == 1
    assert missing_disc[0].severity == "medium"
    assert "Logitech" in missing_disc[0].title


def test_duplicate_invoice_detection(clean_invoice_data, clean_po_data):
    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data,
        is_duplicate_invoice=True
    )

    dup_disc = [d for d in discrepancies if d.type == "DUPLICATE_INVOICE"]
    assert len(dup_disc) == 1
    assert dup_disc[0].severity == "high"

    decision, score = compute_rule_decision(discrepancies)
    assert decision == "REJECT"


def test_vendor_name_mismatch(clean_invoice_data, clean_po_data):
    clean_invoice_data.vendor_name = "Totally Different Supplies Corp"

    discrepancies = match_documents(
        invoice_data=clean_invoice_data,
        po_data=clean_po_data
    )

    vendor_disc = [d for d in discrepancies if d.type == "VENDOR_MISMATCH"]
    assert len(vendor_disc) == 1
    assert vendor_disc[0].severity == "high"

    decision, score = compute_rule_decision(discrepancies)
    assert decision == "REJECT"


def test_tolerance_logic():
    # Tolerance helper: abs_tol = 1.0 (₹1.00), pct_tol = 0.005 (0.5%)
    # Exact match
    assert _is_within_tolerance(100.0, 100.0, 1.0, 0.005) is True

    # ₹0.50 difference on ₹100 is within ₹1.00 absolute tolerance
    assert _is_within_tolerance(100.50, 100.0, 1.0, 0.005) is True

    # ₹5.00 difference on ₹100 exceeds ₹1.00 and 0.5% (₹0.50)
    assert _is_within_tolerance(105.0, 100.0, 1.0, 0.005) is False

    # On large amount ₹100,000, 0.5% is ₹500
    # ₹300 difference is within 0.5% tolerance
    assert _is_within_tolerance(100300.0, 100000.0, 1.0, 0.005) is True

    # ₹800 difference exceeds 0.5% tolerance
    assert _is_within_tolerance(100800.0, 100000.0, 1.0, 0.005) is False


def test_pdf_report_generation(clean_invoice_data, clean_po_data):
    from app.models import Review
    from app.services.report_generator import generate_review_pdf

    mock_review = Review(
        id="test-review-1234",
        status="APPROVED",
        system_decision="APPROVE",
        rule_score=100.0,
        rationale="All line items and totals match agreed PO terms perfectly.",
        vendor_name="Acme Technologies India Pvt Ltd",
        invoice_number="INV-2024-101",
        po_number="PO-2024-001",
        invoice_total=604750.0,
        po_total=604750.0,
        currency="INR",
        invoice_filename="sample_1_invoice.pdf",
        po_filename="sample_1_po.pdf",
        invoice_data=clean_invoice_data.model_dump(),
        po_data=clean_po_data.model_dump(),
        discrepancies=[]
    )
    pdf_bytes = generate_review_pdf(mock_review)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

