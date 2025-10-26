#!/usr/bin/env python3
import sys, argparse
from pathlib import Path
from rag_model import build_index, ask

def ensure_index(parsed_path: str, idx_path: str, engine: str):
    idx = Path(idx_path)
    if not idx.exists():
        meta = build_index(parsed_path, idx_path, engine=engine)
        print(f"[build] index ready → {idx_path} | segments={meta.get('count')} | engine={engine}")
    return idx_path

def main():
    p = argparse.ArgumentParser(description="Contract Q&A over parsed JSON")
    p.add_argument("--parsed", required=True, help="Path to parsed JSON (your document-as-segments)")
    p.add_argument("--idx", default=".cache/idx.joblib", help="Index cache path")
    p.add_argument("--engine", choices=["tfidf","sbert"], default="tfidf")
    p.add_argument("--mode", choices=["extractive","generative"], default="extractive")
    p.add_argument("--k", type=int, default=8)
    p.add_argument("--lambda_mmr", type=float, default=0.75)
    p.add_argument("--q", help="One-shot question (if omitted, enters REPL)")
    args = p.parse_args()

    idx_path = ensure_index(args.parsed, args.idx, args.engine)

    def ask_once(question: str):
        out = ask(idx_path, question, k=args.k, lambda_mmr=args.lambda_mmr, mode=args.mode)
        ans = out["result"]
        print("\n=== Answer ===")
        print(ans.get("answer", "NOT_FOUND"))
        print("Citations:", ans.get("citations", []))
        # (Optional) show which chunks were used
        # print("Hits:", out["hits"])
        # print("Timings (ms):", out["timings_ms"])

    if args.q:
        ask_once(args.q)
        return

    # Interactive loop
    print("RAG Q&A REPL. Type your question, or 'exit' to quit.")
    while True:
        try:
            q = input("\nQ> ").strip()
            if not q: continue
            if q.lower() in {"exit","quit","q"}: break
            ask_once(q)
        except (EOFError, KeyboardInterrupt):
            break

if __name__ == "__main__":
    main()
