import pymupdf as fitz
import io
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class ParsedPage:
    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text


class ParsedDocument:
    def __init__(self, filename: str, pages: List[ParsedPage]):
        self.filename = filename
        self.pages = pages

    @property
    def full_text(self) -> str:
        return "\n\n--- Page Break ---\n\n".join(
            f"[Page {p.page_number}]\n{p.text}" for p in self.pages
        )

    def find_evidence_snippet(self, target_term: str, context_chars: int = 120) -> Tuple[int, str]:
        """
        Search for a term or number across pages and return the (page_number, text_snippet).
        Falls back to page 1 snippet if not directly found.
        """
        if not target_term:
            first_text = self.pages[0].text if self.pages else ""
            return 1, first_text[:context_chars].strip()

        term_clean = str(target_term).strip().lower()

        for page in self.pages:
            page_lower = page.text.lower()
            idx = page_lower.find(term_clean)
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(page.text), idx + len(term_clean) + 80)
                snippet = page.text[start:end].replace("\n", " ").strip()
                return page.page_number, f"...{snippet}..."

        # If exact string isn't found, try first token
        first_token = term_clean.split()[0] if term_clean.split() else ""
        if len(first_token) > 2:
            for page in self.pages:
                idx = page.text.lower().find(first_token)
                if idx != -1:
                    start = max(0, idx - 30)
                    end = min(len(page.text), idx + len(first_token) + 60)
                    snippet = page.text[start:end].replace("\n", " ").strip()
                    return page.page_number, f"...{snippet}..."

        # Default fallback
        first_text = self.pages[0].text if self.pages else ""
        snippet = first_text[:context_chars].replace("\n", " ").strip()
        return 1, snippet if snippet else "Document text available in review details."


def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "document.pdf") -> ParsedDocument:
    """
    Extracts text from PDF bytes using PyMuPDF.
    If pages have little or no text (< 30 characters), attempts OCR via pytesseract and pdf2image.
    Gracefully degrades if OCR dependencies/binaries are missing.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: List[ParsedPage] = []

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        text = page.get_text("text").strip()

        # If text is too sparse (likely scanned or image-based PDF), try OCR fallback
        if len(text) < 30:
            logger.info(f"Page {page_num} has minimal text ({len(text)} chars). Attempting OCR fallback...")
            ocr_text = _try_ocr_fallback(doc, page_idx)
            if ocr_text and len(ocr_text) > len(text):
                text = ocr_text

        pages.append(ParsedPage(page_number=page_num, text=text))

    return ParsedDocument(filename=filename, pages=pages)


def _try_ocr_fallback(doc: fitz.Document, page_idx: int) -> str:
    """
    Attempts to OCR a page by rendering it as a pixmap and passing to pytesseract.
    Catches Missing Binary or ImportError cleanly without crashing.
    """
    try:
        import pytesseract
        from PIL import Image

        page = doc[page_idx]
        pix = page.get_pix(dpi=200)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        extracted_ocr = pytesseract.image_to_string(image)
        logger.info(f"OCR successfully extracted {len(extracted_ocr)} chars from page {page_idx + 1}")
        return extracted_ocr.strip()
    except ImportError:
        logger.warning("pytesseract or PIL not installed. Skipping OCR fallback.")
        return ""
    except Exception as e:
        logger.warning(f"OCR fallback failed (Tesseract binary likely not installed in system PATH): {e}")
        return ""
