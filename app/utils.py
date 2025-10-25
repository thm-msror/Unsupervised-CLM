# app/utils.py
from typing import Optional

def parse_document(file_bytes: bytes, file_name: str) -> str:
    """
    FE-only stub: return placeholder text so the UI can be built without python-docx / PyPDF2.
    Swap this to a real parser later.
    """
    name = (file_name or "").lower()
    if name.endswith(".pdf"):
        return "DEMO TEXT (PDF): parser disabled during FE sprint."
    if name.endswith(".docx"):
        return "DEMO TEXT (DOCX): parser disabled during FE sprint."
    # plain text fallback
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return "DEMO TEXT: unsupported file; parser disabled."
