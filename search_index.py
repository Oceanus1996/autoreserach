#!/usr/bin/env python3
"""Keyword search across all *.jsonl venue lists -> print matching DOIs.

Usage:
    python search_index.py fuzzing
    python search_index.py "large language model" --venue "IEEE S&P"
    python search_index.py llm --title-only
"""
import argparse
import glob
import json
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="+", help="all terms must appear (AND)")
    ap.add_argument("--venue", default=None, help="filter by venue tag substring")
    ap.add_argument("--title-only", action="store_true")
    args = ap.parse_args()

    terms = [t.lower() for t in args.terms]
    here = os.path.dirname(os.path.abspath(__file__))
    n = 0
    for path in sorted(glob.glob(os.path.join(here, "*.jsonl"))):
        for line in open(path, encoding="utf-8"):
            d = json.loads(line)
            if args.venue and args.venue.lower() not in d["venue"].lower():
                continue
            hay = d["title"].lower() if args.title_only else (d["title"] + " " + d["abstract"]).lower()
            if all(t in hay for t in terms):
                n += 1
                print(f"{d['doi'] or '(no doi)'}  [{d['venue']} {d['year']}]  {d['title']}")
    print(f"\n{n} matches")


if __name__ == "__main__":
    main()
