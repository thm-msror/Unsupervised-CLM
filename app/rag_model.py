#!/usr/bin/env python3
"""
RAG over parsed contract segments.
- Input: JSON list as you posted (one item may contain "full_text"; others contain {"id","text",...})
- Indexing: TF-IDF (default). Optional SBERT if installed.
- Retrieval: cosine + MMR diversification.
- Answers:
  A) Extractive baseline (no LLM): returns top spans + citations.
  B) Generative grounded (Gemini) if GEMINI_API_KEY is set.

CLI:
  Index:    python rag_model.py build --parsed data/parsed/sample.json --out .cache/idx.joblib
  Query:    python rag_model.py ask --idx .cache/idx.joblib --q "Governing law?" --k 8 --mode extractive
  Gemini:   python rag_model.py ask --idx .cache/idx.joblib --q "Termination rights?" --k 8 --mode generative
"""
import os, sys, math, re, json, time, argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import orjson
from joblib import dump, load
from sklearn.feature_extraction.text import TfidfVectorizer

LEGAL_PATTERNS = {
    "governing_law": re.compile(
        r"(?:governing\s+law[^.]*\.|construed\s+and\s+enforced\s+in\s+accordance\s+with\s+the\s+laws\s+of\s+[^.]+\."
        r"|laws?\s+and\s+regulations\s+of\s+[^.]+\.)",
        re.I
    ),
    "termination": re.compile(
        r"(?:^|\n)\s*Termination[\s\S]{0,1000}|(?:terminate[^.]{0,800}\.)",
        re.I
    ),
    "payment": re.compile(
        r"(?:pass[-\s]?through cost|monthly Management Services charge|settle all charges.*?on a net basis|"
        r"invoice[^.]{0,300}\.|milestone[^.]{0,300}\.|net\s*(?:10|15|30|45|60)\s*days[^.]*\.)",
        re.I
    ),
    "parties": re.compile(
        r"(?:between\s+.*?\s+and\s+.*?\)|by and among\s+.*?\))",
        re.I
    ),
    "confidential": re.compile(
        r"(?:confidential|proprietary)[\s\S]{0,800}",
        re.I
    ),
    "governing_venue": re.compile(
        r"laws?\s+of\s+the\s+State\s+of\s+[A-Za-z ]+[^.]*?(?:venue|jurisdiction)[^.]*?\.",
        re.I
    ),
    # capture typical liability caps in enterprise contracts
    "liability_cap": re.compile(
        r"(?:IN\s+NO\s+EVENT|in no event)[\s\S]{0,200}?(?:aggregate\s+liability|liability\b)[\s\S]{0,400}?"
        r"(?:exceed|greater of)[\s\S]{0,200}?(?:fees|amounts)\s+(?:paid|received)[\s\S]{0,200}?"
        r"(?:\b\d{1,2}\s*\(?\d{1,2}?\)?\s*months|\btwelve\s*\(?12\)?\s*months|\byear)\b[\s\S]{0,200}\.",
        re.I
    ),
}


# top of file
_SBERT_CACHE = {}
def _get_sbert(name):
    from sentence_transformers import SentenceTransformer
    if name not in _SBERT_CACHE:
        _SBERT_CACHE[name] = SentenceTransformer(name)
    return _SBERT_CACHE[name]



# ---------- Utilities ----------
def _require(cond: bool, msg: str):
    if not cond: raise RuntimeError(msg)

def read_json(path: str):
    return orjson.loads(Path(path).read_bytes())

def write_json(path: str, obj: Any):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(orjson.dumps(obj, option=orjson.OPT_INDENT_2))

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

# ---------- Data loading ----------
def load_parsed(src: str|List[Dict[str,Any]]) -> Tuple[str, List[Dict[str,Any]]]:
    items = src
    if isinstance(src, str):
        data = read_json(src)
        items = data if isinstance(data, list) else data.get("items", [])
    full_text = ""
    segments = []
    for it in items:
        if isinstance(it, dict) and "full_text" in it:
            full_text = it["full_text"]
        elif isinstance(it, dict) and "id" in it and "text" in it:
            seg = {"id": str(it["id"]),
                   "text": normalize_space(it["text"]),
                   "title": it.get("title",""),
                   "level": it.get("level")}
            segments.append(seg)
    _require(segments, "No segments found")
    return full_text, segments

