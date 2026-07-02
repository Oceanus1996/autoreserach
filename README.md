# CS Paper Search — Local Literature Index (Security + Software Engineering)

A reusable **research skill**: an offline, greppable index of top-tier **Security** and
**Software-Engineering** conference/journal papers (2021–2026), storing **title +
abstract + DOI** so any keyword hit maps straight back to a paper. Built around
**search + scale**: search from a keyword, scale by reusing the saved local corpus.

- **Corpus:** `all_index.jsonl` — one JSON paper per line
- **Search CLI:** `find.py` — runs from any directory, always searches the local corpus
- **Build/refresh:** `build_venue.py`, `build_all.py`, `fetch_pacmse.py` (DBLP + OpenAlex)

## Corpus snapshot — 8,926 papers · 2021–2026

| Security (5,257) | # | Software Eng. (3,669) | # |
|---|---|---|---|
| USENIX Security | 1,782 | ASE | 1,258 |
| ACM CCS | 1,617 | ICSE | 1,030 |
| IEEE S&P | 978 | FSE | 832 |
| NDSS | 880 | ISSTA | 549 |

Each record: `venue, year, title, abstract, doi, authors, dblp_url, ee`.
Most 2026 venues are not held/indexed yet (only e.g. NDSS 2026 is in).

## Quickstart

```bash
git clone <this-repo>
cd paper-search-skill

# search (ALL terms must appear; --any for OR)
python find.py prompt injection
python find.py "text-to-image" jailbreak --venue "S&P"
python find.py llm agent --year 2024-2026 --title-only
python find.py multimodal --any --limit 60
```

Flags: `--venue <substr>`, `--year 2024` or `--year 2024-2026`, `--any`, `--title-only`, `--limit N`.
Output per hit: `[venue year] title` + a link (DOI → doi.org; NDSS/USENIX → official page).

`find.py` resolves the corpus path from its own location, so it works from any working directory.

## Refresh / extend the corpus

```bash
# one venue-year (DBLP list + DOIs, then OpenAlex fills abstracts by DOI)
python build_venue.py --toc db/conf/sp/sp2025.bht --tag "IEEE S&P" --year 2025

# FSE 2024+/ISSTA 2025 publish in PACMSE — split by issue
python fetch_pacmse.py --vol pacmse2 --year 2025 --issue ISSTA --tag "ISSTA"

# rebuild the merged index
python - <<'PY'
import glob, json
with open('all_index.jsonl','w',encoding='utf-8') as o:
    for p in sorted(glob.glob('data/venues/*_20*.jsonl')):
        for l in open(p, encoding='utf-8'): o.write(l)
PY
```

## How it's built (why this design)

- **DBLP** is the backbone (authoritative venue/year membership + DOIs, not rate-limited).
- **OpenAlex** is queried **by DOI** (a non-search endpoint) to fill abstracts — avoids the
  rate-limited anonymous search and OpenAlex's messier conference-venue assignment.

## File map

| Path | Purpose |
|---|---|
| `all_index.jsonl` | merged corpus (8,926 papers) |
| `data/venues/*.jsonl` | per venue-year source lists |
| `find.py` | portable search CLI |
| `build_venue.py` / `build_all.py` / `fetch_pacmse.py` | fetch / extend the corpus |
| `taxonomy.json` / `synonyms.json` | controlled-vocabulary faceted tags (domain/type/method/scope/problem) |
| `prep_chunks.py` / `apply_labels.py` | split + apply LLM facet labels |
| `RESEARCH-INDEX.md` | portable local-usage portal (author's machine paths) |

## Data provenance & license

- **Code:** MIT (see `LICENSE`).
- **Metadata** (titles, DOIs, authors, venue/year): from **DBLP** (released under CC0).
- **Abstracts:** from **OpenAlex** (CC0). Reconstructed from OpenAlex's inverted index.

This repository redistributes bibliographic metadata + abstracts for research/search
convenience. All rights to the underlying papers remain with their publishers.
