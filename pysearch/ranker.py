"""
Ranker: decides WHICH matching documents are the BEST matches, and in what order.

The core intuition (TF-IDF):
    A term is important to a document if it appears OFTEN in that document
    (TF = term frequency) but RARELY across the whole collection
    (IDF = inverse document frequency). "Python" in a Python tutorial: high TF,
    low IDF. "Metaclass" in that tutorial: high TF AND high IDF -> very telling.

Formulas used here (documented so you can defend every choice):

    tf(t, d)  = 1 + log(count(t, d))        -- "log TF": the first occurrence of
                                                a word tells you a lot; the
                                                50th tells you little. The log
                                                models that diminishing return.
                                                (count=1 -> tf=1, count=10 -> ~3.3)

    idf(t)    = log(1 + N / df(t))          -- N = total docs, df = docs
                                                containing t. The +1 inside the
                                                log ("smoothed IDF") avoids
                                                division edge cases and keeps
                                                idf positive. A term in every
                                                doc gets idf = log(2) ~= 0.69
                                                (small but nonzero); a term in
                                                1 of 1000 docs gets ~6.9.

    weight(t, d) = tf(t, d) * idf(t)        -- the classic TF-IDF weight.

    score(q, d)  = cosine(query_vec, doc_vec)
                 = dot(q, d) / (|q| * |d|)  -- cosine similarity treats each
                                                document as a vector in
                                                "term space" and measures the
                                                ANGLE between query and doc.
                                                Dividing by |d| (the document's
                                                Euclidean length) is LENGTH
                                                NORMALIZATION: without it, long
                                                documents would always win just
                                                for containing more words.

Why cosine instead of just summing tf-idf?
    Summing favors long documents (more terms = more chances to match).
    Cosine normalizes by length, so a short, focused document can outrank a
    long, rambling one. This is the standard textbook choice (Manning et al.,
    "Introduction to Information Retrieval", ch. 6).
"""

import math


class TfIdfRanker:
    def __init__(self, index):
        self.index = index
        # Cache idf per term: it never changes unless docs are added.
        self._idf_cache = {}

    # ------------------------------------------------------------------ weights
    def idf(self, term):
        """Inverse document frequency with smoothing; cached per term."""
        if term not in self._idf_cache:
            df = self.index.doc_freq(term)
            n = self.index.doc_count
            # df is at least 1 here (we only call idf for terms in the index),
            # but max() guards the math if that ever changes.
            self._idf_cache[term] = math.log(1 + n / max(df, 1))
        return self._idf_cache[term]

    def doc_vector(self, doc_id):
        """Full TF-IDF weight vector of a document, over ALL its terms.

        We use the complete vector (not just query terms) so that |d| is the
        document's TRUE Euclidean length. This matters: with a single-term
        query, every candidate's query-restricted vector would be 1-dimensional
        and every cosine would be exactly 1.0 - no ranking at all. The full
        vector keeps length normalization honest.

        Cost: O(vocabulary) per document. A production engine precomputes and
        stores each doc's norm at index time; we compute it on the fly because
        clarity beats speed at this scale.
        """
        vec = {}
        for term, docs in self.index.postings.items():
            count = len(docs.get(doc_id, ()))
            if count:
                vec[term] = (1 + math.log(count)) * self.idf(term)
        return vec

    def query_vector(self, terms):
        """TF-IDF weight vector of the query itself.

        Query TF uses the same 1+log(tf) curve (a term repeated in the query
        counts a bit more), and query terms share the DOCUMENT idf - this keeps
        query and document weights on the same scale so cosine is meaningful.
        """
        weights = {}
        for t in terms:
            if t in weights:
                continue  # count each distinct term once, using its frequency
            tf = terms.count(t)
            weights[t] = (1 + math.log(tf)) * self.idf(t)
        return weights

    # ------------------------------------------------------------------ scoring
    @staticmethod
    def cosine(vec_a, vec_b):
        """Cosine similarity between two sparse {term: weight} vectors."""
        dot = sum(w * vec_b.get(t, 0.0) for t, w in vec_a.items())
        norm_a = math.sqrt(sum(w * w for w in vec_a.values()))
        norm_b = math.sqrt(sum(w * w for w in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def score(self, query_terms, doc_id):
        """Cosine similarity between the query and one document.

        The dot product only ranges over query terms (other doc dimensions
        are zero in the query vector), but BOTH norms are over full vectors -
        that is what makes length normalization work.
        """
        qv = self.query_vector(query_terms)
        dv = self.doc_vector(doc_id)
        return self.cosine(qv, dv)

    def rank(self, query_terms, doc_ids):
        """Score every candidate doc, return [(doc_id, score)] sorted best-first."""
        scored = [(d, self.score(query_terms, d)) for d in doc_ids]
        # Sort by score desc; break ties by doc_id for deterministic output.
        scored.sort(key=lambda pair: (pair[1], pair[0]), reverse=True)
        return scored
