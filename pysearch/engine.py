"""
SearchEngine: the public API. Wires tokenizer -> index -> query parser -> ranker
into two methods:

    add_document(doc_id, text)   index one document (incremental)
    search(query, top_k=10)       parse, match, rank -> [(doc_id, score)]

Design note: the engine is deliberately thin. All the real work lives in the
specialized modules (tokenizer/index/query/ranker), so each piece can be
understood - and unit-tested - in isolation. The engine just orchestrates:

    query string --parse--> AST --evaluate--> candidate doc_ids
                                                  |
                        scoring terms --rank--> sorted [(doc_id, score)]
"""

from .index import InvertedIndex
from .query import QueryParser
from .ranker import TfIdfRanker


class SearchEngine:
    def __init__(self, index=None):
        self.index = index or InvertedIndex()
        self.parser = QueryParser(self.index)
        self.ranker = TfIdfRanker(self.index)

    # ------------------------------------------------------------ indexing
    def add_document(self, doc_id, text):
        """Add (or replace) one document in the index.

        The ranker's IDF cache is cleared because document frequencies change
        whenever the collection changes. (A production engine would update IDF
        incrementally; clearing is simpler and correct.)
        """
        self.index.add_document(doc_id, text)
        self.ranker._idf_cache.clear()

    def add_documents(self, docs):
        """Bulk-add an iterable of (doc_id, text) pairs."""
        for doc_id, text in docs:
            self.add_document(doc_id, text)

    # ------------------------------------------------------------ searching
    def search(self, query, top_k=10):
        """Run a query; return [(doc_id, score)] sorted by score, best first.

        Steps:
          1. Parse the query string into an AST.
          2. Evaluate the AST -> the CANDIDATE set (boolean/phrase filtering).
          3. Rank candidates with TF-IDF cosine similarity over the query's
             positive terms; keep the top_k.
        """
        ast = self.parser.parse(query)
        candidates = self.parser.evaluate(ast)
        if not candidates:
            return []
        terms = self.parser.scoring_terms(ast)
        if not terms:  # e.g. a pure NOT query - nothing to score with
            return [(d, 0.0) for d in sorted(candidates)[:top_k]]
        return self.ranker.rank(terms, candidates)[:top_k]

    def get_snippet(self, doc_id, query_terms=None, width=160):
        """A short text excerpt from a document, for display in results.

        If query_terms are given, the snippet is centered on the first match
        (like Google's bolded snippets); otherwise it's the document's start.
        """
        text = self.index.doc_store.get(doc_id, "")
        if not query_terms:
            snippet = text[:width]
        else:
            lowered = text.lower()
            first_hit = min(
                (lowered.find(t) for t in query_terms if t in lowered),
                default=-1,
            )
            if first_hit == -1:
                snippet = text[:width]
            else:
                start = max(0, first_hit - width // 3)
                snippet = text[start:start + width]
                if start > 0:
                    snippet = "..." + snippet
        if len(text) > width and not snippet.endswith("..."):
            snippet += "..."
        return snippet.strip()

    # ------------------------------------------------------------ persistence
    def save(self, path):
        """Persist the index to disk."""
        self.index.save(path)

    @classmethod
    def load(cls, path):
        """Load a previously saved index into a ready-to-search engine."""
        return cls(index=InvertedIndex.load(path))
