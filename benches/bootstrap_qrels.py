# benches/bootstrap_qrels.py
import json, re, sys
from pathlib import Path
from joblib import load
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

idx = load(Path(sys.argv[1]))
src = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
ids, texts = idx["ids"], idx["texts"]
id2text = dict(zip(ids, texts))

vec = TfidfVectorizer(lowercase=True, ngram_range=(1,2), token_pattern=r"(?u)\b[\w\-]{2,}\b")
X = vec.fit_transform(texts)

def tfidf_top(query, limit=10):
    qv = vec.transform([query])
    sims = cosine_similarity(qv, X).ravel()
    order = sims.argsort()[::-1][:limit]
    return [ids[i] for i in order]

out = []
for it in src:
    q = it["q"]; k = it.get("k", 8)
    gold_ids = []
    gold_answers = []
    if "gold_regex" in it:
        pat = re.compile(it["gold_regex"], re.I|re.S)
        gold_ids = [i for i,t in id2text.items() if t and pat.search(t)]
        if not gold_ids:
            # fallback: use the question as query
            gold_ids = tfidf_top(q, limit=10)
        # weak gold answers: take a plausible sentence or a snippet
        for i in gold_ids[:3]:
            t = id2text.get(i) or ""
            m = re.search(r"[^.؟!]*[.؟!]", t)
            gold_answers.append((m.group(0) if m else t[:200]).strip())
    else:
        gold_ids = it.get("gold_ids", []) or tfidf_top(q, limit=10)
        gold_answers = it.get("gold_answers", [])[:3]
    out.append({"q": q, "k": k, "gold_ids": gold_ids[:10], "gold_answers": gold_answers[:3]})

Path(sys.argv[3]).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"wrote {sys.argv[3]}  (items={len(out)})")
