import re
import os
import json
import fitz  # PyMuPDF
import docx
from langdetect import detect
from bidi.algorithm import get_display
import arabic_reshaper
import time
from datetime import datetime


def read_docu(file_path: str):
    """
    Reads .docx or .pdf and returns (text, lang)
    where 'text' is normalized Unicode string and 'lang' is e.g. 'en' or 'ar'.
    """
    start_time = time.time()
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    # ----------- DOCX -----------
    if ext == ".docx":
        try:
            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {e}")

    # ----------- PDF ------------
    elif ext == ".pdf":
        try:
            with fitz.open(file_path) as pdf:
                pages = []
                for page in pdf:
                    # Extract text from each page
                    pages.append(page.get_text("text"))
                text = "\n".join(pages)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {e}")

    else:
        raise ValueError("Unsupported file type. Only .pdf or .docx allowed.")

    # ----------- Normalize --------
    text = text.strip()
    if not text:
        raise ValueError("No readable text extracted.")

    # ----------- Detect Language --------
    try:
        lang = detect(text[:4000])  # langdetect only needs a few k chars
    except Exception:
        lang = "unknown"

    # ----------- Arabic Post-process (for display) --------
    # NOTE: Only reshape for display/UI, not for NLP offsets.
    if lang == "ar":
        text_display = get_display(arabic_reshaper.reshape(text))
        text_display = fix_arabic(text_display)
    else:
        text_display = text
    return_obj = {
        "file_name": os.path.splitext(os.path.basename(file_path))[0],
        "language": lang,
        "length": len(text_display),
        "parsed_timestamp" : datetime.now().isoformat(),
        "parsed_duration" : time.time() - start_time ,
        "parsed_duration_per_thousand_char" : (time.time() - start_time)/len(text_display) *10000 ,
        "full_text": text_display,
    }
    return return_obj

def fix_arabic(s: str) -> str:
    return get_display(arabic_reshaper.reshape(s))

# HDR_NUM = re.compile(r'^\s*(?:Section|Sec\.|Article|Clause)?\s*(\d+(?:\.\d+){0,3})\b[^\n]{0,100}$', re.I)
# HDR_CAPS = re.compile(r'^[A-Z0-9 ,&/\-\(\)\'"]{3,80}$')
# HDR_LABEL = re.compile(r'^[A-Za-z ]{3,50}:\s*$')
# HDR_AR_NUM = re.compile(r'^(?:المادة|البند)\s+\d+', re.UNICODE)

# def find_sections(full_text: str, lang: str):
#     lines = full_text.splitlines(keepends=True)
#     anchors = []  # list of (char_index, level, title)
#     idx = 0
#     for line in lines:
#         s = line.strip()
#         is_hdr = (
#             HDR_NUM.match(s) or HDR_CAPS.match(s) or HDR_LABEL.match(s) or HDR_AR_NUM.match(s)
#         )
#         if is_hdr:
#             # quick level guess: depth = count of dots or keyword weight
#             m = HDR_NUM.match(s)
#             level = len(m.group(1).split(".")) if m else 1
#             anchors.append((idx, level, s))
#         idx += len(line)
    
    
#     sections = []
#     sections.append({
#         "full_text": full_text
#     })
#     # If no anchors, return one giant section
#     if not anchors:
        
#         default_section_size = 500
#         for e, i in enumerate(range(0, len(full_text), default_section_size)):
#             start = max(0, i-100)
#             end = i + default_section_size + 100
#             sections.append({
#                 "id": f"sec_{e}",
#                 "lang": lang, 
#                 "title": full_text[start:start+20],
#                 "level": None,
#                 "start_char": start,
#                 "end_char": end,
#                 "len": end - start,
#                 "text": full_text[start:end].strip()
#             })
#         return sections

#     # Build sections
#     is_start = True 
#     for i, (start, level, title) in enumerate(anchors):
#         if is_start and start!=0:
#             is_start = False
#             sections.append({
#                 "id": f"sec_{0}",
#                 "lang": lang, 
#                 "title": title.strip(),
#                 "level": level,
#                 "start_char": 0,
#                 "end_char": start,
#                 "len": start,
#                 "text": full_text[0:start+1].strip()
#             })
            
#         end = anchors[i+1][0] if i+1 < len(anchors) else len(full_text)
#         sections.append({
#             "id": f"sec_{i+1}",
#             "lang": lang, 
#             "title": title.strip(),
#             "level": level,
#             "start_char": start,
#             "end_char": end,
#             "len": end - start,
#             "text": full_text[start:end].strip()
#         })
#     return sections

def get_doc_paths(folder_path):
    """
    Recursively scans 'folder_path' (and all its subfolders)
    for .doc, .docx, and .pdf files.
    Returns a list of absolute paths.
    """
    doc_pdf_files = []

    for root, _, files in os.walk(folder_path):
        for filename in files:
            if filename.lower().endswith(('.doc', '.docx', '.pdf')):
                full_path = os.path.join(root, filename)
                doc_pdf_files.append(full_path)

    return doc_pdf_files

def test():
    input_root = r"data"
    output_root = r"data/parsed"

    os.makedirs(output_root, exist_ok=True)

    print(get_doc_paths(input_root))

    for docu_path in get_doc_paths(input_root):
        docu = read_docu(docu_path)

        # --- make a safe filename ---
        rel_path = os.path.relpath(docu_path, input_root)
        safe_name = rel_path.replace(os.sep, "_")
        base_name = os.path.splitext(safe_name)[0] + ".json"
        filename = os.path.join(output_root, base_name)

        # --- save the sections JSON ---
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(docu, f, ensure_ascii=False, indent=4)

        print(f"✅ Data saved to {filename}")


test()

