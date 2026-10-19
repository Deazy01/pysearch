"""
pysearch web demo: a tiny Flask app with a search box.

Run:
    .venv/bin/python app.py
Then open http://127.0.0.1:5000 in a browser.

On first run it builds the index from data/corpus.py and caches it to
data/index.json, so restarts are instant. The /search endpoint returns JSON;
the homepage is a minimal UI that calls it.
"""
import os

from flask import Flask, jsonify, render_template, request

from pysearch import SearchEngine
from data.corpus import load_corpus

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "data", "index.json")

app = Flask(__name__)


def get_engine():
    """Load the cached index, or build it from the demo corpus on first run."""
    if os.path.exists(INDEX_PATH):
        return SearchEngine.load(INDEX_PATH)
    engine = SearchEngine()
    engine.add_documents(load_corpus())
    engine.save(INDEX_PATH)
    return engine


engine = get_engine()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():
    """GET /search?q=...&k=10 -> JSON list of {doc_id, score, snippet}."""
    query = request.args.get("q", "").strip()
    try:
        top_k = max(1, min(int(request.args.get("k", 10)), 50))
    except ValueError:
        top_k = 10
    if not query:
        return jsonify({"query": query, "results": []})

    ast = engine.parser.parse(query)
    terms = engine.parser.scoring_terms(ast)
    results = [
        {
            "doc_id": doc_id,
            "score": round(score, 4),
            "snippet": engine.get_snippet(doc_id, terms),
        }
        for doc_id, score in engine.search(query, top_k=top_k)
    ]
    return jsonify({"query": query, "results": results})


@app.route("/stats")
def stats():
    """Corpus statistics, handy for the README demo."""
    return jsonify({
        "documents": engine.index.doc_count,
        "unique_terms": len(engine.index.postings),
    })


if __name__ == "__main__":
    app.run(debug=True)
