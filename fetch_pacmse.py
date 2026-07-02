#!/usr/bin/env python3
"""Fetch a PACMSE (Proc. ACM Softw. Eng.) volume and split by issue (FSE/ISSTA).

Since 2024 FSE and 2025 ISSTA publish in PACMSE, DBLP groups them in one journal
volume; the per-paper `number` field ("FSE" / "ISSTA") separates them.

Usage:
    python fetch_pacmse.py --vol pacmse1 --year 2024 --issue FSE   --tag "FSE"
    python fetch_pacmse.py --vol pacmse2 --year 2025 --issue FSE   --tag "FSE"
    python fetch_pacmse.py --vol pacmse2 --year 2025 --issue ISSTA --tag "ISSTA"
"""
import argparse
import html
import json
import urllib.parse

from build_venue import http_json, fetch_abstracts


def fetch_volume(vol, issue):
    q = urllib.parse.quote(f"toc:db/journals/pacmse/{vol}.bht:")
    papers, first = [], 0
    while True:
        url = f"https://dblp.org/search/publ/api?q={q}&h=1000&f={first}&format=json"
        d = http_json(url)
        hits = d["result"]["hits"]
        total = int(hits["@total"])
        batch = hits.get("hit", [])
        for x in batch:
            info = x["info"]
            if info.get("number") != issue:
                continue
            authors = info.get("authors", {}).get("author", [])
            if isinstance(authors, dict):
                authors = [authors]
            papers.append({
                "title": html.unescape((info.get("title") or "").rstrip(".")),
                "doi": (info.get("doi") or "").lower(),
                "authors": [html.unescape(a["text"]) for a in authors],
                "dblp_url": info.get("url", ""),
                "ee": info.get("ee", ""),
            })
        first += len(batch)
        print(f"  {vol}: scanned {first}/{total}, {len(papers)} in issue {issue}")
        if not batch or first >= total:
            break
    return papers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vol", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--issue", required=True)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()

    papers = fetch_volume(args.vol, args.issue)
    abstracts = fetch_abstracts([p["doi"] for p in papers])
    out = f"{args.tag}_{args.year}.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for p in papers:
            f.write(json.dumps({
                "venue": args.tag, "year": args.year, "title": p["title"],
                "abstract": abstracts.get(p["doi"], ""), "doi": p["doi"],
                "authors": p["authors"], "dblp_url": p["dblp_url"], "ee": p["ee"],
            }, ensure_ascii=False) + "\n")
    wa = sum(1 for p in papers if abstracts.get(p["doi"]))
    print(f"Done: {len(papers)} papers -> {out} ({wa} with abstract)")


if __name__ == "__main__":
    main()
