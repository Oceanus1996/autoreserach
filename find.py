#!/usr/bin/env python3
"""Portable search over the LOCAL research corpus.

Always searches d:\\skill\\research-index\\all_index.jsonl no matter which folder
you run it from (path is resolved from this file's location). Prints venue / year
/ title / DOI so any hit maps straight back to a paper.

Examples (run from ANY directory):
    python D:\\skill\\research-index\\find.py prompt injection
    python D:\\skill\\research-index\\find.py "text-to-image" jailbreak --venue "S&P"
    python D:\\skill\\research-index\\find.py llm agent --year 2024-2026 --title-only
    python D:\\skill\\research-index\\find.py multimodal --any --limit 60
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "all_index.jsonl")


def parse_year(s):
    if not s:
        return None
    if "-" in s:
        a, b = s.split("-", 1)
        return (int(a), int(b))
    return (int(s), int(s))


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("terms", nargs="+", help="keywords; ALL must appear (use --any for OR)")
    ap.add_argument("--venue", default=None, help="filter by venue substring, e.g. 'S&P'")
    ap.add_argument("--year", default=None, help="single year or range, e.g. 2024 or 2024-2026")
    ap.add_argument("--any", action="store_true", help="match ANY term instead of all")
    ap.add_argument("--title-only", action="store_true")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    if not os.path.exists(CORPUS):
        sys.exit(f"corpus not found: {CORPUS}")
    yr = parse_year(args.year)
    terms = [t.lower() for t in args.terms]

    hits = []
    for line in open(CORPUS, encoding="utf-8"):
        r = json.loads(line)
        if args.venue and args.venue.lower() not in r["venue"].lower():
            continue
        if yr and not (yr[0] <= r["year"] <= yr[1]):
            continue
        hay = r["title"].lower() if args.title_only else (r["title"] + " " + (r.get("abstract") or "")).lower()
        ok = any(t in hay for t in terms) if args.any else all(t in hay for t in terms)
        if ok:
            hits.append(r)

    hits.sort(key=lambda r: (-r["year"], r["venue"]))
    for r in hits[:args.limit]:
        link = ("https://doi.org/" + r["doi"]) if r.get("doi") else (r.get("ee") or "(no link)")
        print(f"[{r['venue']} {r['year']}] {r['title']}")
        print(f"    {link}")
    shown = min(len(hits), args.limit)
    print(f"\n{len(hits)} matches" + (f" (showing {shown})" if len(hits) > shown else ""))


if __name__ == "__main__":
    main()
