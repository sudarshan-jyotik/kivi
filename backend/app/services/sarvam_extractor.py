import json
import logging
import re
import httpx
from typing import Dict, Any, Optional
from ..config import settings
from ..schemas import DocumentData

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a senior Accounts Payable Auditor and document parsing engine.
Your task is to extract structured JSON data from the given document text (which is either an INVOICE or a PURCHASE ORDER).

You MUST return ONLY a valid, raw JSON object conforming strictly to this schema:
{
  "document_type": "INVOICE" or "PURCHASE_ORDER",
  "vendor_name": "Full legal name of the vendor/supplier",
  "document_number": "Invoice Number (e.g. INV-1001) or PO Number (e.g. PO-5001)",
  "date": "Date of the document (YYYY-MM-DD or as printed)",
  "gstin": "GSTIN (e.g. 29ABCDE1234F1Z5) or null if not found",
  "currency": "INR",
  "subtotal": 10000.00,
  "tax_details": {
    "CGST": 900.00,
    "SGST": 900.00,
    "IGST": 0.00
  },
  "total_tax": 1800.00,
  "grand_total": 11800.00,
  "line_items": [
    {
      "description": "Item description",
      "quantity": 10.0,
      "unit_price": 1000.0,
      "tax_rate": 18.0,
      "line_total": 10000.0,
      "hsn_sac": "8471"
    }
  ]
}

CRITICAL RULES:
1. Return ONLY the raw JSON object. No explanation, no markdown backticks, no markdown formatting.
2. All numeric fields (subtotal, total_tax, grand_total, quantity, unit_price, tax_rate, line_total) MUST be numbers (floats or ints), NOT strings. Remove commas and currency symbols like ₹, $, Rs.
3. Extract all line items accurately.
"""


def _clean_json_response(content: str) -> str:
    """Extract and clean raw JSON from LLM response."""
    content = content.strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
        content = content.strip()
    
    # Extract outermost JSON object {...}
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group(0)

    return content.strip()


async def extract_document_data(
    document_text: str,
    doc_type_hint: str = "INVOICE"
) -> DocumentData:
    """
    Uses Sarvam AI chat completions API to extract structured DocumentData from text.
    Validates with Pydantic and retries once on invalid JSON.
    """
    if not settings.SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not configured in environment or .env file.")

    url = f"{settings.SARVAM_BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "api-subscription-key": settings.SARVAM_API_KEY
    }

    user_prompt = f"""Document Type: {doc_type_hint}

Document Content:
\"\"\"
{document_text}
\"\"\"

Extract all information and return strict raw JSON conforming to the schema."""

    payload = {
        "model": settings.SARVAM_MODEL,
        "messages": [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4096
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            res_data = response.json()
            raw_content = res_data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"Sarvam AI HTTP Error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 429:
                raise RuntimeError("Sarvam AI rate limit exceeded. Please wait a moment and retry.")
            raise RuntimeError(f"Sarvam AI API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Failed to communicate with Sarvam AI: {e}")
            raise RuntimeError(f"Sarvam AI connection failed: {str(e)}")

        # Attempt 1: Parse & Validate
        cleaned = _clean_json_response(raw_content)
        try:
            data = DocumentData.model_validate_json(cleaned)
            return data
        except Exception as parse_err:
            logger.warning(f"Initial JSON validation failed: {parse_err}. Content snippet: {cleaned[:150]}. Retrying once with fix prompt...")

            # Retry once with explicit fix prompt
            fix_payload = {
                "model": settings.SARVAM_MODEL,
                "messages": [
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": raw_content},
                    {
                        "role": "user",
                        "content": f"The output was not valid JSON: {str(parse_err)}. Please output ONLY the raw, complete valid JSON object now."
                    }
                ],
                "temperature": 0.0,
                "max_tokens": 4096
            }

            try:
                retry_response = await client.post(url, headers=headers, json=fix_payload)
                retry_response.raise_for_status()
                retry_data = retry_response.json()
                retry_content = _clean_json_response(retry_data["choices"][0]["message"]["content"])
                return DocumentData.model_validate_json(retry_content)
            except Exception as final_err:
                logger.error(f"Retry JSON validation failed: {final_err}")
                raise ValueError(f"Failed to parse document with Sarvam AI: {final_err}")
