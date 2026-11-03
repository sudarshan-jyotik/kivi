import logging
import httpx
from typing import List, Tuple
from ..schemas import Discrepancy, DocumentData
from ..config import settings

logger = logging.getLogger(__name__)

RATIONALE_SYSTEM_PROMPT = """You are an Accounts Payable Audit Assistant.
A rule-based deterministic matching engine has already audited an invoice against its purchase order, identified discrepancies, and made an official decision (APPROVE, REVIEW, or REJECT).

Your ONLY task is to write a concise, professional 2-3 sentence rationale explaining the findings to human accounts payable managers.
Reference specific vendor names, document numbers, amounts, and critical discrepancy details.
Do NOT change or override the decision. Explain WHY this decision was rendered based on the provided findings."""


def compute_rule_decision(discrepancies: List[Discrepancy]) -> Tuple[str, float]:
    """
    Deterministic rule-based decision engine.
    Returns (decision, score) where decision in ["APPROVE", "REVIEW", "REJECT"]
    and score in [0.0, 100.0].
    """
    if not discrepancies:
        return "APPROVE", 100.0

    high_flags = [d for d in discrepancies if d.severity == "high"]
    med_flags = [d for d in discrepancies if d.severity == "medium"]
    low_flags = [d for d in discrepancies if d.severity == "low"]

    # Calculate score deduction
    penalty = (len(high_flags) * 35.0) + (len(med_flags) * 15.0) + (len(low_flags) * 5.0)
    score = max(0.0, 100.0 - penalty)

    # Severe automatic rejection triggers
    critical_reject_types = {
        "DUPLICATE_INVOICE",
        "VENDOR_MISMATCH",
        "GSTIN_MISMATCH",
    }
    has_critical_reject = any(d.type in critical_reject_types for d in high_flags)

    # If there are high severity price/item/total discrepancies and score is low
    if has_critical_reject or score < 40.0:
        return "REJECT", round(score, 1)

    if high_flags or med_flags or score < 85.0:
        return "REVIEW", round(score, 1)

    return "APPROVE", round(score, 1)


async def generate_rationale(
    decision: str,
    score: float,
    discrepancies: List[Discrepancy],
    invoice_data: DocumentData,
    po_data: DocumentData
) -> str:
    """
    Calls Sarvam AI to write a short plain-English explanation for the decision.
    If Sarvam AI fails or is not configured, provides a deterministic summary fallback.
    """
    # Deterministic fallback text
    if not discrepancies:
        fallback_text = (
            f"Automated 2-way match succeeded with a perfect score of {score}/100. "
            f"All line items, quantities, unit prices, and GST totals from {invoice_data.vendor_name} "
            f"for Invoice {invoice_data.document_number} match Purchase Order {po_data.document_number} within tolerance. "
            "Recommended for automatic approval."
        )
    else:
        discrepancy_summaries = "; ".join(f"{d.title} ({d.description})" for d in discrepancies[:3])
        fallback_text = (
            f"Decision rendered as {decision} (Score: {score}/100) due to {len(discrepancies)} detected discrepancy(ies). "
            f"Key findings: {discrepancy_summaries}. "
            "Manual review required before payment disbursement."
        )

    if not settings.SARVAM_API_KEY:
        return fallback_text

    discrepancy_text = "\n".join([
        f"- [{d.severity.upper()}] {d.title}: {d.description} (Expected: {d.expected_value}, Actual: {d.actual_value})"
        for d in discrepancies
    ]) if discrepancies else "None. All items and totals match."

    user_prompt = f"""Official Decision: {decision}
Rule Score: {score}/100
Vendor: {invoice_data.vendor_name}
Invoice: {invoice_data.document_number} (Total: ₹{invoice_data.grand_total:,.2f})
PO: {po_data.document_number} (Total: ₹{po_data.grand_total:,.2f})

Detected Discrepancies:
{discrepancy_text}

Write a professional 2-3 sentence AP audit rationale explaining why this was marked as {decision}."""

    url = f"{settings.SARVAM_BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": settings.SARVAM_API_KEY
    }
    payload = {
        "model": settings.SARVAM_MODEL,
        "messages": [
            {"role": "system", "content": RATIONALE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1024
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            res_data = response.json()
            llm_text = res_data["choices"][0]["message"]["content"].strip()
            return llm_text
    except Exception as e:
        logger.warning(f"Failed to generate Sarvam AI rationale ({e}). Using deterministic fallback.")
        return fallback_text
