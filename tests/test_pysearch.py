"""
Tests for pysearch. Run with:  .venv/bin/python -m pytest tests/ -v
"""
import os
import tempfile

import pytest

from pysearch import SearchEngine
from pysearch.index import InvertedIndex
from pysearch.query import QueryParser
from pysearch.ranker import TfIdfRanker
from pysearch.tokenizer import tokenize


# ---------------------------------------------------------------- tokenizer
class TestTokenizer:
    def test_lowercases(self):
        assert tokenize("Python PYTHON") == ["python", "python"]

    def test_strips_punctuation(self):
        assert tokenize("hello, world!") == ["hello", "world"]

    def test_removes_stopwords(self):
        assert tokenize("the quick brown fox") == ["quick", "brown", "fox"]

    def test_stems_plurals(self):
        assert tokenize("runs") == tokenize("running") == tokenize("run")

    def test_stems_ing_ed(self):
        assert tokenize("indexed") == ["index"]
        assert tokenize("searching") == ["search"]

    def test_keeps_technical_tokens(self):
        assert "esp32" in tokenize("ESP32 microcontroller")

    def test_empty_string(self):
        assert tokenize("") == []


# ---------------------------------------------------------------- index
@pytest.fixture
def small_index():
    idx = InvertedIndex()
    idx.add_document("d1", "the quick brown fox jumps")
    idx.add_document("d2", "the quick rabbit runs fast")
    idx.add_document("d3", "lazy dogs sleep all day")
    return idx


class TestIndex:
    def test_doc_count(self, small_index):
        assert small_index.doc_count == 3

    def test_term_lookup(self, small_index):
        assert small_index.docs_with("quick") == {"d1", "d2"}
        assert small_index.docs_with("fox") == {"d1"}
        assert small_index.docs_with("nonexistent") == set()

    def test_positions_recorded(self, small_index):
        # "quick" is the first indexed term (position 0) in d1 and d2
        # ("the" is a stopword, so it takes no position).
        assert small_index.positions("quick", "d1") == [0]
        assert small_index.positions("quick", "d2") == [0]

    def test_phrase_match(self, small_index):
        assert small_index.docs_with_phrase(["quick", "brown"]) == {"d1"}

    def test_phrase_no_match_wrong_order(self, small_index):
        assert small_index.docs_with_phrase(["brown", "quick"]) == set()

    def test_phrase_no_match_gap(self, small_index):
        # "quick" and "fox" are not adjacent in d1 ("brown" is between).
        assert small_index.docs_with_phrase(["quick", "fox"]) == set()

    def test_incremental_add(self, small_index):
        small_index.add_document("d4", "quick silver fox")
        assert small_index.doc_count == 4
        assert small_index.docs_with("silver") == {"d4"}

    def test_readd_replaces(self, small_index):
        small_index.add_document("d1", "completely different words here")
        assert small_index.docs_with("fox") == set()
        # Our lite stemmer keeps "different" intact (no -ent rule) -
        # consistency between index and query is what matters.
        assert small_index.docs_with("different") == {"d1"}

    def test_save_load_roundtrip(self, small_index):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "index.json")
            small_index.save(path)
            loaded = InvertedIndex.load(path)
        assert loaded.doc_count == 3
        assert loaded.docs_with("quick") == {"d1", "d2"}
        assert loaded.positions("brown", "d1") == [1]


# ---------------------------------------------------------------- query parser
@pytest.fixture
def parser(small_index):
    return QueryParser(small_index)


