"""
Query parser: turns a query string into an AST, then evaluates it against the index.

Supported syntax:
    python lora          implicit AND between terms (like Google)
    python AND lora       explicit AND
    python OR java        either term
    python NOT java       first term, excluding docs with the second
    "exact phrase"       terms must appear consecutively, in order
    (a OR b) AND c        parentheses for grouping

How it works (two phases):
    1. PARSE: a tiny recursive-descent parser builds a tree (AST) from the
       query string. Grammar, in precedence order (loosest first):
           or_expr  := and_expr (OR and_expr)*
           and_expr := not_expr ((AND | implicit) not_expr)*
           not_expr := NOT not_expr | atom
           atom     := "(" or_expr ")" | "phrase" | term
    2. EVALUATE: walk the tree; each node returns a SET of matching doc_ids:
           TERM   -> index.docs_with(term)
           PHRASE -> index.docs_with_phrase(terms)   (positional check)
           AND    -> intersection        OR -> union        NOT -> complement

Ranking note: boolean logic only decides the CANDIDATE set. The final ORDER
always comes from TF-IDF cosine scoring (ranker.py), using every positive
query term (terms under a NOT are excluded from scoring - they only filter).
"""

import re

from .tokenizer import tokenize

# Split a query into: "quoted phrases", parens, operators, bare words.
_TOKEN_RE = re.compile(r'"[^"]*"|\(|\)|\bAND\b|\bOR\b|\bNOT\b|[^\s()"]+')


class QueryParser:
    def __init__(self, index):
        self.index = index

    # ------------------------------------------------------------ tokenize
    def _lex(self, query):
        """Split the raw query into (kind, value) tokens.

        Words AND phrases go through the SAME tokenizer as documents, so
        "Running" in a query becomes "run" exactly like it does in the index.
        Operators are recognized ONLY in uppercase to avoid clashing with
        ordinary words.
        """
        tokens = []
        for raw in _TOKEN_RE.findall(query):
            if raw == "(":
                tokens.append(("LPAREN", raw))
            elif raw == ")":
                tokens.append(("RPAREN", raw))
            elif raw in ("AND", "OR", "NOT"):
                tokens.append(("OP", raw))
            elif raw.startswith('"'):
                terms = tokenize(raw.strip('"'))
                tokens.append(("PHRASE", terms))
            else:
                terms = tokenize(raw)
                # A word that tokenizes to nothing (e.g. a stopword like
                # "the") carries no signal - drop it instead of matching nothing.
                if terms:
                    # tokenize() may split "state-of-the-art" into several
                    # terms; treat them as an implicit AND.
                    for t in terms:
                        tokens.append(("TERM", t))
        return tokens

    # ------------------------------------------------------------ parse
    def parse(self, query):
        """Parse a query string into an AST (nested tuples)."""
        self._tokens = self._lex(query)
        self._pos = 0
        if not self._tokens:
            return ("EMPTY",)
        node = self._parse_or()
        return node

    def _peek(self):
        kind, _ = self._tokens[self._pos] if self._pos < len(self._tokens) else (None, None)
        return kind

    def _next(self):
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _parse_or(self):
        node = self._parse_and()
        while self._peek() == "OP" and self._tokens[self._pos][1] == "OR":
            self._next()
            node = ("OR", node, self._parse_and())
        return node

    def _parse_and(self):
        node = self._parse_not()
        while True:
            kind = self._peek()
            if kind == "OP" and self._tokens[self._pos][1] == "AND":
                self._next()  # consume explicit AND
            elif kind in ("TERM", "PHRASE", "LPAREN") or (
                kind == "OP" and self._tokens[self._pos][1] == "NOT"
            ):
                pass  # implicit AND: two atoms side by side
            else:
                break
            node = ("AND", node, self._parse_not())
        return node

    def _parse_not(self):
        if self._peek() == "OP" and self._tokens[self._pos][1] == "NOT":
            self._next()
            return ("NOT", self._parse_not())
        return self._parse_atom()

    def _parse_atom(self):
        kind, value = self._next()
        if kind == "LPAREN":
            node = self._parse_or()
            # Consume the matching ")"; tolerate a missing one gracefully.
            if self._peek() == "RPAREN":
                self._next()
            return node
        if kind == "PHRASE":
            return ("PHRASE", value)
        return ("TERM", value)  # kind == "TERM"

    # ------------------------------------------------------------ evaluate
    def evaluate(self, node):
        """Evaluate an AST against the index -> set of matching doc_ids."""
        kind = node[0]
        if kind == "EMPTY":
            return set()
        if kind == "TERM":
            return self.index.docs_with(node[1])
        if kind == "PHRASE":
            return self.index.docs_with_phrase(node[1]) if node[1] else set()
        if kind == "AND":
            return self.evaluate(node[1]) & self.evaluate(node[2])
        if kind == "OR":
            return self.evaluate(node[1]) | self.evaluate(node[2])
        if kind == "NOT":
            all_docs = set(self.index.doc_store)
            return all_docs - self.evaluate(node[1])
        raise ValueError(f"unknown AST node: {kind}")

    # ------------------------------------------------------------ scoring terms
    def scoring_terms(self, node):
        """All positive (non-negated) terms in the AST, for the ranker.

        Boolean structure filters CANDIDATES; ranking then scores those
        candidates with plain TF-IDF over the positive terms. Terms under a
        NOT only filter - they must not boost scores.
        """
        kind = node[0]
        if kind == "TERM":
            return [node[1]]
        if kind == "PHRASE":
            return list(node[1])
        if kind in ("AND", "OR"):
            return self.scoring_terms(node[1]) + self.scoring_terms(node[2])
        return []  # NOT and EMPTY contribute nothing to scoring
