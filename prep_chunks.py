#!/usr/bin/env python3
"""Split a venue jsonl into agent-sized chunk files for classification.

Each chunk is a compact numbered list (doi + title + truncated abstract) so an
LLM sub-agent can label many papers in one context.

Usage:
    python prep_chunks.py IEEE_SandP_2024.jsonl --size 40 --words 90
"""
import argparse
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("infile")
    ap.add_argument("--size", type=int, default=40)
    ap.add_argument("--words", type=int, default=90)
    ap.add_argument("--outdir", default="label_work")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    rows = [json.loads(l) for l in open(args.infile, encoding="utf-8")]
    base = os.path.splitext(os.path.basename(args.infile))[0]
    n = 0
    for start in range(0, len(rows), args.size):
        chunk = rows[start:start + args.size]
        path = os.path.join(args.outdir, f"{base}__chunk{n:02d}.txt")
        with open(path, "w", encoding="utf-8") as f:
            for i, r in enumerate(chunk):
                gi = start + i
                ab = " ".join((r.get("abstract") or "").split()[:args.words])
                f.write(f"[{gi}] doi={r['doi']}\n")
                f.write(f"TITLE: {r['title']}\n")
                f.write(f"ABSTRACT: {ab or '(none)'}\n\n")
        print(f"{path}: {len(chunk)} papers")
        n += 1
    print(f"{len(rows)} papers -> {n} chunks in {args.outdir}/")


if __name__ == "__main__":
    main()
