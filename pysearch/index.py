"""
Inverted index: the core data structure of every search engine.

The problem it solves:
    Given a query like "lora", which documents contain it? Scanning every
    document's full text for every query is O(total text) per query - far too
    slow. Instead we PRECOMPUTE the mapping once, at index time:

        term -> { doc_id -> [positions where the term occurs] }

    This "inverted" mapping (term-first instead of document-first) makes lookup
    O(1) per query term: we jump straight to the documents containing it.

Why store POSITIONS (not just "term appears in doc")?
    Positions enable phrase queries. "wireless sensor" as a phrase should only
    match documents where "wireless" is IMMEDIATELY followed by "sensor" -
    i.e. position(sensor) == position(wireless) + 1. Without positions we'd
    need the raw text at query time.

What else lives here:
    - doc_store: doc_id -> original text (for snippets at display time).
    - doc_lengths: doc_id -> number of indexed terms (needed for length
      normalization in ranking - see ranker.py).
    - doc_count: N, the total number of documents (needed for IDF).
    - save()/load(): persist the whole index so you don't rebuild on restart.
      We use JSON - human-inspectable, which is nice for learning. (Production
      engines use custom binary formats for speed; same idea.)
"""

import json
import os

from .tokenizer import tokenize


class InvertedIndex:
    def __init__(self):
        # postings[term][doc_id] = sorted list of positions
        self.postings = {}
        # doc_id -> original raw text (for result snippets)
        self.doc_store = {}
        # doc_id -> count of indexed (post-stopword) terms in that doc
        self.doc_lengths = {}

    # ------------------------------------------------------------------ build
    def add_document(self, doc_id, text):
        """Tokenize one document and merge its postings into the index.

        Adding is incremental: you can call this any number of times, in any
        order. Re-adding an existing doc_id REPLACES that document (we remove
        the old postings first) so the index never holds stale data.
        """
        if doc_id in self.doc_store:
            self._remove_document(doc_id)

        terms = tokenize(text)
        self.doc_store[doc_id] = text
        self.doc_lengths[doc_id] = len(terms)

        for position, term in enumerate(terms):
            # setdefault chains: get-or-create the nested dicts as we go.
            self.postings.setdefault(term, {}).setdefault(doc_id, []).append(position)

    def _remove_document(self, doc_id):
        """Erase every posting belonging to doc_id (used before re-adding)."""
        for term, docs in self.postings.items():
            docs.pop(doc_id, None)
        # Drop terms that no longer occur in ANY document, keeping the
        # vocabulary clean.
        self.postings = {t: d for t, d in self.postings.items() if d}
        self.doc_store.pop(doc_id, None)
        self.doc_lengths.pop(doc_id, None)

    # ------------------------------------------------------------------ query
    @property
    def doc_count(self):
        """N: total number of indexed documents (needed for IDF)."""
        return len(self.doc_store)

    def doc_freq(self, term):
        """df(term): in how many documents does this term appear?"""
        return len(self.postings.get(term, {}))

    def term_freq(self, term, doc_id):
        """tf(term, doc): how many times does the term occur in this doc?"""
        return len(self.postings.get(term, {}).get(doc_id, []))

    def docs_with(self, term):
        """All doc_ids containing the term (for boolean/term queries)."""
        return set(self.postings.get(term, {}))

    def positions(self, term, doc_id):
        """Positions of term inside doc_id (for phrase queries)."""
        return self.postings.get(term, {}).get(doc_id, [])

    def docs_with_phrase(self, terms):
        """Documents where the terms appear consecutively, in order.

        How it works: take the positions of the FIRST term in each candidate
        doc. For each such position p, check whether term[i] occurs at p + i
        for every i. This is the classic positional phrase-matching algorithm -
        O(occurrences of first term), no text scanning needed.
        """
        if not terms:
            return set()
        first, rest = terms[0], terms[1:]
        result = set()
        for doc_id in self.docs_with(first):
            first_positions = set(self.positions(first, doc_id))
            # Pre-build position sets for the remaining terms in THIS doc.
            rest_sets = [set(self.positions(t, doc_id)) for t in rest]
            for p in first_positions:
                if all((p + i + 1) in rest_sets[i] for i in range(len(rest))):
                    result.add(doc_id)
                    break  # one match is enough to include the doc
        return result

    # ------------------------------------------------------------------ persist
    def save(self, path):
        """Write the index to disk as JSON."""
        data = {
            "postings": self.postings,
            "doc_store": self.doc_store,
            "doc_lengths": self.doc_lengths,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path):
        """Rebuild an InvertedIndex from a file written by save()."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        index = cls()
        index.postings = data["postings"]
        index.doc_store = data["doc_store"]
        index.doc_lengths = data["doc_lengths"]
        return index

    def save_if_needed(self, path):
        """Save only when the file is missing (convenience for the demo app)."""
        if not os.path.exists(path):
            self.save(path)
