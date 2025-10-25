# app/utils.py  (add if missing)
from io import BytesIO
import docx
from PyPDF2 import PdfReader

def parse_document(file_bytes: bytes, file_name: str) -> str:
    name = (file_name or "").lower()
    if name.endswith(".pdf"):
        reader = PdfReader(BytesIO(file_bytes))
        return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
    if name.endswith(".docx"):
        d = docx.Document(BytesIO(file_bytes))
        return "\n".join(p.text for p in d.paragraphs).strip()
    return file_bytes.decode("utf-8", errors="ignore")
