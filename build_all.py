#!/usr/bin/env python3
"""Batch-build the CS research index for Security + Software Engineering venues.

For each (venue, year) it tries candidate DBLP TOC keys in order and uses the
first that actually returns papers. A real empty response = SKIP (not held yet);
a network failure after retries = ERROR (safe to re-run — completed files are
resumed, not refetched). Finally merges everything into all_index.jsonl.
"""
import glob
import json
import os
import sys

from build_venue import fetch_dblp_toc, fetch_abstracts

YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

# tag -> function(year) returning ordered candidate DBLP TOC bht keys
VENUES = {
    "IEEE S&P":        lambda y: [f"db/conf/sp/sp{y}.bht"],
    "USENIX Security": lambda y: [f"db/conf/uss/uss{y}.bht"],
    "ACM CCS":         lambda y: [f"db/conf/ccs/ccs{y}.bht"],
    "NDSS":            lambda y: [f"db/conf/ndss/ndss{y}.bht"],
    "ICSE":            lambda y: [f"db/conf/icse/icse{y}.bht"],
    "FSE":             lambda y: [f"db/conf/fse/fse{y}.bht", f"db/conf/sigsoft/fse{y}.bht"],
    "ASE":             lambda y: [f"db/conf/kbse/ase{y}.bht"],
    "ISSTA":           lambda y: [f"db/conf/issta/issta{y}.bht"],
}


def slug(tag, year):
    return f"{tag.replace(' ', '_').replace('&', 'and')}_{year}.jsonl"


def write_jsonl(path, tag, year, papers, abstracts):
    with open(path, "w", encoding="utf-8") as f:
        for p in papers:
            f.write(json.dumps({
                "venue": tag, "year": year, "title": p["title"],
                "abstract": abstracts.get(p["doi"], ""), "doi": p["doi"],
                "authors": p["authors"], "dblp_url": p["dblp_url"], "ee": p["ee"],
            }, ensure_ascii=False) + "\n")


def main():
    summary = []
    for tag, cand in VENUES.items():
        for year in YEARS:
            out = slug(tag, year)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                n = sum(1 for _ in open(out, encoding="utf-8"))
                print(f"RESUME {tag} {year}: {out} exists ({n} papers)", file=sys.stderr)
                summary.append((tag, year, "ok", n))
                continue
            try:
                papers = []
                for toc in cand(year):
                    papers = fetch_dblp_toc(toc)
                    if papers:
                        print(f"\n=== {tag} {year}  ({toc}) ===", file=sys.stderr)
                        break
                if not papers:
                    print(f"SKIP {tag} {year}: not in DBLP yet", file=sys.stderr)
                    summary.append((tag, year, "skip", 0))
                    continue
                abstracts = fetch_abstracts([p["doi"] for p in papers])
                write_jsonl(out, tag, year, papers, abstracts)
                wa = sum(1 for p in papers if abstracts.get(p["doi"]))
                print(f"  -> {out}: {len(papers)} papers, {wa} with abstract", file=sys.stderr)
                summary.append((tag, year, "ok", len(papers)))
            except Exception as e:  # noqa: BLE001
                print(f"ERROR {tag} {year}: {e}", file=sys.stderr)
                summary.append((tag, year, "error", 0))

    # merge all per-venue-year files into one index
    merged, tot = "all_index.jsonl", 0
    with open(merged, "w", encoding="utf-8") as out_f:
        for path in sorted(glob.glob("*.jsonl")):
            if os.path.basename(path) == merged:
                continue
            for line in open(path, encoding="utf-8"):
                out_f.write(line)
                tot += 1

    print("\n\n==== SUMMARY ====")
    for tag, year, st, n in summary:
        print(f"  {tag:16} {year}  {st:6} {n:4}")
    print(f"  merged -> {merged}: {tot} papers")
    errs = [f"{t} {y}" for t, y, st, _ in summary if st == "error"]
    if errs:
        print("  RE-RUN for errors (just run again, completed files resume): " + ", ".join(errs))


if __name__ == "__main__":
    main()
