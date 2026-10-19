# pysearch

A **from-scratch full-text search engine** in Python — inverted index, positional phrase search, boolean queries, and TF-IDF ranking with cosine similarity. Zero search dependencies: no Elasticsearch, Lucene, or Whoosh. Just the standard library, Flask, and pytest.

Author: **Joshua Kofoworola (Deazy01)**

---

## Architecture

```
                         ┌──────────────┐
                         │  Documents   │
                         └──────┬───────┘
                                │  tokenizer.py: lowercase → strip
                                │  punctuation → drop stopwords → stem
                                ▼
┌──────────┐   parse    ┌────────────────┐  evaluate   ┌───────────────┐
│  Query   │ ─────────▶ │ query.py (AST) │ ──────────▶ │  candidates   │
│ "esp32   │            │ AND/OR/NOT,    │  set of     │  {doc_ids}    │
│  NOT lora"│            │ "phrases", ()  │  doc_ids    └───────┬───────┘
└──────────┘            └────────────────┘                      │
                                                               │ rank
                                                               ▼
┌──────────────┐   lookup   ┌──────────────┐   score   ┌──────────────────┐
│ index.py     │ ◀───────── │ ranker.py    │ ───────▶ │ ranked results   │
│ term → {doc: │  postings  │ TF-IDF ×     │  cosine │ [(doc_id, score)] │
│  [positions]}│            │ cosine sim   │         └──────────────────┘
└──────────────┘            └──────────────┘
```

**Module map**

| File | Responsibility |
|---|---|
| `pysearch/tokenizer.py` | Normalization pipeline: lowercase, punctuation split, stopword removal, rule-based stemming |
| `pysearch/index.py` | Inverted index with positional postings, document store, save/load |
| `pysearch/query.py` | Recursive-descent parser → AST → set-based boolean/phrase evaluation |
| `pysearch/ranker.py` | TF-IDF weighting + cosine similarity ranking |
| `pysearch/engine.py` | `SearchEngine` facade: `add_document()` / `search()` / `save()` / `load()` |
| `app.py` + `templates/` | Flask REST API + minimal search UI |
| `data/corpus.py` | 40-document demo corpus (embedded, Python, search, ML, CS) |
| `tests/` | 37 pytest tests covering every module |

---

## Features

- **Full-text indexing** — incremental `add_document()`, JSON persistence
- **Phrase search** — `"deep sleep"` matches only consecutive terms, via positional postings
- **Boolean queries** — `AND`, `OR`, `NOT`, parentheses, implicit `AND` (`python flask`)
- **TF-IDF ranking** — log-scaled TF, smoothed IDF, cosine similarity with length normalization
- **REST API** — `GET /search?q=...&k=10` returns ranked JSON with snippets
- **Web UI** — clean dark-themed search page with scores

---

## Install & Run

```bash
# 1. Create a virtual environment and install the only two dependencies
python3 -m venv .venv
.venv/bin/pip install flask pytest

# 2. Run the test suite (37 tests)
.venv/bin/python -m pytest tests/ -v

# 3. Try the search engine in Python
.venv/bin/python - <<'EOF'
from pysearch import SearchEngine
from data.corpus import load_corpus

engine = SearchEngine()
engine.add_documents(load_corpus())

for doc_id, score in engine.search('"deep sleep"', top_k=3):
    print(f"{doc_id}  {score:.4f}")
EOF

# 4. Launch the web UI  →  http://127.0.0.1:5000
.venv/bin/python app.py
```

### Example queries and expected output

| Query | Top result | Why |
|---|---|---|
| `esp32` | `emb03` (0.297) | Mentions ESP32 most often |
| `"deep sleep"` | `emb09` (0.486) | Only doc with the exact phrase prominent |
| `python AND flask` | `py03` (0.619) | The Flask web-framework article |
| `lora NOT bluetooth` | `emb02` (0.336) | LoRaWAN article, no Bluetooth mention |
| `inverted index` | `se02` (0.480) | The inverted-index explainer |
| `(python OR flask) AND web` | `py03` (0.646) | Boolean grouping works |

---

## How It Works

### 1. The inverted index (`index.py`)

Searching by scanning every document is O(total text) per query — too slow. Instead, at index time we build the reverse mapping:

```
"esp32"  →  { emb01: [0, 31], emb03: [5, 12, 20, 44], emb11: [8] }
```

Each term points to the documents containing it **and the positions** where it occurs. Query lookup is then O(1) per term: jump straight to the postings, no scanning.

Positions exist for **phrase search**: `"deep sleep"` matches a document only if `position(sleep) == position(deep) + 1` somewhere in it.

### 2. Tokenization (`tokenizer.py`)

Documents and queries must go through the *identical* pipeline, or nothing matches:

1. **Lowercase** — `Python` and `python` are the same word.
2. **Split on punctuation** — `state-of-the-art` → four terms.
3. **Drop stopwords** — `the`, `is`, `and` appear everywhere, so they carry ~zero signal and only bloat the index.
4. **Stem** — chop to root form so `running`, `runs` → `run`. Our rule-based stemmer is deliberately simple; the key insight is that it only needs to be *consistent* between index and query time, not linguistically perfect.

### 3. Boolean + phrase retrieval (`query.py`)

The query string is parsed into a tree (AST) by a recursive-descent parser — `OR` binds loosest, then `AND` (explicit or implicit), then `NOT`, then atoms (terms, `"phrases"`, parentheses). Evaluating the tree yields a **set of candidate documents** using set operations: AND = intersection, OR = union, NOT = complement.

### 4. TF-IDF ranking (`ranker.py`)

Boolean retrieval only filters; ranking orders. Each document becomes a vector in "term space":

- **TF** (term frequency): `1 + log(count)` — the first occurrence of a word tells you a lot; the 50th tells you little. The log models that diminishing return.
- **IDF** (inverse document frequency): `log(1 + N / df)` — terms rare across the collection (`metaclass`) outweigh terms everywhere (`python` in a Python corpus).
- **Cosine similarity**: the angle between query and document vectors. Dividing by each vector's length is *length normalization* — without it, long documents would always win just for containing more words.

Final score = cosine between the TF-IDF-weighted query vector and each candidate's **full** TF-IDF document vector. (Using the full document vector for the norm matters: with a single-term query, query-restricted vectors would all score exactly 1.0.)

---

## Tech Stack

- **Python 3** (standard library only for the engine)
- **Flask** — REST API + demo UI
- **pytest** — 37 tests

## Limitations & Next Steps

- Single-machine, in-memory index (JSON persistence, no sharding)
- No BM25 — TF-IDF + cosine is the classic baseline; BM25 would be the natural upgrade
- English-only lite stemmer; Snowball/Porter2 would improve recall
- Ranking ignores link/graph signals (cf. PageRank)

---

*Built from scratch to learn how search really works — every line commented for study.*
