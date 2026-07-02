# 📚 本地文獻檢索入口(Research Index Portal)

> **這是一個「可攜入口檔」。把它複製到任何資料夾打開都可以——所有指令都用絕對路徑指回本地語料庫,不依賴當前目錄。**

## 🎯 一句話
本機已建好一個**資安四大 + 軟工四大(2021–2026)頂會論文**的本地語料庫,含**標題 + 摘要 + DOI**,可離線關鍵字檢索,命中即得 DOI。

- **語料庫位置(預設資料夾):** `D:\skill\research-index\`
- **主資料檔:** `D:\skill\research-index\all_index.jsonl`(一行一篇 JSON)
- **檢索工具:** `D:\skill\research-index\find.py`

---

## ⚡ 立刻使用(在任何資料夾的終端機都能跑)

```bash
python D:\skill\research-index\find.py prompt injection
python D:\skill\research-index\find.py "text-to-image" jailbreak --venue "S&P"
python D:\skill\research-index\find.py llm agent --year 2024-2026 --title-only
python D:\skill\research-index\find.py multimodal --any --limit 60
```

參數:`--venue <子字串>`、`--year 2024` 或 `--year 2024-2026`、`--any`(任一詞即命中,預設是全部詞)、`--title-only`、`--limit N`。
輸出每行:`[venue year] 標題` +(有 DOI 連 doi.org,NDSS/USENIX 連官方頁)。

---

## 📊 語料庫快照(8,926 篇 · 2021–2026)

| 資安(5,257) | 篇 | 軟工(3,669) | 篇 |
|---|---|---|---|
| USENIX Security | 1,782 | ASE | 1,258 |
| ACM CCS | 1,617 | ICSE | 1,030 |
| IEEE S&P | 978 | FSE | 832 |
| NDSS | 880 | ISSTA | 549 |

每筆欄位:`venue, year, title, abstract, doi, authors, dblp_url, ee`。
> 註:多數 2026 場次尚未開/未上架,只有 NDSS 2026 等已收錄。

---

## 🤖 給 AI 助理的指示(當這個檔在別的資料夾被打開時)

如果你(Claude Code / Codex / Cline / Copilot)在其他專案裡讀到這個檔:

1. **本地語料庫在 `D:\skill\research-index\`**;要找文獻時,**優先用 `python D:\skill\research-index\find.py <關鍵字>` 檢索本地**,不要先上網。
2. 需要更細的欄位或自訂查詢,直接讀 `D:\skill\research-index\all_index.jsonl`(JSON Lines)。
3. 已整理好的主題簡報在 `D:\skill\research-index\process\`(例:`mcp-security-briefing.html`)。
4. 使用者預設語言:**繁體中文**。找到論文請附 **venue / 年份 / 標題 / DOI(或 ee 連結)**。
5. 只有本地找不到、或使用者明確要求時,才擴大到網路或重新抓取。

---

## 🗂 檔案地圖(`D:\skill\research-index\`)

| 檔案 | 用途 |
|---|---|
| `all_index.jsonl` | **主語料庫**(8,926 篇,標題+摘要+DOI) |
| `find.py` | **可攜檢索 CLI**(任意目錄可跑,固定指回本地) |
| `taxonomy.json` / `synonyms.json` | 分面標籤的有限詞表 + 合併映射 |
| `process/*.html` | 已整理的主題文獻簡報 |
| `*_20xx.jsonl` | 各 venue-year 原始清單(分檔) |
| `build_venue.py` / `build_all.py` / `fetch_pacmse.py` | 抓取/擴充語料庫的腳本 |
| `search_index.py` / `apply_labels.py` / `prep_chunks.py` | 舊版搜尋 / 標籤套用 / 切塊 |

---

## 🔄 之後要擴充/更新語料庫

```bash
cd /d/skill/research-index
# 抓某個 venue-year(DBLP + OpenAlex 補摘要)
python build_venue.py --toc db/conf/sp/sp2025.bht --tag "IEEE S&P" --year 2025
# 重建合併索引
python - <<'PY'
import glob,json
with open('all_index.jsonl','w',encoding='utf-8') as o:
    for p in sorted(glob.glob('*_20*.jsonl')):
        if p.endswith('.labeled.jsonl'): continue
        for l in open(p,encoding='utf-8'): o.write(l)
PY
```

---
*資料來源:DBLP(清單+DOI)+ OpenAlex(摘要),依 DOI 補齊。此檔為離線檢索的固定入口,複製到任何位置皆可用。*
