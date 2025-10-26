# app/parse_utils.py  (create if you don’t have one)
import re, json, sys
from pathlib import Path

SENT_SPLIT = re.compile(r'(?<=[\.\?\!])\s+(?=[A-Z\[])')

def to_sentence_segments(parsed_path, out_path):
    items = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
    out = []
    # carry over the full_text item unchanged if present
    for it in items:
        if isinstance(it, dict) and "full_text" in it:
            out.append(it); break
    for it in items:
        if not (isinstance(it, dict) and "id" in it and "text" in it):
            continue
        title = it.get("title","")
        for i, sent in enumerate(SENT_SPLIT.split(it["text"].strip())):
            s = sent.strip()
            if not s: continue
            out.append({"id": f"{it['id']}_s{i:03d}", "lang": it.get("lang","en"),
                        "title": title, "level": it.get("level"), "text": s})
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    to_sentence_segments(sys.argv[1], sys.argv[2])
