#!/usr/bin/env python3
"""Build a searchable {title, abstract, doi} list for one CS venue-year.

Backbone: DBLP (authoritative venue/year membership + DOIs, no rate limit).
Abstracts: OpenAlex, looked up in batches BY DOI (non-search endpoint, not rate-limited).

Each output line is one paper:
    {venue, year, title, abstract, doi, authors, dblp_url, ee}

Usage:
    python build_venue.py --toc db/conf/sp/sp2024.bht --tag "IEEE S&P" --year 2024
"""
import argparse
import html
import json
import sys
import time
import urllib.parse
import urllib.request

MAILTO = "rrm19960902@gmail.com"

# DBLP throttles aggressively (429 / connection reset). Space out its requests.
_last_hit = {}
_MIN_INTERVAL = {"dblp.org": 3.0, "api.openalex.org": 1.0}


def _throttle(url):
    host = urllib.parse.urlparse(url).netloc
    gap = _MIN_INTERVAL.get(host, 0.0)
    if gap:
        elapsed = time.time() - _last_hit.get(host, 0.0)
        if elapsed < gap:
            time.sleep(gap - elapsed)
    _last_hit[host] = time.time()


def http_json(url, tries=8):
    """Return parsed JSON. Raises RuntimeError (not SystemExit) after retries so
    callers can decide whether to skip, retry, or abort the batch."""
    for i in range(tries):
        try:
            _throttle(url)
            req = urllib.request.Request(url, headers={"User-Agent": f"research-index (mailto:{MAILTO})"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            wait = min(3 * (i + 1), 20)
            print(f"  retry {i+1}/{tries} after {wait}s ({e})", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError("request failed after retries: " + url)


def fetch_dblp_toc(toc):
    """Return list of paper dicts from a DBLP venue TOC (bht key)."""
    q = urllib.parse.quote(f"toc:{toc}:")
    papers, first, total = [], 0, None
    while True:
        url = f"https://dblp.org/search/publ/api?q={q}&h=1000&f={first}&format=json"
        d = http_json(url)
        hits = d["result"]["hits"]
        total = int(hits["@total"])
        batch = hits.get("hit", [])
        for x in batch:
            info = x["info"]
            if info.get("type", "").startswith("Editorship"):
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
        print(f"  DBLP: {first}/{total} hits ({len(papers)} papers)", file=sys.stderr)
        if not batch or first >= total:
            break
    return papers


def fetch_abstracts(dois):
    """Map DOI -> abstract via OpenAlex, batched by DOI (50 per request)."""
    out = {}
    dois = [d for d in dois if d]
    for i in range(0, len(dois), 50):
        batch = dois[i:i + 50]
        filt = "doi:" + "|".join(batch)
        url = (f"https://api.openalex.org/works?filter={urllib.parse.quote(filt)}"
               f"&select=doi,abstract_inverted_index&per-page=50&mailto={MAILTO}")
        d = http_json(url)
        for w in d.get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "").lower()
            inv = w.get("abstract_inverted_index")
            if doi and inv:
                pos = sorted((idx, wd) for wd, idxs in inv.items() for idx in idxs)
                out[doi] = " ".join(wd for _, wd in pos)
        print(f"  OpenAlex abstracts: {len(out)} matched ({min(i+50,len(dois))}/{len(dois)} DOIs queried)", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--toc", required=True, help="DBLP TOC bht key, e.g. db/conf/sp/sp2024.bht")
    ap.add_argument("--tag", required=True, help="Venue label, e.g. 'IEEE S&P'")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    print(f"Building {args.tag} {args.year} from {args.toc}", file=sys.stderr)
    papers = fetch_dblp_toc(args.toc)
    abstracts = fetch_abstracts([p["doi"] for p in papers])

    out = args.out or f"{args.tag.replace(' ', '_').replace('&', 'and')}_{args.year}.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for p in papers:
            f.write(json.dumps({
                "venue": args.tag,
                "year": args.year,
                "title": p["title"],
                "abstract": abstracts.get(p["doi"], ""),
                "doi": p["doi"],
                "authors": p["authors"],
                "dblp_url": p["dblp_url"],
                "ee": p["ee"],
            }, ensure_ascii=False) + "\n")

    with_abs = sum(1 for p in papers if abstracts.get(p["doi"]))
    with_doi = sum(1 for p in papers if p["doi"])
    print(f"\nDone: {len(papers)} papers -> {out}", file=sys.stderr)
    print(f"  with DOI:      {with_doi}/{len(papers)}", file=sys.stderr)
    print(f"  with abstract: {with_abs}/{len(papers)}", file=sys.stderr)


if __name__ == "__main__":
    main()
