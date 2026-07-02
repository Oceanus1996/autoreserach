#!/usr/bin/env python3
"""Merge agent label outputs back onto the paper records + enforce finite vocab.

Reads label_work/*.out.jsonl (per-paper labels keyed by doi), optionally remaps
synonyms via synonyms.json ({axis: {variant: canonical}}), validates every label
against taxonomy.json, and writes <venue>.labeled.jsonl with the 5 axis fields.

Run with --report first to see proposed new terms / out-of-vocab labels before
committing them to taxonomy.json.

Usage:
    python apply_labels.py --report
    python apply_labels.py --source IEEE_SandP_2024.jsonl
"""
import argparse
import glob
import json
import os
from collections import Counter

AXES = ["domain", "article_type", "method", "scope", "problem"]
MULTI = {"method", "scope", "problem"}


def load_taxonomy():
    tax = json.load(open("taxonomy.json", encoding="utf-8"))
    return {a: set(tax["axes"][a]["values"]) for a in AXES}


def load_synonyms():
    if os.path.exists("synonyms.json"):
        return json.load(open("synonyms.json", encoding="utf-8"))
    return {a: {} for a in AXES}


def load_labels():
    by_doi = {}
    for path in glob.glob(os.path.join("label_work", "*.out.jsonl")):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if r.get("doi"):
                by_doi[r["doi"].lower()] = r
    return by_doi


def canon(axis, val, syn):
    return syn.get(axis, {}).get(val, val)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="show new/out-of-vocab terms, don't write")
    ap.add_argument("--source", help="one source jsonl; default = all *_2*.jsonl")
    args = ap.parse_args()

    vocab = load_taxonomy()
    syn = load_synonyms()
    labels = load_labels()
    print(f"loaded {len(labels)} labeled papers")

    if args.report:
        seen = {a: Counter() for a in AXES}
        oov = {a: Counter() for a in AXES}
        for r in labels.values():
            for a in AXES:
                vals = r.get(a, [])
                vals = vals if isinstance(vals, list) else [vals]
                for v in vals:
                    if not v:
                        continue
                    c = canon(a, v, syn)
                    seen[a][c] += 1
                    if c not in vocab[a]:
                        oov[a][c] += 1
        for a in AXES:
            print(f"\n== {a} == ({len(seen[a])} distinct)")
            for v, n in seen[a].most_common():
                flag = "  <-- NOT in taxonomy" if v in oov[a] else ""
                print(f"   {n:4}  {v}{flag}")
        return

    sources = [args.source] if args.source else sorted(
        p for p in glob.glob("*.jsonl")
        if p not in ("all_index.jsonl",) and not p.endswith(".labeled.jsonl"))
    for src in sources:
        out = src.replace(".jsonl", ".labeled.jsonl")
        n = matched = 0
        with open(out, "w", encoding="utf-8") as f:
            for line in open(src, encoding="utf-8"):
                rec = json.loads(line)
                n += 1
                lab = labels.get(rec["doi"].lower())
                if lab:
                    matched += 1
                    for a in AXES:
                        vals = lab.get(a, [] if a in MULTI else "")
                        if isinstance(vals, list):
                            rec[a] = [canon(a, v, syn) for v in vals]
                        else:
                            rec[a] = canon(a, vals, syn)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{src}: {matched}/{n} labeled -> {out}")


if __name__ == "__main__":
    main()