# ---------- Index builders ----------
class TfidfIndex:
    def __init__(self, segments: List[Dict[str,Any]]):
        # in TfidfIndex.__init__
        from sklearn.feature_extraction.text import TfidfVectorizer
        # vectorizer config
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1,3),
            max_df=0.95,
            min_df=1,
            max_features=120_000,
            sublinear_tf=True,
            norm="l2",
            token_pattern=r"(?u)\b[\w\-]{2,}\b"  # keep hyphenated legal terms
        )

        
        self.texts = [s["text"] for s in segments]
        self.ids = [s["id"] for s in segments]
        self.X = self.vectorizer.fit_transform(self.texts)

    def search(self, query: str, k: int) -> List[Tuple[str, float, str]]:
        from sklearn.metrics.pairwise import cosine_similarity
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.X).ravel()
        idx = sims.argsort()[::-1][:k]
        return [(self.ids[i], float(sims[i]), self.texts[i]) for i in idx]

def try_sbert(segments: List[Dict[str,Any]]):
    # Optional SBERT path; only used if sentence-transformers installed.
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        model = SentenceTransformer(model_name)
        texts = [s["text"] for s in segments]
        ids = [s["id"] for s in segments]
        X = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return {"type":"sbert", "model_name": model_name, "ids":ids, "texts":texts, "X":X}
    except Exception:
        return None
    
# simple query rewrite for legal intents
def _rewrite_query(q: str) -> str:
    ql = q.lower()
    boosts = []
    if "govern" in ql or "law" in ql or "jurisd" in ql:
        boosts += ['"governing law"', "construed", "enforced", "laws of", "state of"]
    if "terminat" in ql or "expire" in ql:
        boosts += ["termination", "notice", '"prior written notice"', "insolvent", "mutual written agreement"]
    if any(x in ql for x in ("payment","fee","fees","charges","settle","compensation","consideration","remuneration")):
        boosts += ["payment", "pass-through", "monthly", "charge", "settle", "net basis", "invoice", "due date", "late fee"]
    if "parties" in ql or "roles" in ql:
        boosts += ["by and among", "between", "affiliate", "service provider", "service recipient"]
    return q + " " + " ".join(boosts)

def cosine(a, b):
    import numpy as np
    num = float((a*b).sum())
    da = float(np.sqrt((a*a).sum()))
    db = float(np.sqrt((b*b).sum()))
    if da==0 or db==0: return 0.0
    return num/(da*db)

def sbert_search(index, query: str, k: int):
    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer(index["model_name"])
    qv = model.encode([query], normalize_embeddings=True)[0]
    sims = (index["X"] @ qv)
    order = np.argsort(sims)[::-1][:k]
    return [(index["ids"][i], float(sims[i]), index["texts"][i]) for i in order]

# ---------- MMR diversification ----------
def mmr(cands: List[Tuple[str,float,str]], k: int, lambda_mult: float=0.75) -> List[Tuple[str,float,str]]:
    # cands: [(id, score, text)]
    import numpy as np
    if len(cands) <= k: return cands
    # Recompute vector reps via simple TF vectors for diversity estimation
    # Minimal overhead using token counts.
    def vec(text):
        toks = text.lower().split()
        d = {}
        for w in toks: d[w] = d.get(w,0)+1
        return d
    vocab = {}
    vecs = []
    for _,_,t in cands:
        vv = vec(t); vecs.append(vv)
        for w in vv.keys(): vocab[w]=True
    vocab = {w:i for i,w in enumerate(vocab.keys())}
    def to_dense(vd):
        v=[0]*len(vocab)
        for w,c in vd.items():
            if w in vocab: v[vocab[w]]=c
        return np.asarray(v, dtype=float)
    dense = [to_dense(v) for v in vecs]
    def cos(a,b):
        num=float((a*b).sum()); da=float(np.sqrt((a*a).sum())); db=float(np.sqrt((b*b).sum()))
        return 0.0 if da==0 or db==0 else num/(da*db)

    selected = []
    remaining = list(range(len(cands)))
    # normalize relevance to [0,1]
    rel = [c[1] for c in cands]
    m = max(rel) or 1.0
    rel = [r/m for r in rel]
    while remaining and len(selected)<k:
        if not selected:
            i = max(remaining, key=lambda j: rel[j])
            selected.append(i); remaining.remove(i); continue
        def mmr_score(j):
            max_sim = max(cos(dense[j], dense[i]) for i in selected) if selected else 0.0
            return lambda_mult*rel[j] - (1-lambda_mult)*max_sim
        i = max(remaining, key=mmr_score)
        selected.append(i); remaining.remove(i)
    return [cands[i] for i in selected]

