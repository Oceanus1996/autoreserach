#!/usr/bin/env python3
"""Fetch a venue-year's papers from OpenAlex into a searchable JSONL list.

Stores {venue, year, title, abstract, doi, authors, oa_id} per line so the
result can be grepped / semantically searched, and every hit maps back to a DOI.

Usage:
    python fetch_openalex.py --venue "IEEE Symposium on Security and Privacy" --year 2024
    python fetch_openalex.py --source-id S1990970 --year 2024 --tag "IEEE S&P"
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

MAILTO = "rrm19960902@gmail.com"
BASE = "https://api.openalex.org"


def get(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"research-index (mailto:{MAILTO})"})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            if isinstance(data, dict) and data.get("error"):
                raise RuntimeError(data.get("message", data["error"]))
            return data
        except Exception as e:  # noqa: BLE001
            wait = 2 * (i + 1)
            print(f"  retry {i+1}/{tries} after {wait}s ({e})", file=sys.stderr)
            time.sleep(wait)
    raise SystemExit("OpenAlex request failed after retries: " + url)


def resolve_source(name):
    q = urllib.parse.quote(name)
    url = f"{BASE}/sources?search={q}&per-page=5&mailto={MAILTO}"
    data = get(url)
    results = data.get("results", [])
    if not results:
        raise SystemExit(f"No source found for: {name}")
    print("Source candidates:", file=sys.stderr)
    for s in results:
        print(f"  {s['id'].split('/')[-1]}  {s['display_name']}  works={s.get('works_count')}", file=sys.stderr)
    return results[0]["id"].split("/")[-1], results[0]["display_name"]


def reconstruct_abstract(inv):
    if not inv:
        return ""
    positions = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)


def fetch_works(source_id, year, tag):
    filt = f"primary_location.source.id:{source_id},publication_year:{year},type:article"
    cursor = "*"
    out = []
    while cursor:
        url = (f"{BASE}/works?filter={filt}&per-page=200&cursor={urllib.parse.quote(cursor)}"
               f"&select=id,title,doi,publication_year,authorships,abstract_inverted_index&mailto={MAILTO}")
        data = get(url)
        for w in data.get("results", []):
            out.append({
                "venue": tag,
                "year": w.get("publication_year"),
                "title": w.get("title"),
                "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "authors": [a["author"]["display_name"] for a in w.get("authorships", [])],
                "oa_id": w["id"].split("/")[-1],
            })
        cursor = data.get("meta", {}).get("next_cursor")
        print(f"  fetched {len(out)} ...", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--venue")
    ap.add_argument("--source-id")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--tag")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if args.source_id:
        sid, name = args.source_id, args.tag or args.source_id
    else:
        sid, name = resolve_source(args.venue)
    tag = args.tag or name
    print(f"Fetching {tag} {args.year} (source {sid})", file=sys.stderr)

    works = fetch_works(sid, args.year, tag)
    out = args.out or f"{tag.replace(' ', '_').replace('&','and')}_{args.year}.jsonl"
    with_abs = sum(1 for w in works if w["abstract"])
    with open(out, "w", encoding="utf-8") as f:
        for w in works:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    print(f"\nDone: {len(works)} papers -> {out}", file=sys.stderr)
    print(f"  with abstract: {with_abs}/{len(works)}", file=sys.stderr)
    print(f"  with DOI:      {sum(1 for w in works if w['doi'])}/{len(works)}", file=sys.stderr)


if __name__ == "__main__":
    main()
