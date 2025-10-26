#!/usr/bin/env python3
from .rag_model import build_index, ask
import sys, argparse, os, re
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from src.rag.rag_model import build_index, ask


# ---------- UTILITIES ----------
def _strip_quotes(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = s.strip()
    return s[1:-1].strip() if len(s) >= 2 and s[0] in "'\"" and s[-1] == s[0] else s


# ---------- HUMANIZER ----------
def makehuman(question: str, evidence_answer: str, contexts: list[dict]) -> str:
    """
    Use Gemini API to humanize the extracted evidence into concise English.
    Uses top-k context for better summaries. Falls back to evidence if API fails.
    """
    ev = _strip_quotes(evidence_answer or "")
    q = (question or "").strip()
    if not ev:
        return "I couldn’t find this in the document."

    # Pack multiple context snippets
    packed = "\n\n".join(
        f"[{c.get('id')}] {c.get('text','')[:800]}"
        for c in (contexts or [])[:5]
    )

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ev

    genai.configure(api_key=api_key)

    prompt = f"""
You are a professional legal summarizer. Using the provided contract context,
rewrite the evidence into a clear, short English answer.

Question:
{q}

Extracted Evidence:
\"\"\"{ev}\"\"\"

Context (from contract):
{packed}

Guidelines:
- Output only in fluent English (no Arabic or other languages).
- Be concise (1–2 sentences).
- Use formal, legally appropriate phrasing.
- Do not invent facts; stay grounded in the context.
- If context is unclear or irrelevant, say exactly:
  "I couldn’t find this in the document."
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        resp = model.generate_content(
            prompt,
            generation_config={"temperature": 0.2, "max_output_tokens": 150},
            request_options={"timeout": 12.0},
        )
        txt = (resp.text or "").strip()
        return txt if txt else ev
    except Exception:
        return ev


# ---------- INDEX BUILDER ----------
def ensure_index(parsed_path: str, idx_path: str, engine: str):
    idx = Path(idx_path)
    if not idx.exists():
        meta = build_index(parsed_path, idx_path, engine=engine)
        print(f"[build] index ready → {idx_path} | segments={meta.get('count')} | engine={engine}")
    return idx_path


# ---------- MAIN ----------
def main():
    p = argparse.ArgumentParser(description="Contract Q&A over parsed JSON")
    p.add_argument("--parsed", required=True, help="Path to parsed JSON (your document-as-segments)")
    p.add_argument("--idx", default=".cache/idx.joblib", help="Index cache path")
    p.add_argument("--engine", choices=["tfidf", "sbert"], default="tfidf")
    p.add_argument("--mode", choices=["extractive", "generative"], default="extractive")
    p.add_argument("--k", type=int, default=8)
    p.add_argument("--lambda_mmr", type=float, default=0.75)
    p.add_argument("--q", help="One-shot question (if omitted, enters REPL)")
    args = p.parse_args()

    idx_path = ensure_index(args.parsed, args.idx, args.engine)

    def ask_once(question: str):
        out = ask(idx_path, question, k=args.k, lambda_mmr=args.lambda_mmr, mode=args.mode)
        ans = out["result"]
        raw_answer = ans.get("answer", "NOT_FOUND")
        contexts = out.get("contexts", [])  # new addition from modified rag_model.py

        # Humanize dynamically using top-k context
        human = makehuman(question, raw_answer, contexts) if args.mode == "extractive" else raw_answer

        print("\n=== Answer ===")
        print(human)

        print("\n--- Evidence (quoted) ---")
        print(raw_answer)

        print("Citations:", ans.get("citations", []))
        # Uncomment for timing info
        # print("Timings (ms):", out.get("timings_ms", {}))

    if args.q:
        ask_once(args.q)
        return

    print("RAG Q&A REPL. Type your question, or 'exit' to quit.")
    while True:
        try:
            q = input("\nQ> ").strip()
            if not q:
                continue
            if q.lower() in {"exit", "quit", "q"}:
                break
            ask_once(q)
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    main()