# ---------- Answering ----------
EXTRACTIVE_JSON_SPEC = (
    'Return ONLY JSON of the form {"answer": str, "citations": [ids...]}. '
    'Base answer strictly on quoted spans. If insufficient evidence: {"answer":"NOT_FOUND","citations":[]}.'
)

def extractive_answer(query, hits, max_chars=700):
    if not hits:
        return {"answer": "NOT_FOUND", "citations": []}

    q = query.lower()
    joined = " ".join(h[2] for h in hits)  # <-- define once and reuse


    # helper: prefer the first hit whose text contains the match; else fall back to top-5 citations
    def pack_with_best_citation(txt: str):
        mtxt = txt.strip()
        cid = None
        for hid, _, htxt in hits:
            if mtxt and mtxt in htxt:
                cid = hid
                break
        cites = [cid] if cid else [h[0] for h in hits[:5]]
        return {"answer": f"\"{mtxt[:max_chars]}\"", "citations": cites}

    # Governing law
    if "govern" in q or "law" in q or "jurisd" in q:
        law_sent = None
        law_pat = re.compile(r"[^\.]*laws?\s+of\s+[^\.]+\.", re.I)
        for hid, _, htxt in hits:
            m = law_pat.search(htxt)
            if m:
                law_sent = m.group(0).strip()
                if len(law_sent) > 30:
                    return {"answer": f"\"{law_sent}\"", "citations": [hid]}
        m = LEGAL_PATTERNS["governing_law"].search(joined)
        if m:
            return pack_with_best_citation(m.group(0))

    # Termination
    if "terminat" in q or "expire" in q:
        m = LEGAL_PATTERNS["termination"].search(joined)
        if m:
            return pack_with_best_citation(m.group(0).splitlines()[0])

    # Payment
    if any(x in q for x in ("payment", "fee", "charges", "settle", "compensation")):
        m = LEGAL_PATTERNS["payment"].search(joined)
        if m:
            return pack_with_best_citation(m.group(0))

    # Parties
    if "parties" in q or "roles" in q or "between" in q or "by and among" in q:
        m = LEGAL_PATTERNS["parties"].search(joined)
        if m:
            return pack_with_best_citation(m.group(0))

    # Confidentiality
    if "confidential" in q:
        m = LEGAL_PATTERNS["confidential"].search(joined)
        if m:
            return pack_with_best_citation(m.group(0))

    # Venue (don’t recompute joined)
    if "venue" in q or "governing" in q or "law" in q:
        m = LEGAL_PATTERNS["governing_venue"].search(joined)
        if m:
            return pack_with_best_citation(m.group(0))

    # Liability cap (don’t recompute joined)
    if "liability" in q or "cap" in q or "limit" in q:
        m = LEGAL_PATTERNS["liability_cap"].search(joined)
        if m:
            return pack_with_best_citation(m.group(0))

    # Fallback: lexical best-match sentence
    sents = re.split(r'(?<=[\.\?\!])\s+', joined)
    q_terms = [t for t in re.findall(r"[A-Za-z0-9]+", q) if len(t) > 2]
    best, score = "", 0
    for s in sents:
        t = s.lower()
        sc = sum(1 for qt in q_terms if qt in t)
        if sc > score and 0 < len(s) <= max_chars:
            best, score = s.strip(), sc
    if best:
        return pack_with_best_citation(best)

    return pack_with_best_citation(hits[0][2].splitlines()[0])


def generative_answer(query: str, hits: List[Tuple[str,float,str]]) -> Dict[str,Any]:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return {"answer":"NOT_FOUND", "citations":[]}
    import google.generativeai as genai, json as pyjson
    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    packed = "\n\n".join([f"[{i}] {normalize_space(t)}" for i,_,t in hits])
    system = (
        "Answer strictly from the provided contract snippets. "
        "Quote exact spans in double quotes. "
        "Return JSON: {\"answer\": str, \"citations\": [segment_id,...]}. "
        "If insufficient evidence, return {\"answer\":\"NOT_FOUND\",\"citations\":[]}. "
        "No extra text."
    )
    user = f"Context:\n{packed}\n\nQuestion: {query}\n{EXTRACTIVE_JSON_SPEC}"
    resp = model.generate_content(
        [{"role":"system","parts":[system]},
         {"role":"user","parts":[user]}],
        generation_config={"temperature":0.0,"max_output_tokens":512},
        request_options={"timeout": 12.0},
    )
    txt = resp.text or ""
    s = txt.find("{"); e = txt.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return {"answer":"NOT_FOUND","citations":[]}
    return json.loads(txt[s:e+1])

