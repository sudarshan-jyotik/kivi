import uuid
from typing import List, Dict, Any, Optional, Tuple
from rapidfuzz import fuzz
from ..schemas import DocumentData, Discrepancy, DiscrepancyEvidence, LineItem
from ..config import settings
from .document_parser import ParsedDocument


def _is_within_tolerance(val1: float, val2: float, abs_tol: float, pct_tol: float) -> bool:
    """Checks if two numbers match within absolute or percentage tolerance."""
    diff = abs(val1 - val2)
    max_val = max(abs(val1), abs(val2))
    allowed = max(abs_tol, max_val * pct_tol)
    return diff <= allowed


def match_documents(
    invoice_data: DocumentData,
    po_data: DocumentData,
    invoice_doc: Optional[ParsedDocument] = None,
    po_doc: Optional[ParsedDocument] = None,
    is_duplicate_invoice: bool = False,
    abs_tolerance: Optional[float] = None,
    pct_tolerance: Optional[float] = None
) -> List[Discrepancy]:
    """
    Deterministic matching engine comparing an Invoice against a Purchase Order.
    Returns a list of Discrepancy objects with severity, expected vs actual values,
    and verbatim text snippets with page numbers.
    """
    abs_tol = abs_tolerance if abs_tolerance is not None else settings.TOLERANCE_ABSOLUTE
    pct_tol = pct_tolerance if pct_tolerance is not None else settings.TOLERANCE_PERCENT

    discrepancies: List[Discrepancy] = []

    # 1. Duplicate Invoice Check
    if is_duplicate_invoice:
        page_num, snippet = (1, f"Invoice Number: {invoice_data.document_number}")
        if invoice_doc:
            page_num, snippet = invoice_doc.find_evidence_snippet(invoice_data.document_number)

        discrepancies.append(Discrepancy(
            id=str(uuid.uuid4()),
            type="DUPLICATE_INVOICE",
            severity="high",
            title="Duplicate Invoice Detected",
            description=f"Invoice number '{invoice_data.document_number}' already exists in the system for vendor '{invoice_data.vendor_name}'. Potential duplicate billing.",
            expected_value="Unique invoice number",
            actual_value=invoice_data.document_number,
            evidence=DiscrepancyEvidence(
                source_document="INVOICE",
                page_number=page_num,
                text_snippet=snippet
            )
        ))

    # 2. Vendor Name Check
    vendor_ratio = fuzz.token_sort_ratio(invoice_data.vendor_name.lower(), po_data.vendor_name.lower())
    if vendor_ratio < 80:
        page_num, snippet = (1, invoice_data.vendor_name)
        if invoice_doc:
            page_num, snippet = invoice_doc.find_evidence_snippet(invoice_data.vendor_name)

        discrepancies.append(Discrepancy(
            id=str(uuid.uuid4()),
            type="VENDOR_MISMATCH",
            severity="high",
            title="Vendor Name Mismatch",
            description=f"Invoice vendor '{invoice_data.vendor_name}' does not match Purchase Order vendor '{po_data.vendor_name}' (similarity: {vendor_ratio:.0f}%).",
            expected_value=po_data.vendor_name,
            actual_value=invoice_data.vendor_name,
            evidence=DiscrepancyEvidence(
                source_document="INVOICE",
                page_number=page_num,
                text_snippet=snippet
            )
        ))

    # 3. GSTIN Check (if present on both)
    if invoice_data.gstin and po_data.gstin:
        clean_inv_gstin = invoice_data.gstin.strip().upper().replace(" ", "")
        clean_po_gstin = po_data.gstin.strip().upper().replace(" ", "")
        if clean_inv_gstin != clean_po_gstin:
            page_num, snippet = (1, invoice_data.gstin)
            if invoice_doc:
                page_num, snippet = invoice_doc.find_evidence_snippet(invoice_data.gstin)

            discrepancies.append(Discrepancy(
                id=str(uuid.uuid4()),
                type="GSTIN_MISMATCH",
                severity="high",
                title="GSTIN Mismatch",
                description=f"Invoice GSTIN '{invoice_data.gstin}' does not match PO GSTIN '{po_data.gstin}'.",
                expected_value=po_data.gstin,
                actual_value=invoice_data.gstin,
                evidence=DiscrepancyEvidence(
                    source_document="INVOICE",
                    page_number=page_num,
                    text_snippet=snippet
                )
            ))

    # 4. Currency Check
    if invoice_data.currency.upper() != po_data.currency.upper():
        discrepancies.append(Discrepancy(
            id=str(uuid.uuid4()),
            type="CURRENCY_MISMATCH",
            severity="high",
            title="Currency Mismatch",
            description=f"Invoice currency ({invoice_data.currency}) differs from PO currency ({po_data.currency}).",
            expected_value=po_data.currency,
            actual_value=invoice_data.currency,
            evidence=None
        ))

    # 5. Line Item Matching (Fuzzy description + quantity/price proximity)
    po_items_unmatched = list(range(len(po_data.line_items)))
    invoice_items_matched = []

    for inv_idx, inv_item in enumerate(invoice_data.line_items):
        best_match_idx = None
        best_score = -1.0

        for po_idx in po_items_unmatched:
            po_item = po_data.line_items[po_idx]
            # Description similarity (0 - 100)
            desc_score = fuzz.token_sort_ratio(inv_item.description.lower(), po_item.description.lower())

            # Price closeness bonus (up to 20 pts)
            price_score = 0.0
            if po_item.unit_price > 0:
                price_ratio = min(inv_item.unit_price, po_item.unit_price) / max(inv_item.unit_price, po_item.unit_price)
                price_score = price_ratio * 20.0

            # Qty closeness bonus (up to 10 pts)
            qty_score = 0.0
            if po_item.quantity > 0:
                qty_ratio = min(inv_item.quantity, po_item.quantity) / max(inv_item.quantity, po_item.quantity)
                qty_score = qty_ratio * 10.0

            total_composite = (desc_score * 0.7) + price_score + qty_score

            if total_composite > best_score and desc_score >= 60:
                best_score = total_composite
                best_match_idx = po_idx

        if best_match_idx is not None:
            po_items_unmatched.remove(best_match_idx)
            po_item = po_data.line_items[best_match_idx]
            invoice_items_matched.append((inv_item, po_item))

            # Find snippet for inv_item
            inv_page, inv_snippet = (1, inv_item.description)
            if invoice_doc:
                inv_page, inv_snippet = invoice_doc.find_evidence_snippet(inv_item.description)

            # Check Quantity Mismatch
            if not _is_within_tolerance(inv_item.quantity, po_item.quantity, 0.01, 0.001):
                severity = "high" if inv_item.quantity > po_item.quantity else "medium"
                discrepancies.append(Discrepancy(
                    id=str(uuid.uuid4()),
                    type="LINE_ITEM_QTY_MISMATCH",
                    severity=severity,
                    title=f"Quantity Mismatch: {inv_item.description}",
                    description=f"Billed quantity ({inv_item.quantity}) differs from PO quantity ({po_item.quantity}).",
                    expected_value=po_item.quantity,
                    actual_value=inv_item.quantity,
                    evidence=DiscrepancyEvidence(
                        source_document="INVOICE",
                        page_number=inv_page,
                        text_snippet=inv_snippet
                    )
                ))

            # Check Unit Price Mismatch
            if not _is_within_tolerance(inv_item.unit_price, po_item.unit_price, abs_tol, pct_tol):
                severity = "high" if inv_item.unit_price > po_item.unit_price else "low"
                discrepancies.append(Discrepancy(
                    id=str(uuid.uuid4()),
                    type="LINE_ITEM_PRICE_MISMATCH",
                    severity=severity,
                    title=f"Unit Price Mismatch: {inv_item.description}",
                    description=f"Billed unit price (₹{inv_item.unit_price:,.2f}) does not match agreed PO price (₹{po_item.unit_price:,.2f}).",
                    expected_value=f"₹{po_item.unit_price:,.2f}",
                    actual_value=f"₹{inv_item.unit_price:,.2f}",
                    evidence=DiscrepancyEvidence(
                        source_document="INVOICE",
                        page_number=inv_page,
                        text_snippet=inv_snippet
                    )
                ))

            # Check Tax Rate Mismatch
            if abs(inv_item.tax_rate - po_item.tax_rate) > 0.1:
                discrepancies.append(Discrepancy(
                    id=str(uuid.uuid4()),
                    type="LINE_ITEM_TAX_MISMATCH",
                    severity="medium",
                    title=f"Tax Rate Mismatch: {inv_item.description}",
                    description=f"Billed GST rate ({inv_item.tax_rate}%) differs from PO rate ({po_item.tax_rate}%).",
                    expected_value=f"{po_item.tax_rate}%",
                    actual_value=f"{inv_item.tax_rate}%",
                    evidence=DiscrepancyEvidence(
                        source_document="INVOICE",
                        page_number=inv_page,
                        text_snippet=inv_snippet
                    )
                ))
        else:
            # Extra item on invoice not present in PO
            inv_page, inv_snippet = (1, inv_item.description)
            if invoice_doc:
                inv_page, inv_snippet = invoice_doc.find_evidence_snippet(inv_item.description)

            discrepancies.append(Discrepancy(
                id=str(uuid.uuid4()),
                type="LINE_ITEM_EXTRA_ON_INVOICE",
                severity="high",
                title=f"Unapproved Item: {inv_item.description}",
                description=f"Line item '{inv_item.description}' (Total: ₹{inv_item.line_total:,.2f}) is present on invoice but was NOT ordered in Purchase Order.",
                expected_value="Item not in PO",
                actual_value=f"{inv_item.description} (Qty: {inv_item.quantity}, Price: ₹{inv_item.unit_price:,.2f})",
                evidence=DiscrepancyEvidence(
                    source_document="INVOICE",
                    page_number=inv_page,
                    text_snippet=inv_snippet
                )
            ))

    # Any remaining unmatched items in PO?
    for po_idx in po_items_unmatched:
        po_item = po_data.line_items[po_idx]
        po_page, po_snippet = (1, po_item.description)
        if po_doc:
            po_page, po_snippet = po_doc.find_evidence_snippet(po_item.description)

        discrepancies.append(Discrepancy(
            id=str(uuid.uuid4()),
            type="LINE_ITEM_MISSING_FROM_INVOICE",
            severity="medium",
            title=f"PO Item Missing from Invoice: {po_item.description}",
            description=f"Item '{po_item.description}' was ordered in PO (Qty: {po_item.quantity}, Price: ₹{po_item.unit_price:,.2f}) but is absent from the invoice.",
            expected_value=f"{po_item.description} (Qty: {po_item.quantity})",
            actual_value="Missing from invoice",
            evidence=DiscrepancyEvidence(
                source_document="PURCHASE_ORDER",
                page_number=po_page,
                text_snippet=po_snippet
            )
        ))

    # 6. Total Amount Checks
    # Subtotal check
    if not _is_within_tolerance(invoice_data.subtotal, po_data.subtotal, abs_tol, pct_tol):
        inv_page, inv_snippet = (1, f"Subtotal: {invoice_data.subtotal}")
        if invoice_doc:
            inv_page, inv_snippet = invoice_doc.find_evidence_snippet(str(int(invoice_data.subtotal)))

        discrepancies.append(Discrepancy(
            id=str(uuid.uuid4()),
            type="SUBTOTAL_MISMATCH",
            severity="medium",
            title="Subtotal Mismatch",
            description=f"Invoice subtotal (₹{invoice_data.subtotal:,.2f}) does not match PO subtotal (₹{po_data.subtotal:,.2f}).",
            expected_value=f"₹{po_data.subtotal:,.2f}",
            actual_value=f"₹{invoice_data.subtotal:,.2f}",
            evidence=DiscrepancyEvidence(
                source_document="INVOICE",
                page_number=inv_page,
                text_snippet=inv_snippet
            )
        ))

    # Grand Total check
    if not _is_within_tolerance(invoice_data.grand_total, po_data.grand_total, abs_tol, pct_tol):
        inv_page, inv_snippet = (1, f"Total: {invoice_data.grand_total}")
        if invoice_doc:
            inv_page, inv_snippet = invoice_doc.find_evidence_snippet(str(int(invoice_data.grand_total)))

        discrepancies.append(Discrepancy(
            id=str(uuid.uuid4()),
            type="TOTAL_MISMATCH",
            severity="high",
            title="Grand Total Mismatch",
            description=f"Invoice grand total (₹{invoice_data.grand_total:,.2f}) differs from agreed PO total (₹{po_data.grand_total:,.2f}) by ₹{abs(invoice_data.grand_total - po_data.grand_total):,.2f}.",
            expected_value=f"₹{po_data.grand_total:,.2f}",
            actual_value=f"₹{invoice_data.grand_total:,.2f}",
            evidence=DiscrepancyEvidence(
                source_document="INVOICE",
                page_number=inv_page,
                text_snippet=inv_snippet
            )
        ))

    return discrepancies

