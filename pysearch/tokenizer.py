"""
Tokenizer: turns raw text into a clean stream of search terms.

Why tokenize?
    A search engine can't match "Running" against a query for "run" unless both
    sides go through the SAME normalization pipeline. The tokenizer is that
    pipeline. Every document AND every query passes through it, so "Run!", "running"
    and "RUN" all collapse to the same term: "run".

Pipeline (in order):
    1. Lowercase       - "Python" and "python" are the same word.
    2. Split on non-alphanumerics - punctuation becomes word boundaries,
       so "state-of-the-art" -> ["state", "of", "the", "art"].
    3. Drop stopwords  - ultra-common words ("the", "is", "and") appear in nearly
       every document, so they carry almost no signal and only bloat the index.
    4. Stem            - chop words to their root so morphological variants match:
       "running" -> "run", "batteries" -> "batteri". We use a small rule-based
       stemmer (Porter-lite): fast, no dependencies, good enough for search.
       (True Porter stemming has ~60 rules; ours covers the common suffixes.)

Important design note: the stemmer is deliberately simple. In a production
engine you'd use Porter2/Snowball, but the KEY IDEA is identical - normalize
variants to a shared root so recall goes up.
"""

import re

# A compact stopword list: the most common English function words.
# These are removed because they appear in ~every document and therefore
# contribute almost nothing to distinguishing one document from another
# (their IDF weight would be ~0 anyway - see ranker.py).
STOPWORDS = frozenset("""
    a an and are as at be but by for from has he in is it its of on or that the
    to was were will with we you your this these those they them his her our
    not no so if then than too very can just do does did done have had having
    been being over under between into through during before after above below
    up down out off again once here there when where which who whom whose what
    why how all any both each few more most other some such only own same than
    s t d ll m re ve
""".split())


def _stem(word: str) -> str:
    """Reduce a word to its root form with a small set of ordered suffix rules.

    The golden rule of stemming for search: it does NOT need to be linguistically
    perfect - it needs to be CONSISTENT. Documents and queries go through the
    same function, so "running"/"runs"/"ran" just need to collide. (We don't
    handle irregulars like run/ran - a known, acceptable limitation.)
    """
    if len(word) <= 3:
        return word  # too short to stem safely
    w = word

    # 1. Plurals: "batteries" -> "battery", "boxes" -> "box", "runs" -> "run".
    #    The "ss" guard keeps "class" intact.
    if w.endswith("ies") and len(w) - 3 >= 3:
        w = w[:-3] + "y"
    elif w.endswith("es") and len(w) - 2 >= 3:
        w = w[:-2]
    elif w.endswith("s") and len(w) - 1 >= 3 and not w.endswith("ss"):
        w = w[:-1]

    # 2. Verb endings: "running" -> "runn", "indexed" -> "index".
    stripped_verb = False
    for suffix in ("ing", "ed"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            w = w[: -len(suffix)]
            stripped_verb = True
            break

    # 3. Undouble the consonant left behind: "runn" -> "run".
    #    Only after a verb strip, so "bell" keeps its double-l.
    if stripped_verb and len(w) > 3 and w[-1] == w[-2] and w[-1] not in "aeiou":
        w = w[:-1]

    # 4. Adverb/noun suffixes: "quickly" -> "quick", "organization" -> "organiz".
    for suffix, min_stem in (("ization", 3), ("ation", 3), ("ment", 3),
                             ("ness", 3), ("ly", 3)):
        if w.endswith(suffix) and len(w) - len(suffix) >= min_stem:
            w = w[: -len(suffix)]
            break
    return w


def tokenize(text: str) -> list:
    """Full pipeline: lowercase -> split -> drop stopwords -> stem.

    Returns the list of terms IN ORDER (positions matter for phrase search,
    so we must not use a set here).
    """
    # [a-z0-9]+ keeps letters and digits, drops everything else.
    # Digits are kept because "esp32" and "3.3v" carry real meaning in tech text.
    raw = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in raw if w not in STOPWORDS]


def tokenize_with_positions(text: str) -> list:
    """Same as tokenize(), but returns (term, position) pairs.

    Positions are counted over the FILTERED stream (after stopword removal),
    which is what the index stores. Phrase queries ("exact phrase") work by
    checking that terms appear at CONSECUTIVE positions - see index.py.
    """
    return list(enumerate(tokenize(text)))
