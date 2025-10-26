#!/usr/bin/env python3
# metrics_rag.py — local RAG metrics (latency + simple accuracy) for one index.

import sys, json, re, csv, subprocess, argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
from joblib import load

# ---- Bench loader ----
def load_bench(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    # expected: [{"q": "...", "gold_regex": "...", "k": 8}, ...]
    for i, it in enumerate(data):
        if "q" not in it or "gold_regex" not in it:
            raise ValueError(f"bench item {i} missing 'q' or 'gold_regex'")
        it.setdefault("k", 8)
    return data

# ---- Utilities ----
def load_texts_from_index(idx_path: Path) -> Dict[str, str]:
    idx = load(idx_path)  # saved in rag_model.build()
    ids = idx.get("ids") or []
    texts = idx.get("texts") or []
    return {i: t for i, t in zip(ids, texts)}

def run_ask(idx_path: Path, query: str, k: int) -> Tuple[Any, Dict[str,str] | None]:
    py = sys.executable  # use current venv interpreter
    cmd = [
        py, str(Path("rag_model.py")), "ask",
        "--idx", str(idx_path), "--q", query, "--k", str(k), "--mode", "extractive",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return None, {"error": p.stderr.strip()}
    try:
        return json.loads(p.stdout), None
    except Exception as e:
        return None, {"error": f"bad_json: {e}", "stdout": p.stdout[:2000]}

def hit_at_k(hits: List[Dict[str,Any]], gold_regex: str, texts_by_id: Dict[str,str]) -> int:
    pat = re.compile(gold_regex, re.I | re.S)
    for h in hits:
        seg = texts_by_id.get(h.get("id",""), "")
        if seg and pat.search(seg):
            return 1
    return 0

def p_at_1(hits: List[Dict[str,Any]], gold_regex: str, texts_by_id: Dict[str,str]) -> int:
    if not hits:
        return 0
    pat = re.compile(gold_regex, re.I | re.S)
    seg = texts_by_id.get(hits[0].get("id",""), "")
    return 1 if seg and pat.search(seg) else 0

def exact_match(answer_text: str, gold_regex: str) -> int:
    if not isinstance(answer_text, str):
        return 0
    return 1 if re.search(gold_regex, answer_text, re.I | re.S) else 0

# ---- Main ----
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idx", default=str(Path(".cache") / "idx.joblib"))
    ap.add_argument("--out_csv", default=str(Path(".cache") / "metrics.csv"))
    ap.add_argument("--bench", required=True, help="Path to bench JSON")
    args = ap.parse_args()

    idx_path = Path(args.idx)
    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    texts_by_id = load_texts_from_index(idx_path)

    rows = []
    BENCH = load_bench(Path(args.bench))
    for b in BENCH:
        out, err = run_ask(idx_path, b["q"], b["k"])
        if err:
            rows.append({"q": b["q"], "status": "ERR",
                         "latency_ms": "", "hit_at_k": "", "p1": "", "em": "",
                         "err": err.get("error","")})
            continue

        ans = out.get("result", {}).get("answer", "")
        hits = out.get("hits", [])
        tms = out.get("timings_ms", {})
        total_ms = tms.get("total", "")

        hak = hit_at_k(hits, b["gold_regex"], texts_by_id)
        p1  = p_at_1(hits, b["gold_regex"], texts_by_id)
        em  = exact_match(ans, b["gold_regex"])

        rows.append({"q": b["q"], "status": "OK",
                    "latency_ms": total_ms, "hit_at_k": hak, "p1": p1, "em": em, "err": ""})

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["q","status","latency_ms","hit_at_k","p1","em","err"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    oks = [r for r in rows if r["status"] == "OK"]
    if oks:
        lat = []
        for r in oks:
            v = r["latency_ms"]
            try:
                lat.append(float(v))
            except Exception:
                pass
        avg_lat = round(sum(lat)/len(lat), 2) if lat else None
        print(json.dumps({
            "queries": len(rows),
            "ok": len(oks),
            "avg_latency_ms": avg_lat,
            "Hit@k": round(sum(r["hit_at_k"] for r in oks) / len(oks), 3),
            "P@1":   round(sum(r["p1"] for r in oks) / len(oks), 3),
            "ExactMatch": round(sum(r["em"] for r in oks) / len(oks), 3)
        }, indent=2))
    else:
        print(json.dumps({"queries": len(rows), "ok": 0}, indent=2))

if __name__ == "__main__":
    main()