class TestQueryParser:
    def test_plain_term(self, parser):
        assert parser.evaluate(parser.parse("quick")) == {"d1", "d2"}

    def test_implicit_and(self, parser):
        assert parser.evaluate(parser.parse("quick fox")) == {"d1"}

    def test_explicit_and(self, parser):
        assert parser.evaluate(parser.parse("quick AND fox")) == {"d1"}

    def test_or(self, parser):
        assert parser.evaluate(parser.parse("fox OR rabbit")) == {"d1", "d2"}

    def test_not(self, parser):
        assert parser.evaluate(parser.parse("quick NOT fox")) == {"d2"}

    def test_phrase(self, parser):
        assert parser.evaluate(parser.parse('"quick brown"')) == {"d1"}

    def test_phrase_no_match(self, parser):
        assert parser.evaluate(parser.parse('"brown quick"')) == set()

    def test_parens(self, parser):
        assert parser.evaluate(parser.parse("(fox OR rabbit) AND quick")) == {"d1", "d2"}

    def test_and_binds_tighter_than_or(self, parser):
        # fox OR (rabbit AND quick): d1 has fox; d2 has rabbit+quick.
        assert parser.evaluate(parser.parse("fox OR rabbit AND quick")) == {"d1", "d2"}

    def test_empty_query(self, parser):
        assert parser.evaluate(parser.parse("")) == set()

    def test_stopwords_ignored(self, parser):
        # "the" is a stopword -> query reduces to "quick".
        assert parser.evaluate(parser.parse("the quick")) == {"d1", "d2"}

    def test_scoring_terms_excludes_negated(self, parser):
        ast = parser.parse("quick NOT fox")
        assert parser.scoring_terms(ast) == ["quick"]


# ---------------------------------------------------------------- ranker
class TestRanker:
    def test_tf_repetition_ranks_higher(self):
        # NOTE (real IR subtlety): pure cosine similarity is scale-invariant -
        # doubling EVERY term count leaves the angle unchanged. Repetition only
        # helps when it shifts the document's term PROPORTIONS toward the query.
        engine = SearchEngine()
        engine.add_document("once", "python tutorial")
        engine.add_document("twice", "python python tutorial")
        results = engine.search("python")
        assert results[0][0] == "twice"
        assert results[1][0] == "once"
        assert results[0][1] > results[1][1]

    def test_rare_term_matters_more(self):
        # "zebra" is rarer than "animal", so its IDF weight is higher:
        # the doc mentioning zebras should top an OR query for both.
        engine = SearchEngine()
        engine.add_document("a", "animal animal animal animal")
        engine.add_document("b", "zebra animal")
        engine.add_document("c", "animal")
        top = engine.search("zebra OR animal")[0][0]
        assert top == "b"

    def test_scores_between_zero_and_one(self):
        engine = SearchEngine()
        engine.add_document("d1", "python programming language")
        for _, score in engine.search("python"):
            assert 0.0 <= score <= 1.0

    def test_no_match_empty(self):
        engine = SearchEngine()
        engine.add_document("d1", "python programming")
        assert engine.search("quantum") == []


# ---------------------------------------------------------------- engine end-to-end
class TestEngine:
    def test_end_to_end_phrase(self):
        engine = SearchEngine()
        engine.add_document("d1", "the esp32 supports bluetooth low energy")
        engine.add_document("d2", "energy efficiency matters for bluetooth devices")
        results = engine.search('"bluetooth low energy"')
        assert [d for d, _ in results] == ["d1"]

    def test_end_to_end_boolean(self):
        engine = SearchEngine()
        engine.add_document("d1", "esp32 microcontroller with wifi")
        engine.add_document("d2", "arduino microcontroller board")
        engine.add_document("d3", "esp32 lora long range radio")
        results = engine.search("esp32 NOT lora")
        assert [d for d, _ in results] == ["d1"]

    def test_top_k_limits_results(self):
        engine = SearchEngine()
        for i in range(20):
            engine.add_document(f"d{i}", f"python document number {i}")
        assert len(engine.search("python", top_k=5)) == 5

    def test_snippet_contains_text(self):
        engine = SearchEngine()
        engine.add_document("d1", "python " * 50 + "end of document here")
        snippet = engine.get_snippet("d1", ["python"])
        assert "python" in snippet.lower()

    def test_save_load_engine(self):
        engine = SearchEngine()
        engine.add_document("d1", "python search engine")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "engine.json")
            engine.save(path)
            loaded = SearchEngine.load(path)
        assert [d for d, _ in loaded.search("python")] == ["d1"]
