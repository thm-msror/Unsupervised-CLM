#!/usr/bin/env python3
# metrics_rag.py — suite-level RAG metrics (retrieval + reader + latency).
import sys, json, re, csv, math, subprocess, argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from joblib import load

def _strip_quotes(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = s.strip()
    return re.sub(r'^(["\'])(.*)\1$', r'\2', s)
# ---------- Bench / Suite loaders ----------
def load_bench(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("bench must be a JSON list")
    for i, it in enumerate(data):
        if "q" not in it:
            raise ValueError(f"bench item {i} missing 'q'")
        it.setdefault("k", 8)
    return data

def load_suite(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "datasets" not in data or not isinstance(data["datasets"], list):
        raise ValueError("suite JSON must have 'datasets': [ ... ]")
    return data

# ---------- Utilities ----------
def load_texts_from_index(idx_path: Path) -> Dict[str, str]:
    idx = load(idx_path)  # saved in rag_model.build()
    ids = idx.get("ids") or []
    texts = idx.get("texts") or []
    return {i: t for i, t in zip(ids, texts)}

def run_ask(idx_path: Path, query: str, k: int) -> Tuple[Any, Dict[str,str] | None]:
    import os
    py = os.getenv("PY") or sys.executable  # prefer env PY, else current python
    rag_path = Path(__file__).parent / "rag_model.py"  # <— robust path to app/rag_model.py

    cmd = [
        str(py), str(rag_path), "ask",
        "--idx", str(idx_path), "--q", query, "--k", str(k), "--mode", "extractive",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return None, {"error": p.stderr.strip()}
    try:
        return json.loads(p.stdout), None
    except Exception as e:
        return None, {"error": f"bad_json: {e}", "stdout": p.stdout[:2000]}


# ---------- Retrieval metrics ----------
def compute_ranking_metrics(
    hits: List[Dict[str,Any]],
    gold_ids: List[str],
    k_eval: Optional[int] = None
) -> Dict[str, float]:
    """
    hits: [{"id": str, "score": float, ...}, ...] (already ranked desc)
    gold_ids: set/list of relevant doc ids
    k_eval: evaluate up to this k (default=len(hits))
    """
    if not hits:  # return zeros
        return {"hit@k":0.0, "recall@k":0.0, "mrr@k":0.0, "ndcg@k":0.0, "map@k":0.0}

    K = min(k_eval or len(hits), len(hits))
    rel_set = set(gold_ids or [])
    rel_flags = [1 if h.get("id","") in rel_set else 0 for h in hits[:K]]

    # Hit@K: any relevant in top-K
    hit_at_k = 1.0 if any(rel_flags) else 0.0

    # Recall@K: #relevant retrieved / #relevant total
    total_rel = max(1, len(rel_set))
    recall_at_k = sum(rel_flags) / total_rel

    # MRR@K: reciprocal rank of first relevant
    mrr = 0.0
    for i, r in enumerate(rel_flags, start=1):
        if r == 1:
            mrr = 1.0 / i
            break

    # DCG / nDCG@K (binary gains)
    def dcg(rs):
        return sum(r / math.log2(i+1) for i, r in enumerate(rs, start=1))
    dcg_k = dcg(rel_flags)
    ideal = sorted(rel_flags, reverse=True)
    idcg_k = dcg(ideal) if any(ideal) else 1.0
    ndcg = dcg_k / idcg_k

    # AP@K / MAP component (binary gains)
    precisions = []
    rel_seen = 0
    for i, r in enumerate(rel_flags, start=1):
        if r == 1:
            rel_seen += 1
            precisions.append(rel_seen / i)
    ap = sum(precisions) / total_rel if total_rel > 0 else 0.0

    return {
        "hit@k": hit_at_k,
        "recall@k": recall_at_k,
        "mrr@k": mrr,
        "ndcg@k": ndcg,
        "map@k": ap
    }

# ---------- Reader metrics ----------
def squad_like_f1(pred: str, refs: List[str]) -> float:
    if not isinstance(pred, str) or not refs:
        return 0.0
    def norm(s: str) -> List[str]:
        s = re.sub(r"[^A-Za-z0-9\u0600-\u06FF]+", " ", s.lower()).strip()
        return s.split()
    pred_toks = norm(pred)
    if not pred_toks: return 0.0
    best = 0.0
    for ref in refs:
        ref_toks = norm(ref or "")
        if not ref_toks: 
            continue
        common = {}
        for t in pred_toks:
            common[t] = min(pred_toks.count(t), ref_toks.count(t))
        overlap = sum(common.values())
        if overlap == 0:
            f1 = 0.0
        else:
            prec = overlap / len(pred_toks)
            rec  = overlap / len(ref_toks)
            f1 = 2 * prec * rec / (prec + rec)
        best = max(best, f1)
    return best

def exact_match_any(pred: str, refs: List[str]) -> int:
    if not isinstance(pred, str) or not refs:
        return 0
    norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
    p = norm(pred)
    for r in refs:
        if norm(r or "") == p:
            return 1
    return 0

# ---------- Back-compat regex checks ----------
def hit_at_k_regex(hits: List[Dict[str,Any]], gold_regex: str, texts_by_id: Dict[str,str]) -> int:
    pat = re.compile(gold_regex, re.I | re.S)
    for h in hits:
        seg = texts_by_id.get(h.get("id",""), "")
        if seg and pat.search(seg):
            return 1
    return 0

def p_at_1_regex(hits: List[Dict[str,Any]], gold_regex: str, texts_by_id: Dict[str,str]) -> int:
    if not hits:
        return 0
    pat = re.compile(gold_regex, re.I | re.S)
    seg = texts_by_id.get(hits[0].get("id",""), "")
    return 1 if seg and pat.search(seg) else 0

def exact_match_regex(answer_text: str, gold_regex: str) -> int:
    if not isinstance(answer_text, str):
        return 0
    return 1 if re.search(gold_regex, answer_text, re.I | re.S) else 0

# ---------- Core eval for one dataset ----------
def eval_dataset(idx_path: Path, bench_items: List[Dict[str,Any]], out_csv: Path) -> Dict[str, Any]:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    texts_by_id = load_texts_from_index(idx_path)

    rows = []
    for b in bench_items:
        q = b["q"]; k = int(b.get("k", 8))
        out, err = run_ask(idx_path, q, k)
        if err:
            rows.append({"q": q, "status": "ERR",
                         "latency_ms": "", "hit@k": "", "recall@k": "", "mrr@k": "", "ndcg@k": "",
                         "map@k": "", "em": "", "f1": "", "err": err.get("error","")})
            continue

        # --- normalize answer text ---
        def _strip_quotes(s: str) -> str:
            if not isinstance(s, str): return s
            s = s.strip()
            return re.sub(r'^(["\'])(.*)\1$', r'\2', s)

        ans = _strip_quotes((out.get("result", {}) or {}).get("answer", ""))
        hits = out.get("hits", []) or []
        tms  = out.get("timings_ms", {}) or {}
        total_ms = tms.get("total", "")

        # Two supervision modes:
        if "gold_ids" in b and isinstance(b["gold_ids"], list):
            # qrels-style supervision
            rank = compute_ranking_metrics(hits, b["gold_ids"], k_eval=k)
            refs = b.get("gold_answers") if isinstance(b.get("gold_answers"), list) else None
            em = exact_match_any(ans, refs) if refs else ""
            f1 = round(squad_like_f1(ans, refs), 3) if refs else ""
            rows.append({
                "q": q, "status": "OK", "latency_ms": total_ms,
                "hit@k": round(rank["hit@k"],3),
                "recall@k": round(rank["recall@k"],3),
                "mrr@k": round(rank["mrr@k"],3),
                "ndcg@k": round(rank["ndcg@k"],3),
                "map@k": round(rank["map@k"],3),
                "em": em, "f1": f1, "err": ""
            })
        else:
            # back-compat regex supervision
            gold_regex = b.get("gold_regex", "")
            hak = hit_at_k_regex(hits, gold_regex, texts_by_id)
            p1  = p_at_1_regex(hits, gold_regex, texts_by_id)
            em  = exact_match_regex(ans, gold_regex)
            rows.append({
                "q": q, "status": "OK", "latency_ms": total_ms,
                "hit@k": hak, "recall@k": "", "mrr@k": "", "ndcg@k": "",
                "map@k": "", "em": em, "f1": "", "p1(regex)": p1, "err": ""
            })

    # write per-dataset CSV
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        fields = ["q","status","latency_ms","hit@k","recall@k","mrr@k","ndcg@k","map@k","em","f1","err"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows: w.writerow({k: r.get(k,"") for k in fields})

    # aggregate
    oks = [r for r in rows if r["status"] == "OK"]
    lat = []
    for r in oks:
        try: lat.append(float(r["latency_ms"]))
        except: pass
    def mean_of(key):
        vals = [r[key] for r in oks if isinstance(r.get(key), (int,float))]
        return round(sum(vals)/len(vals), 3) if vals else None
    def mean_bool(key):
        vals = [float(r[key]) for r in oks if str(r.get(key)) not in ("","None")]
        return round(sum(vals)/len(vals), 3) if vals else None

    agg = {
        "queries": len(rows),
        "ok": len(oks),
        "avg_latency_ms": round(sum(lat)/len(lat),2) if lat else None,
        "Hit@k": mean_bool("hit@k"),
        "Recall@k": mean_of("recall@k"),
        "MRR@k": mean_of("mrr@k"),
        "nDCG@k": mean_of("ndcg@k"),
        "MAP@k": mean_of("map@k"),
        "EM": mean_bool("em"),
        "F1": mean_of("f1"),
    }
    return {"rows": rows, "agg": agg}

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idx", help="Path to one index (when not using --suite)")
    ap.add_argument("--bench", help="Path to one bench JSON (list of items)")
    ap.add_argument("--suite", help="Path to a suite JSON ({datasets:[{name,idx,bench},...]})")
    ap.add_argument("--out_dir", default=str(Path(".cache") / "metrics"))
    args = ap.parse_args()

    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    if args.suite:
        suite = load_suite(Path(args.suite))
        results = []
        for ds in suite["datasets"]:
            name = ds["name"]
            idx_path = Path(ds["idx"])
            bench_items = load_bench(Path(ds["bench"]))
            per_csv = out_dir / f"{name}.csv"
            res = eval_dataset(idx_path, bench_items, per_csv)
            agg = res["agg"]; agg["dataset"] = name
            results.append(agg)

        # suite-level macro-average (unweighted)
        keys = ["avg_latency_ms","Hit@k","Recall@k","MRR@k","nDCG@k","MAP@k","EM","F1"]
        macro = {"datasets": len(results), "queries_total": sum(r["queries"] for r in results)}
        for k in keys:
            vals = [r[k] for r in results if r.get(k) is not None]
            macro[k] = round(sum(vals)/len(vals), 3) if vals else None

        print(json.dumps({"per_dataset": results, "macro_avg": macro}, indent=2))
        (out_dir / "suite_summary.json").write_text(json.dumps({"per_dataset": results, "macro_avg": macro}, indent=2), encoding="utf-8")
    else:
        if not args.idx or not args.bench:
            raise SystemExit("Provide --suite OR (--idx AND --bench)")
        idx_path = Path(args.idx)
        bench_items = load_bench(Path(args.bench))
        per_csv = out_dir / "metrics.csv"
        res = eval_dataset(idx_path, bench_items, per_csv)
        print(json.dumps(res["agg"], indent=2))

if __name__ == "__main__":
    main()