# ---------- Public API ----------
def build_index(parsed_path: str, out_path: str, engine: str="tfidf"):
    _, segments = load_parsed(parsed_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    meta = {"engine": engine, "built_at": int(time.time()), "count": len(segments)}
    if engine == "tfidf":
        idx = TfidfIndex(segments)
        dump({"type":"tfidf","ids":idx.ids,"texts":idx.texts,"X":idx.X,"vectorizer":idx.vectorizer,"meta":meta}, out_path)
    elif engine == "sbert":
        sidx = try_sbert(segments)
        _require(sidx is not None, "sentence-transformers not available")
        dump({"type":"sbert", **sidx, "meta":meta}, out_path)
    else:
        raise RuntimeError("engine must be tfidf or sbert")
    return meta

def _search(idx_obj, query: str, k: int) -> List[Tuple[str,float,str]]:
    q = _rewrite_query(query)
    if idx_obj["type"] == "tfidf":
        from sklearn.metrics.pairwise import cosine_similarity
        qv = idx_obj["vectorizer"].transform([q])
        sims = cosine_similarity(qv, idx_obj["X"]).ravel()
        order = sims.argsort()[::-1]
        topn = 50  # stable candidate pool for MMR
        order = order[:topn]
        return [(idx_obj["ids"][i], float(sims[i]), idx_obj["texts"][i]) for i in order]
    elif idx_obj["type"] == "sbert":
        from sentence_transformers import SentenceTransformer
        import numpy as np
        model = _get_sbert(idx_obj["model_name"])
        qv = model.encode([q], normalize_embeddings=True)[0]
        sims = (idx_obj["X"] @ qv)
        order = np.argsort(sims)[::-1][:max(k, 50)]
        return [(idx_obj["ids"][i], float(sims[i]), idx_obj["texts"][i]) for i in order]
    raise RuntimeError("unknown index type")


def ask(idx_path: str, query: str, k: int=8, lambda_mmr: float=0.75, mode: str="extractive") -> Dict[str,Any]:
    t0 = time.perf_counter()
    idx = load(idx_path)

    t1 = time.perf_counter()
    raw_hits = _search(idx, query, k=k)
    t2 = time.perf_counter()
    hits = mmr(raw_hits, k=k, lambda_mult=lambda_mmr)
    t3 = time.perf_counter()

    if mode == "extractive":
        ans = extractive_answer(query, hits)
    else:
        ans = generative_answer(query, hits)
    t4 = time.perf_counter()

    timings_ms = {
        "load_idx": round((t1 - t0) * 1000, 2),
        "retrieval": round((t2 - t1) * 1000, 2),
        "mmr": round((t3 - t2) * 1000, 2),
        "answer": round((t4 - t3) * 1000, 2),
        "total": round((t4 - t0) * 1000, 2),
    }
    contexts = [{"id": h[0], "text": h[2]} for h in hits[:k]]

    return {
        "query": query,
        "hits": [{"id": h[0], "score": h[1]} for h in hits],
        "contexts": contexts,
        "result": ans,
        "timings_ms": timings_ms,
        "meta": idx.get("meta", {})
    }

# ---------- CLI ----------
def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--parsed", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--engine", choices=["tfidf","sbert"], default="tfidf")

    a = sub.add_parser("ask")
    a.add_argument("--idx", required=True)
    a.add_argument("--q", required=True)
    a.add_argument("--k", type=int, default=8)
    a.add_argument("--lambda_mmr", type=float, default=0.75)
    a.add_argument("--mode", choices=["extractive","generative"], default="extractive")

    args = p.parse_args()
    if args.cmd == "build":
        meta = build_index(args.parsed, args.out, engine=args.engine)
        print(orjson.dumps({"status":"ok","meta":meta}, option=orjson.OPT_INDENT_2).decode())
    else:
        out = ask(args.idx, args.q, k=args.k, lambda_mmr=args.lambda_mmr, mode=args.mode)
        
        print(orjson.dumps(out, option=orjson.OPT_INDENT_2).decode())

if __name__ == "__main__":
    main()
